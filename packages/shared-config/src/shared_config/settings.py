from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    service_name: str = Field(default="service")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    job_service_url: str = Field(default="http://job-service:8001", alias="JOB_SERVICE_URL")
    scraper_service_url: str = Field(default="http://scraper-service:8002", alias="SCRAPER_SERVICE_URL")
    orchestrator_service_url: str = Field(default="http://orchestrator-service:8003", alias="ORCHESTRATOR_SERVICE_URL")
    ai_service_url: str = Field(default="http://ai-service:8005", alias="AI_SERVICE_URL")
    apply_service_url: str = Field(default="http://apply-service:8006", alias="APPLY_SERVICE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5", alias="OPENAI_MODEL")
    document_storage_path: str = Field(default="/data/documents", alias="DOCUMENT_STORAGE_PATH")
    worker_concurrency: int = Field(default=4, alias="WORKER_CONCURRENCY")
    dice_email: str | None = Field(default=None, alias="DICE_EMAIL")
    dice_password: str | None = Field(default=None, alias="DICE_PASSWORD")
    dice_login_url: str = Field(default="https://www.dice.com/dashboard/login", alias="DICE_LOGIN_URL")
    browser_headless: bool = Field(default=True, alias="BROWSER_HEADLESS")
    apply_browser_timeout_ms: int = Field(default=60000, alias="APPLY_BROWSER_TIMEOUT_MS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                return value
            return [item.strip() for item in raw.split(",") if item.strip()]
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings(service_name: str) -> ServiceSettings:
    return ServiceSettings(service_name=service_name)
