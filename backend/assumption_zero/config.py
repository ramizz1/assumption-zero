"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────
    app_name: str = "Assumption Zero"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── Database ──────────────────────────────────────────────────
    database_url: str = "sqlite:///./assumption_zero.db"

    # ── AI Providers ──────────────────────────────────────────────
    # Selects which adapter to use as the primary provider.
    # "beta" = Assumption Zero Beta AI (built-in, no key needed)
    ai_provider: str = "beta"

    # ── Assumption Zero Beta / OpenRouter ────────────────────────
    # OpenRouter routes to 200+ open models via a single API.
    # The built-in key works out of the box; set your own for higher limits.
    # https://openrouter.ai
    openrouter_api_key: Optional[str] = None   # leave blank to use built-in key
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # ── Ollama (local models) ────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # ── Research Providers ────────────────────────────────────────
    searxng_base_url: Optional[str] = None
    github_token: Optional[str] = None

    # ── Rate limiting & timeouts ──────────────────────────────────
    rate_limit_per_minute: int = 10
    request_timeout: int = 30

    # ── CORS ──────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Limits ────────────────────────────────────────────────────
    max_idea_length: int = 5000
    max_evidence_items: int = 50
    max_search_results_per_query: int = 10

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        allowed = {"mock", "beta", "openrouter", "ollama"}
        if v not in allowed:
            raise ValueError(f"ai_provider must be one of {allowed}, got: {v!r}")
        return v

    def masked(self) -> dict:
        """Return a copy with secrets replaced — safe for logging."""
        d = self.model_dump()
        for secret_key in ("openrouter_api_key", "github_token"):
            if d.get(secret_key):
                d[secret_key] = "***"
        return d


@lru_cache
def get_settings() -> Settings:
    return Settings()
