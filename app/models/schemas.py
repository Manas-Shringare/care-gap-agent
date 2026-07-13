"""Pydantic request/response schemas for the /v1/prompts endpoint.

These models define PromptTrace's public API contract. They intentionally
have no knowledge of runtime configuration (e.g. which models are supported)
— that validation belongs in the service layer, not the schema layer.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """A request to invoke a Bedrock model."""

    prompt: str = Field(
        ...,
        min_length=1,
        description="The raw text prompt to send to the model.",
    )
    model_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Bedrock model identifier. Must match one of the models "
            "supported by this deployment (validated at request time)."
        ),
    )


class PromptResponse(BaseModel):
    """The result of a prompt invocation, including observability data."""

    request_id: str = Field(..., description="ULID uniquely identifying this invocation.")
    model_id: str = Field(..., description="The model that served this request.")
    completion: str = Field(..., description="The model's generated response text.")
    inference_latency_ms: float = Field(
        ..., description="Time spent waiting on the Bedrock invoke_model call, in milliseconds."
    )
    total_request_latency_ms: float = Field(
        ...,
        description="End-to-end time from request received to response returned, in milliseconds.",
    )
    timestamp: datetime = Field(..., description="UTC timestamp when the response was generated.")