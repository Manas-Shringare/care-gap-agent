"""Unit tests for TraceRepository.

These tests use a real boto3 DynamoDB client wrapped in botocore's Stubber (or a
Mock for errors raised before a request is sent). No real AWS calls are made,
no AWS credentials are required to run this file.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.stub import Stubber

from app.models.schemas import PromptRecord
from app.repositories.trace_repository import TracePersistenceError, TraceRepository

TABLE_NAME = "caregap-audit-test"
REQUEST_ID = "01JBXYZ0000000000000000000"


def _record() -> PromptRecord:
    return PromptRecord(
        request_id=REQUEST_ID,
        model_id="amazon.nova-lite-v1:0",
        prompt="Say hello.",
        completion="Hello there!",
        inference_latency_ms=123.45,
        total_request_latency_ms=130.5,
        timestamp=datetime(2026, 11, 1, 12, 30, 0, tzinfo=UTC),
    )


def _item() -> dict:
    return {
        "request_id": {"S": REQUEST_ID},
        "sk": {"S": "REQUEST"},
        "model_id": {"S": "amazon.nova-lite-v1:0"},
        "prompt": {"S": "Say hello."},
        "completion": {"S": "Hello there!"},
        "inference_latency_ms": {"N": "123.45"},
        "total_request_latency_ms": {"N": "130.5"},
        "timestamp": {"S": "2026-11-01T12:30:00+00:00"},
    }


@pytest.fixture
def stubbed():
    client = boto3.client("dynamodb", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield TraceRepository(client=client, table_name=TABLE_NAME), stubber
        stubber.assert_no_pending_responses()


def test_put_record_writes_item_with_condition(stubbed):
    repo, stubber = stubbed
    stubber.add_response(
        "put_item",
        {},
        expected_params={
            "TableName": TABLE_NAME,
            "Item": _item(),
            "ConditionExpression": "attribute_not_exists(request_id)",
        },
    )

    repo.put_record(_record())


def test_put_record_conditional_failure_raises(stubbed):
    repo, stubber = stubbed
    stubber.add_client_error("put_item", service_error_code="ConditionalCheckFailedException")

    with pytest.raises(TracePersistenceError) as exc_info:
        repo.put_record(_record())

    assert exc_info.value.error_code == "ConditionalCheckFailedException"


def test_put_record_botocore_error_raises():
    # Stubber can only queue service responses, so a connection-level error needs a Mock.
    mock_client = Mock()
    original = EndpointConnectionError(endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    mock_client.put_item.side_effect = original

    repo = TraceRepository(client=mock_client, table_name=TABLE_NAME)

    with pytest.raises(TracePersistenceError) as exc_info:
        repo.put_record(_record())

    assert exc_info.value.error_code == "EndpointConnectionError"
    assert exc_info.value.__cause__ is original


def test_get_record_found(stubbed):
    repo, stubber = stubbed
    stubber.add_response(
        "get_item",
        {"Item": _item()},
        expected_params={
            "TableName": TABLE_NAME,
            "Key": {"request_id": {"S": REQUEST_ID}, "sk": {"S": "REQUEST"}},
            "ConsistentRead": True,
        },
    )

    assert repo.get_record(REQUEST_ID) == _record()


def test_get_record_missing_returns_none(stubbed):
    repo, stubber = stubbed
    stubber.add_response("get_item", {})

    assert repo.get_record(REQUEST_ID) is None
