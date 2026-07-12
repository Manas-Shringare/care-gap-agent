"""Application configuration, loaded from environment variables.

Reads from a local `.env` file (see `.env.example` for the template) or from
real environment variables when running in a container (e.g. AWS App Runner).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings.

    Field names match the variable names in `.env.example` exactly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "prompttrace"
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # AWS
    AWS_REGION: str = "us-east-1"

    # Amazon Bedrock
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # Amazon DynamoDB
    DYNAMODB_TABLE_NAME: str = "prompttrace-requests"


settings = Settings()