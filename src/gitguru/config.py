from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from gitguru.db.url import to_asyncpg_url


class Settings(BaseSettings):
    app_env: str
    database_url: str
    log_level: str = "INFO"
    app_name: str = "GitGuru"
    # The commit this image was built from. CI sets it (Dockerfile ARG GIT_SHA); locally "dev".
    git_sha: str = "dev"

    # LLM gateway (Day 8). Keys default to empty so tests and CI never need them.
    gemini_api_key: str = ""
    groq_api_key: str = ""
    llm_primary_model: str = "gemini-3.5-flash"
    llm_fallback_model: str = "openai/gpt-oss-20b"

    # Both providers speak the OpenAI API, so any compatible server works (Ollama, a test fake).
    llm_primary_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta/openai"
    )
    llm_fallback_base_url: str = "https://api.groq.com/openai/v1"

    llm_timeout_seconds: float = 30.0
    usd_inr: float = 95.0  # rupees per US dollar, for cost estimates
    prompts_dir: Path = Path("prompts")

    # Queue and worker (Day 10). One Redis; the worker is a second process running the same code.
    redis_url: str = "redis://localhost:6379"
    manifest_file: Path = Path("data/manifest.jsonl")
    admin_token: str = ""  # whoever sends this in X-Admin-Token may start an ingestion
    worker_in_api: bool = (
        False  # True where no separate worker service exists (free hosting)
    )
    ingest_concurrency: int = 2  # documents a worker handles at the same time
    ingest_rpm: float = 12.0  # model calls per minute, shared by those documents
    ingest_job_timeout: int = 60  # seconds; a longer job is stopped and tried again
    ingest_max_tries: int = 3

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        return to_asyncpg_url(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
