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

    # ------------------------
    # Email / SES
    # ------------------------
    aws_region: str = Field(..., alias="AWS_REGION")
    aws_access_key_id: str = Field(..., alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., alias="AWS_SECRET_ACCESS_KEY")
    ses_sender: str = Field(..., alias="EMAIL_FROM")  # e.g. no-reply@domain.com

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