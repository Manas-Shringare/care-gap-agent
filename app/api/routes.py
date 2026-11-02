"""API routes for the /v1/prompts resource."""

import logging
import time

import boto3
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from ulid import ULID

from app.config import settings
from app.models.schemas import PromptRecord, PromptRequest, PromptResponse
from app.repositories.trace_repository import TracePersistenceError, TraceRepository
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
_dynamodb_client = boto3.client("dynamodb", region_name=settings.AWS_REGION)
_trace_repository = TraceRepository(client=_dynamodb_client)


def _error_response(status_code: int, error: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


@router.post(
    "",
    response_model=PromptResponse,
    responses={500: {"description": "The trace could not be persisted."}},
)
def create_prompt(request: PromptRequest, response: Response) -> PromptResponse | JSONResponse:
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
    # Measured before persistence so the stored record and the response agree.
    total_request_latency_ms = (time.perf_counter() - start) * 1000

    record = PromptRecord(
        request_id=request_id,
        model_id=request.model_id,
        prompt=request.prompt,
        completion=result.completion,
        inference_latency_ms=result.inference_latency_ms,
        total_request_latency_ms=total_request_latency_ms,
        timestamp=utc_now(),
    )

    # A successful response is a persisted response: never return an unrecorded completion.
    try:
        _trace_repository.put_record(record)
    except TracePersistenceError as exc:
        logger.error(
            "Trace persistence failed",
            extra={
                "request_id": request_id,
                "model_id": request.model_id,
                "error_code": exc.error_code,
            },
        )
        return _error_response(500, "trace_persistence_failed", request_id)

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
        request_id=record.request_id,
        model_id=record.model_id,
        completion=record.completion,
        inference_latency_ms=record.inference_latency_ms,
        total_request_latency_ms=record.total_request_latency_ms,
        timestamp=record.timestamp,
    )


@router.get(
    "/{request_id}",
    response_model=PromptRecord,
    responses={
        404: {"description": "No trace exists for this request_id."},
        500: {"description": "The trace could not be read."},
    },
)
def get_prompt(request_id: str) -> PromptRecord | JSONResponse:
    try:
        record = _trace_repository.get_record(request_id)
    except TracePersistenceError as exc:
        logger.error(
            "Trace lookup failed",
            extra={"request_id": request_id, "error_code": exc.error_code},
        )
        return _error_response(500, "trace_read_failed", request_id)

    if record is None:
        logger.info("Trace not found", extra={"request_id": request_id})
        return _error_response(404, "trace_not_found", request_id)

    return record
