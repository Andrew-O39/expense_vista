from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # ------------------------
    # Database
    # ------------------------
    database_url: str = Field(..., alias="DATABASE_URL")

    # ------------------------
    # Frontend
    # ------------------------
    frontend_url: str = Field(..., alias="FRONTEND_URL")

    # ------------------------
    # Authentication / Security
    # ------------------------
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    password_reset_expire_minutes: int = Field(default=30, alias="PASSWORD_RESET_EXPIRE_MINUTES")

    # ------------------------
    # Email / SES
    # ------------------------
    aws_region: str = Field(..., alias="AWS_REGION")
    aws_access_key_id: str = Field(..., alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., alias="AWS_SECRET_ACCESS_KEY")
    ses_sender: str = Field(..., alias="EMAIL_FROM")  # e.g. no-reply@domain.com

    # ------------------------
    # AI / OpenAI integration
    # ------------------------
    ai_category_suggestion_enabled: bool = Field(default=False, alias="AI_CATEGORY_SUGGESTION_ENABLED")
    ai_assistant_enabled: bool = Field(default=False, alias="AI_ASSISTANT_ENABLED")
    ai_provider: str = Field(default="none", alias="AI_PROVIDER")  # "openai" | "bedrock" | "none"

    # Provider-specific keys
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    bedrock_region: str | None = Field(None, alias="BEDROCK_REGION")
    bedrock_model_id: str | None = Field(None, alias="BEDROCK_MODEL_ID")  # e.g. "anthropic.claude-3-haiku-20240307-v1:0"

    # Assistant model selection (you can override if needed)
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_ASSISTANT_MODEL")

    # ------------------------
    # Pydantic SettingsConfig
    # ------------------------
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="allow"  # Allows extra variables in .env without throwing errors
    )


# Create a global settings instance
settings = Settings()