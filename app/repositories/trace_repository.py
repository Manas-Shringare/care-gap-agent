"""TraceRepository: persists prompt audit records to DynamoDB.

Each request is stored under partition key `request_id`. The prompt invocation
itself is the item with sort key "REQUEST"; later items (e.g. tool calls) will
share the same partition with their own sort keys.

This is the ONLY module in the application aware of DynamoDB item formats. No
other module should construct or parse DynamoDB items.
"""

import logging
from datetime import datetime

from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.models.schemas import PromptRecord

logger = logging.getLogger(__name__)

REQUEST_SK = "REQUEST"


class TracePersistenceError(Exception):
    """Raised when a DynamoDB read or write of a trace record fails."""

    def __init__(self, error_code: str) -> None:
        super().__init__(error_code)
        self.error_code = error_code


def _wrap(exc: ClientError | BotoCoreError) -> TracePersistenceError:
    """Build a TracePersistenceError carrying only the error code, never the message."""
    if isinstance(exc, ClientError):
        return TracePersistenceError(exc.response["Error"]["Code"])
    return TracePersistenceError(type(exc).__name__)


def _to_item(record: PromptRecord) -> dict:
    return {
        "request_id": {"S": record.request_id},
        "sk": {"S": record.sk},
        "model_id": {"S": record.model_id},
        "prompt": {"S": record.prompt},
        "completion": {"S": record.completion},
        "inference_latency_ms": {"N": str(record.inference_latency_ms)},
        "total_request_latency_ms": {"N": str(record.total_request_latency_ms)},
        "timestamp": {"S": record.timestamp.isoformat()},
    }


def _from_item(item: dict) -> PromptRecord:
    return PromptRecord(
        request_id=item["request_id"]["S"],
        sk=item["sk"]["S"],
        model_id=item["model_id"]["S"],
        prompt=item["prompt"]["S"],
        completion=item["completion"]["S"],
        inference_latency_ms=float(item["inference_latency_ms"]["N"]),
        total_request_latency_ms=float(item["total_request_latency_ms"]["N"]),
        timestamp=datetime.fromisoformat(item["timestamp"]["S"]),
    )


class TraceRepository:
    """Reads and writes trace records in DynamoDB.

    The DynamoDB client is injected rather than constructed internally,
    so tests can supply a stubbed client directly.
    """

    def __init__(self, client, table_name: str = settings.DYNAMODB_TABLE_NAME) -> None:
        self._client = client
        self._table_name = table_name

    def put_record(self, record: PromptRecord) -> None:
        """Write a record, refusing to overwrite an existing one.

        Raises:
            TracePersistenceError: if the write fails, including when an item
                with this request_id already exists.
        """
        try:
            self._client.put_item(
                TableName=self._table_name,
                Item=_to_item(record),
                ConditionExpression="attribute_not_exists(request_id)",
            )
        except (ClientError, BotoCoreError) as exc:
            error = _wrap(exc)
            logger.error(
                "Trace write failed",
                extra={"request_id": record.request_id, "error_code": error.error_code},
            )
            raise error from exc

    def get_record(self, request_id: str) -> PromptRecord | None:
        """Return the request record for request_id, or None if it doesn't exist.

        Raises:
            TracePersistenceError: if the read fails.
        """
        try:
            response = self._client.get_item(
                TableName=self._table_name,
                Key={"request_id": {"S": request_id}, "sk": {"S": REQUEST_SK}},
                ConsistentRead=True,
            )
        except (ClientError, BotoCoreError) as exc:
            error = _wrap(exc)
            logger.error(
                "Trace read failed",
                extra={"request_id": request_id, "error_code": error.error_code},
            )
            raise error from exc

        item = response.get("Item")
        if item is None:
            return None
        return _from_item(item)
