from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "care-gap-agent"
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # AWS
    AWS_REGION: str = "us-east-1"

    # Amazon Bedrock
    BEDROCK_MODEL_ID: str = "amazon.nova-lite-v1:0"
    SUPPORTED_MODEL_IDS: Annotated[list[str], NoDecode] = ["amazon.nova-lite-v1:0"]

    @field_validator("SUPPORTED_MODEL_IDS", mode="before")
    @classmethod
    def _split_model_ids(cls, v):
        if isinstance(v, str):
            return [m.strip() for m in v.split(",") if m.strip()]
        return v

    # Amazon DynamoDB
    DYNAMODB_TABLE_NAME: str = "caregap-audit"


settings = Settings()