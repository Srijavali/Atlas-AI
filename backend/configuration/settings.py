from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/atlas_ai",
        description="Async PostgreSQL database connection URL"
    )
    TELEGRAM_BOT_TOKEN: str = Field(
        default="",
        description="Telegram bot token from BotFather"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Execution environment (development, staging, production)"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    WEBHOOK_URL: str = Field(
        default="",
        description="Public URL for Telegram Webhook"
    )
    WEBHOOK_SECRET: str = Field(
        default="",
        description="Secret key to validate Telegram webhook requests"
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")

settings = Settings()
