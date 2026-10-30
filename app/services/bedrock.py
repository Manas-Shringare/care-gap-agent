"""BedrockService: wraps Amazon Bedrock's Converse API.

Responsible for translating care-gap-agent's simple public request shape into
the Bedrock Converse API payload, invoking the model, capturing inference
latency, and parsing the response back into plain text.

This is the ONLY module in the application aware of Bedrock's request or
response formats. No other module should construct or parse Bedrock payloads.
"""

import logging
import time
from dataclasses import dataclass

from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 512


class UnsupportedModelError(Exception):
    """Raised when a requested model_id is not in the supported set."""


class BedrockInvocationError(Exception):
    """Raised when the underlying Bedrock Converse call fails."""


@dataclass(frozen=True)
class BedrockResult:
    completion: str
    inference_latency_ms: float


class BedrockService:
    """Invokes Bedrock models via the Converse API.

    The Bedrock Runtime client is injected rather than constructed
    internally, so tests can supply a stub or mock client directly.
    """

    def __init__(self, client) -> None:
        self._client = client

    def validate_model_id(self, model_id: str) -> None:
        """Raise UnsupportedModelError if model_id isn't in the configured set."""
        if model_id not in settings.SUPPORTED_MODEL_IDS:
            raise UnsupportedModelError(
                f"Model '{model_id}' is not supported. "
                f"Supported models: {settings.SUPPORTED_MODEL_IDS}"
            )

    def invoke(self, prompt: str, model_id: str) -> BedrockResult:
        """Invoke a Bedrock model via Converse and return its completion
        plus inference latency.

        Raises:
            UnsupportedModelError: if model_id is not configured as supported.
            BedrockInvocationError: if the underlying Bedrock call fails.
        """
        self.validate_model_id(model_id)

        messages = [{"role": "user", "content": [{"text": prompt}]}]
        inference_config = {"maxTokens": DEFAULT_MAX_TOKENS}

        start = time.perf_counter()
        try:
            response = self._client.converse(
                modelId=model_id,
                messages=messages,
                inferenceConfig=inference_config,
            )
        except ClientError as exc:
            logger.error("Bedrock invocation failed", extra={"model_id": model_id})
            raise BedrockInvocationError(str(exc)) from exc
        inference_latency_ms = (time.perf_counter() - start) * 1000

        completion = response["output"]["message"]["content"][0]["text"]

        return BedrockResult(completion=completion, inference_latency_ms=inference_latency_ms)