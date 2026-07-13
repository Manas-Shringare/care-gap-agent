"""Unit tests for BedrockService.

These tests use a mocked Bedrock Runtime client — no real AWS calls are made,
no AWS credentials are required to run this file.
"""

from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from app.config import settings
from app.services.bedrock import (
    BedrockInvocationError,
    BedrockResult,
    BedrockService,
    UnsupportedModelError,
)

SUPPORTED_MODEL_ID = settings.SUPPORTED_MODEL_IDS[0]


def _converse_response(text: str) -> dict:
    """Build a minimal, valid Bedrock Converse API response shape."""
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
    }


def test_invoke_returns_parsed_completion():
    mock_client = Mock()
    mock_client.converse.return_value = _converse_response("Hello there!")

    service = BedrockService(client=mock_client)
    result = service.invoke(prompt="Say hello.", model_id=SUPPORTED_MODEL_ID)

    assert isinstance(result, BedrockResult)
    assert result.completion == "Hello there!"
    assert result.inference_latency_ms >= 0
    mock_client.converse.assert_called_once_with(
        modelId=SUPPORTED_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": "Say hello."}]}],
        inferenceConfig={"maxTokens": 512},
    )


def test_invoke_rejects_unsupported_model_id():
    mock_client = Mock()

    service = BedrockService(client=mock_client)

    with pytest.raises(UnsupportedModelError):
        service.invoke(prompt="Say hello.", model_id="not-a-real-model")

    mock_client.converse.assert_not_called()


def test_invoke_wraps_client_errors():
    mock_client = Mock()
    mock_client.converse.side_effect = ClientError(
        error_response={"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
        operation_name="Converse",
    )

    service = BedrockService(client=mock_client)

    with pytest.raises(BedrockInvocationError):
        service.invoke(prompt="Say hello.", model_id=SUPPORTED_MODEL_ID)