"""FastAPI application entrypoint for care-gap-agent."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as prompts_router
from app.config import settings
from app.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level=settings.LOG_LEVEL)
    logger.info(
        "Starting care-gap-agent",
        extra={"environment": settings.ENVIRONMENT, "aws_region": settings.AWS_REGION},
    )
    yield
    logger.info("Shutting down care-gap-agent")


app = FastAPI(
    title="care-gap-agent",
    description="Observability toolkit for Amazon Bedrock applications.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(prompts_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness/readiness check. Used by AWS App Runner health checks."""
    return {"status": "ok", "service": settings.APP_NAME}