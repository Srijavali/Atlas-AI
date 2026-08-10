from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GROQ_SPEECH_MODEL: str = "whisper-large-v3-turbo"

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/atlas_ai",
        description="Async PostgreSQL database connection URL",
    )

    TELEGRAM_BOT_TOKEN: str = Field(
        default="",
        description="Telegram bot token from BotFather",
    )

    GEMINI_API_KEYS: str = Field(
        default="",
        description="Comma-separated Gemini API keys",
    )

    GEMINI_MODEL: str = Field(
        default="gemini-3.6-flash",
        description="Primary Gemini model",
    )

    GEMINI_FALLBACK_MODEL: str = Field(
        default="gemini-3.5-flash-lite",
        description="Fallback Gemini model",
    )

    OPENAI_API_KEYS: str = Field(
    default="",
    description="Comma-separated OpenAI API keys used for credential failover",
    )

    OPENAI_MODEL: str = Field(
        default="gpt-5-mini",
        description="Primary OpenAI model for Atlas",
    )

    GROQ_API_KEY: str = Field(
    default="",
    description="Groq API key",
    )

    GROQ_MODEL: str = Field(
        default="openai/gpt-oss-120b",
        description="Groq model used by Atlas",
    )

    SEC_USER_AGENT: str = Field(
        default="",
        description="User-Agent used for SEC EDGAR requests",
    )

    TWELVE_DATA_API_KEY: str = Field(
    default="",
    description="Twelve Data API key",
    )

    ENVIRONMENT: str = Field(
        default="development",
        description="Execution environment (development, staging, production)",
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level",
    )

    WEBHOOK_URL: str = Field(
        default="",
        description="Public URL for Telegram Webhook",
    )

    WEBHOOK_SECRET: str = Field(
        default="",
        description="Secret key to validate Telegram webhook requests",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")


settings = Settings()