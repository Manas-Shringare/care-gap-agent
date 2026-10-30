"""Structured JSON logging configuration for care-gap-agent.

Every log record is rendered as a single-line JSON object so that logs are
directly queryable in CloudWatch Logs Insights (or any log aggregator) by
field, rather than requiring text parsing.
"""

import json
import logging
import sys
from datetime import UTC, datetime

# Attributes that exist on every stdlib LogRecord. Anything NOT in this set
# was passed in via `extra={...}` by the caller and should be surfaced in
# the JSON output (e.g. request_id, latency_ms).
_STANDARD_RECORD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


class JSONFormatter(logging.Formatter):
    """Renders each LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Surface any caller-supplied `extra` fields (e.g. request_id).
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger to emit structured JSON to stdout.

    Should be called once, at application startup.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Avoid duplicate handlers if this is ever called more than once
    # (e.g. in tests that import main multiple times).
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)