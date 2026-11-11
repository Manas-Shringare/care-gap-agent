"""Unit tests for AthenaExecutor.

These tests use a real boto3 Athena client wrapped in botocore's Stubber (or a
Mock for errors raised before a request is sent). Sleep and clock are faked, so
nothing waits. No real AWS calls are made, no AWS credentials are required.
"""

import logging
from unittest.mock import Mock

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.stub import Stubber

from app.logging import JSONFormatter
from app.services.athena import (
    AthenaClientError,
    AthenaExecutor,
    AthenaQueryCancelledError,
    AthenaQueryFailedError,
    AthenaTimeoutError,
)

QID = "11111111-2222-3333-4444-555555555555"
SQL = "SELECT 1"
FAKE_ARN = "arn:aws:iam::123456789012:user/prompttrace-local-dev"
CONTEXT = {"Catalog": "AwsDataCatalog", "Database": "caregap_silver"}
POLL_PARAMS = {"QueryExecutionId": QID}


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _start_params(params=None) -> dict:
    expected = {"QueryString": SQL, "WorkGroup": "caregap", "QueryExecutionContext": CONTEXT}
    if params:
        expected["ExecutionParameters"] = params
    return expected


def _results_params(next_token=None) -> dict:
    expected = {"QueryExecutionId": QID, "MaxResults": 1000}
    if next_token:
        expected["NextToken"] = next_token
    return expected


def _exec_response(state, *, athena_error=None, reason=None) -> dict:
    status = {"State": state}
    if reason:
        status["StateChangeReason"] = reason
    if athena_error:
        status["AthenaError"] = athena_error
    return {
        "QueryExecution": {
            "QueryExecutionId": QID,
            "Status": status,
            "Statistics": {"DataScannedInBytes": 2048, "TotalExecutionTimeInMillis": 731},
        }
    }


def _row(*values) -> dict:
    return {"Data": [{} if v is None else {"VarCharValue": v} for v in values]}


def _results_page(columns, rows, *, header=True, next_token=None) -> dict:
    page_rows = ([_row(*columns)] if header else []) + [_row(*r) for r in rows]
    response = {
        "ResultSet": {
            "Rows": page_rows,
            "ResultSetMetadata": {"ColumnInfo": [{"Name": c, "Type": "varchar"} for c in columns]},
        }
    }
    if next_token:
        response["NextToken"] = next_token
    return response


def _logged(caplog) -> str:
    """Every captured record rendered as the app's JSON log lines, extras included."""
    formatter = JSONFormatter()
    return "\n".join(formatter.format(record) for record in caplog.records)


@pytest.fixture
def fake():
    return FakeClock()


