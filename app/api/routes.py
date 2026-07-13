"""API routes for the /v1/prompts resource."""

import logging
import time

import boto3
from fastapi import APIRouter, HTTPException, Response
from ulid import ULID

from app.config import settings
from app.models.schemas import PromptRequest, PromptResponse
from app.services.bedrock import (
    BedrockInvocationError,
    BedrockService,
    UnsupportedModelError,
)
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/prompts", tags=["prompts"])

# Constructed once at module load, reused across requests.
_bedrock_client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
_bedrock_service = BedrockService(client=_bedrock_client)


@router.post("", response_model=PromptResponse)
def create_prompt(request: PromptRequest, response: Response) -> PromptResponse:
    request_id = str(ULID())
    response.headers["X-Request-ID"] = request_id

    start = time.perf_counter()
    try:
        result = _bedrock_service.invoke(prompt=request.prompt, model_id=request.model_id)
    except UnsupportedModelError as exc:
        logger.warning(
            "Rejected unsupported model_id",
            extra={"request_id": request_id, "model_id": request.model_id},
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except BedrockInvocationError as exc:
        logger.error(
            "Bedrock invocation failed",
            extra={"request_id": request_id, "model_id": request.model_id},
        )
        raise HTTPException(status_code=502, detail="Upstream model invocation failed") from exc
    total_request_latency_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "Prompt invocation succeeded",
        extra={
            "request_id": request_id,
            "model_id": request.model_id,
            "inference_latency_ms": result.inference_latency_ms,
            "total_request_latency_ms": total_request_latency_ms,
        },
    )

    return PromptResponse(
        request_id=request_id,
        model_id=request.model_id,
        completion=result.completion,
        inference_latency_ms=result.inference_latency_ms,
        total_request_latency_ms=total_request_latency_ms,
        timestamp=utc_now(),
    )