"""AthenaExecutor: runs one read-only query in Amazon Athena and returns its rows.

Responsible for starting the query in the fixed workgroup and database, polling
until it finishes (with a timeout), and paging through the results up to a row
cap.

This is the ONLY module in the application aware of Athena's request or
response formats. No other module should construct or parse Athena payloads.

AWS error messages and StateChangeReason contain the account ID and user ARN, so
they never appear in exceptions or logs. Errors carry a code and the query
execution ID; an admin looks the query up by ID.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

WORKGROUP = "caregap"
QUERY_EXECUTION_CONTEXT = {"Catalog": "AwsDataCatalog", "Database": "caregap_silver"}
PAGE_SIZE = 1000
INITIAL_POLL_INTERVAL_S = 0.25
MAX_POLL_INTERVAL_S = 2.0

_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELLED"}


class AthenaExecutorError(Exception):
    """Base class for every error raised by AthenaExecutor."""

    def __init__(self, code: str, query_execution_id: str | None = None) -> None:
        super().__init__(code, query_execution_id)
        self.code = code
        self.query_execution_id = query_execution_id


class AthenaQueryFailedError(AthenaExecutorError):
    """Raised when the query ends in state FAILED."""

    def __init__(
        self, query_execution_id: str, error_category: int | None, error_type: int | None
    ) -> None:
        super().__init__("QUERY_FAILED", query_execution_id)
        self.error_category = error_category
        self.error_type = error_type


class AthenaQueryCancelledError(AthenaExecutorError):
    """Raised when the query ends in state CANCELLED."""

    def __init__(self, query_execution_id: str) -> None:
        super().__init__("QUERY_CANCELLED", query_execution_id)


class AthenaTimeoutError(AthenaExecutorError):
    """Raised when the query is still running after timeout_s."""

    def __init__(self, query_execution_id: str) -> None:
        super().__init__("QUERY_TIMEOUT", query_execution_id)


class AthenaClientError(AthenaExecutorError):
    """Raised when an Athena API call fails (ClientError or BotoCoreError)."""


@dataclass(frozen=True)
class QueryResult:
    query_execution_id: str
    columns: list[str]
    rows: list[list[str | None]]
    truncated: bool
    data_scanned_bytes: int
    total_ms: int


def _error_code(exc: ClientError | BotoCoreError) -> str:
    """Return the AWS error code (or exception class name), never the message."""
    if isinstance(exc, ClientError):
        return exc.response["Error"]["Code"]
    return type(exc).__name__


class AthenaExecutor:
    """Runs one read-only query in the fixed Athena workgroup.

    The Athena client is injected rather than constructed internally, so tests
    can supply a stubbed client directly. `sleep` and `clock` are injected so
    tests can poll without real waiting.
    """

    def __init__(
        self,
        client,
        *,
        timeout_s: float = 30.0,
        max_rows: int = 1000,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_rows < 1:
            raise ValueError("max_rows must be at least 1")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self._client = client
        self._timeout_s = timeout_s
        self._max_rows = max_rows
        self._sleep = sleep
        self._clock = clock

    def run_query(self, sql: str, params: list[str] | None = None) -> QueryResult:
        """Run one query and return up to max_rows rows.

        params: Athena parses each parameter as a SQL expression, not inert data. 
        Build them in code from validated typed values (ints, enums, allowlisted codes); 
        never pass user or model text.

        `params` are already SQL literals and are passed unchanged as
        ExecutionParameters (omitted when None or empty).

        `truncated` is True when rows were left out. If the cap is reached exactly
        at the end of a page and Athena returns a NextToken, the next page is not
        fetched, so `truncated` is True even if that page would have been empty.

        Raises:
            AthenaQueryFailedError: if the query ends FAILED.
            AthenaQueryCancelledError: if the query ends CANCELLED.
            AthenaTimeoutError: if polling exceeds timeout_s (the query is stopped).
            AthenaClientError: if an Athena API call fails.
        """
        query_execution_id = None
        try:
            query_execution_id = self._start(sql, params)
            execution = self._wait_for_terminal_state(query_execution_id)

            status = execution["Status"]
            state = status["State"]
            statistics = execution.get("Statistics", {})
            total_ms = statistics.get("TotalExecutionTimeInMillis", 0)
            data_scanned_bytes = statistics.get("DataScannedInBytes", 0)

            if state == "FAILED":
                athena_error = status.get("AthenaError", {})
                error = AthenaQueryFailedError(
                    query_execution_id,
                    athena_error.get("ErrorCategory"),
                    athena_error.get("ErrorType"),
                )
                self._log_summary(
                    query_execution_id,
                    state,
                    total_ms=total_ms,
                    data_scanned_bytes=data_scanned_bytes,
                    error_category=error.error_category,
                    error_type=error.error_type,
                )
                raise error
            if state == "CANCELLED":
                self._log_summary(
                    query_execution_id,
                    state,
                    total_ms=total_ms,
                    data_scanned_bytes=data_scanned_bytes,
                )
                raise AthenaQueryCancelledError(query_execution_id)

            columns, rows, truncated = self._fetch_rows(query_execution_id)
            self._log_summary(
                query_execution_id,
                state,
                total_ms=total_ms,
                data_scanned_bytes=data_scanned_bytes,
                row_count=len(rows),
                truncated=truncated,
            )
            return QueryResult(
                query_execution_id=query_execution_id,
                columns=columns,
                rows=rows,
                truncated=truncated,
                data_scanned_bytes=data_scanned_bytes,
                total_ms=total_ms,
            )
        except (ClientError, BotoCoreError) as exc:
            error = AthenaClientError(_error_code(exc), query_execution_id)

        # Raised outside the except block so neither __cause__ nor __context__
        # holds the AWS exception, whose message contains the account ID and ARN.
        logger.error(
            "Athena call failed",
            extra={"query_execution_id": query_execution_id, "error_code": error.code},
        )
        raise error from None

    def _start(self, sql: str, params: list[str] | None) -> str:
        kwargs = {
            "QueryString": sql,
            "WorkGroup": WORKGROUP,
            "QueryExecutionContext": QUERY_EXECUTION_CONTEXT,
        }
        if params:
            kwargs["ExecutionParameters"] = params
        response = self._client.start_query_execution(**kwargs)
        return response["QueryExecutionId"]

    def _wait_for_terminal_state(self, query_execution_id: str) -> dict:
        """Poll until the query reaches a terminal state and return its QueryExecution."""
        deadline = self._clock() + self._timeout_s
        interval = INITIAL_POLL_INTERVAL_S
        while True:
            response = self._client.get_query_execution(QueryExecutionId=query_execution_id)
            execution = response["QueryExecution"]
            if execution["Status"]["State"] in _TERMINAL_STATES:
                return execution

            now = self._clock()
            if now >= deadline:
                self._stop_quietly(query_execution_id)
                self._log_summary(query_execution_id, "TIMEOUT")
                raise AthenaTimeoutError(query_execution_id)

            self._sleep(min(interval, deadline - now))
            interval = min(interval * 2, MAX_POLL_INTERVAL_S)

    def _stop_quietly(self, query_execution_id: str) -> None:
        """Ask Athena to stop the query; a failure here is logged, not raised."""
        try:
            self._client.stop_query_execution(QueryExecutionId=query_execution_id)
        except (ClientError, BotoCoreError) as exc:
            logger.warning(
                "Athena stop failed",
                extra={"query_execution_id": query_execution_id, "error_code": _error_code(exc)},
            )

    def _fetch_rows(
        self, query_execution_id: str
    ) -> tuple[list[str], list[list[str | None]], bool]:
        """Page through results; return (columns, rows, truncated)."""
        columns: list[str] = []
        rows: list[list[str | None]] = []
        next_token = None
        first_page = True
        while True:
            kwargs = {"QueryExecutionId": query_execution_id, "MaxResults": PAGE_SIZE}
            if next_token:
                kwargs["NextToken"] = next_token
            page = self._client.get_query_results(**kwargs)

            result_set = page["ResultSet"]
            page_rows = result_set.get("Rows", [])
            if first_page:
                columns = [c["Name"] for c in result_set["ResultSetMetadata"]["ColumnInfo"]]
                page_rows = page_rows[1:]  # the first row of the first page is the header
                first_page = False

            for row in page_rows:
                if len(rows) == self._max_rows:
                    return columns, rows, True
                # A cell without VarCharValue is SQL NULL.
                rows.append([cell.get("VarCharValue") for cell in row["Data"]])

            next_token = page.get("NextToken")
            if not next_token:
                return columns, rows, False
            if len(rows) == self._max_rows:
                return columns, rows, True

    def _log_summary(
        self,
        query_execution_id: str,
        state: str,
        *,
        total_ms: int = 0,
        data_scanned_bytes: int = 0,
        row_count: int = 0,
        truncated: bool = False,
        **extra,
    ) -> None:
        logger.info(
            "Athena query finished",
            extra={
                "query_execution_id": query_execution_id,
                "state": state,
                "total_ms": total_ms,
                "data_scanned_bytes": data_scanned_bytes,
                "row_count": row_count,
                "truncated": truncated,
                **extra,
            },
        )