@pytest.fixture
def stubbed():
    client = boto3.client("athena", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield client, stubber
        stubber.assert_no_pending_responses()


def _executor(client, fake, **kwargs) -> AthenaExecutor:
    return AthenaExecutor(client, sleep=fake.sleep, clock=fake.clock, **kwargs)


def test_happy_path_polls_until_succeeded(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("QUEUED"), POLL_PARAMS)
    stubber.add_response("get_query_execution", _exec_response("RUNNING"), POLL_PARAMS)
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    stubber.add_response(
        "get_query_results",
        _results_page(["gap_patients", "never_tested"], [["24", "0"]]),
        _results_params(),
    )

    result = _executor(client, fake).run_query(SQL)

    assert result.query_execution_id == QID
    assert result.columns == ["gap_patients", "never_tested"]
    assert result.rows == [["24", "0"]]
    assert result.truncated is False
    assert result.data_scanned_bytes == 2048
    assert result.total_ms == 731
    assert fake.sleeps == [0.25, 0.5]


def test_paginates_with_next_token(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    stubber.add_response(
        "get_query_results",
        _results_page(["id"], [["a"], ["b"]], next_token="page-2"),
        _results_params(),
    )
    stubber.add_response(
        "get_query_results",
        _results_page(["id"], [["c"]], header=False),
        _results_params("page-2"),
    )

    result = _executor(client, fake).run_query(SQL)

    assert result.columns == ["id"]
    assert result.rows == [["a"], ["b"], ["c"]]
    assert result.truncated is False


def test_row_cap_truncates_and_stops_fetching(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    # Only one page is queued: fetching a second one would fail the Stubber.
    stubber.add_response(
        "get_query_results",
        _results_page(["id"], [["a"], ["b"], ["c"], ["d"], ["e"]], next_token="page-2"),
        _results_params(),
    )

    result = _executor(client, fake, max_rows=3).run_query(SQL)

    assert result.rows == [["a"], ["b"], ["c"]]
    assert result.truncated is True


def test_failed_query_raises_without_reason(stubbed, fake, caplog):
    caplog.set_level(logging.INFO)
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response(
        "get_query_execution",
        _exec_response(
            "FAILED",
            athena_error={"ErrorCategory": 2, "ErrorType": 1301},
            reason=f"User: {FAKE_ARN} is not authorized to perform: glue:GetTable",
        ),
        POLL_PARAMS,
    )

    with pytest.raises(AthenaQueryFailedError) as exc_info:
        _executor(client, fake).run_query(SQL)

    exc = exc_info.value
    assert exc.code == "QUERY_FAILED"
    assert exc.query_execution_id == QID
    assert exc.error_category == 2
    assert exc.error_type == 1301
    assert FAKE_ARN not in str(exc)
    assert FAKE_ARN not in repr(exc)
    assert all(FAKE_ARN not in str(arg) for arg in exc.args)
    assert FAKE_ARN not in _logged(caplog)


def test_cancelled_query_raises(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("CANCELLED"), POLL_PARAMS)

    with pytest.raises(AthenaQueryCancelledError) as exc_info:
        _executor(client, fake).run_query(SQL)

    assert exc_info.value.code == "QUERY_CANCELLED"
    assert exc_info.value.query_execution_id == QID


@pytest.mark.parametrize("stop_fails", [False, True])
def test_timeout_stops_query_then_raises(stubbed, fake, stop_fails):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    for _ in range(7):
        stubber.add_response("get_query_execution", _exec_response("RUNNING"), POLL_PARAMS)
    if stop_fails:
        stubber.add_client_error(
            "stop_query_execution",
            service_error_code="InvalidRequestException",
            service_message=FAKE_ARN,
            expected_params=POLL_PARAMS,
        )
    else:
        stubber.add_response("stop_query_execution", {}, POLL_PARAMS)

    with pytest.raises(AthenaTimeoutError) as exc_info:
        _executor(client, fake, timeout_s=6).run_query(SQL)

    assert exc_info.value.code == "QUERY_TIMEOUT"
    assert exc_info.value.query_execution_id == QID
    # Doubles to the 2 s cap, then the last sleep is clipped to the time remaining.
    assert fake.sleeps == [0.25, 0.5, 1, 2, 2, 0.25]
    assert sum(fake.sleeps) == 6


def test_access_denied_on_start_raises_client_error(stubbed, fake, caplog):
    caplog.set_level(logging.INFO)
    client, stubber = stubbed
    # Nothing else is queued: any polling call would fail the Stubber.
    stubber.add_client_error(
        "start_query_execution",
        service_error_code="AccessDeniedException",
        service_message=f"User: {FAKE_ARN} is not authorized to perform: athena:*",
    )

    with pytest.raises(AthenaClientError) as exc_info:
        _executor(client, fake).run_query(SQL)

    exc = exc_info.value
    assert exc.code == "AccessDeniedException"
    assert exc.query_execution_id is None
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert FAKE_ARN not in str(exc)
    assert FAKE_ARN not in repr(exc)
    assert FAKE_ARN not in _logged(caplog)


@pytest.mark.parametrize("params", [["'female'"], None, []])
def test_start_request_shape(stubbed, fake, params):
    client, stubber = stubbed
    # expected_params is an exact match, so this also proves ResultConfiguration is absent.
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params(params))
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    stubber.add_response("get_query_results", _results_page(["n"], []), _results_params())

    result = _executor(client, fake).run_query(SQL, params)

    assert result.rows == []


def test_null_cell_becomes_none(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    stubber.add_response(
        "get_query_results",
        _results_page(["id", "deathdate"], [["p1", None]]),
        _results_params(),
    )

    result = _executor(client, fake).run_query(SQL)

    assert result.rows == [["p1", None]]


def test_botocore_error_during_polling_raises_client_error(fake):
    # Stubber can only queue service responses, so a connection-level error needs a Mock.
    mock_client = Mock()
    mock_client.start_query_execution.return_value = {"QueryExecutionId": QID}
    mock_client.get_query_execution.side_effect = EndpointConnectionError(
        endpoint_url="https://athena.us-east-1.amazonaws.com"
    )

    with pytest.raises(AthenaClientError) as exc_info:
        _executor(mock_client, fake).run_query(SQL)

    assert exc_info.value.code == "EndpointConnectionError"
    assert exc_info.value.query_execution_id == QID
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


def test_exactly_max_rows_is_not_truncated(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    stubber.add_response(
        "get_query_results",
        _results_page(["id"], [["a"], ["b"], ["c"]]),
        _results_params(),
    )

    result = _executor(client, fake, max_rows=3).run_query(SQL)

    assert result.rows == [["a"], ["b"], ["c"]]
    assert result.truncated is False


def test_cap_on_page_boundary_with_next_token_is_truncated(stubbed, fake):
    client, stubber = stubbed
    stubber.add_response("start_query_execution", {"QueryExecutionId": QID}, _start_params())
    stubber.add_response("get_query_execution", _exec_response("SUCCEEDED"), POLL_PARAMS)
    # Only one page is queued: fetching a second one would fail the Stubber.
    stubber.add_response(
        "get_query_results",
        _results_page(["id"], [["a"], ["b"], ["c"]], next_token="page-2"),
        _results_params(),
    )

    result = _executor(client, fake, max_rows=3).run_query(SQL)

    assert result.rows == [["a"], ["b"], ["c"]]
    assert result.truncated is True


@pytest.mark.parametrize("kwargs", [{"max_rows": 0}, {"timeout_s": 0}, {"timeout_s": -1}])
def test_constructor_rejects_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        AthenaExecutor(Mock(), **kwargs)
