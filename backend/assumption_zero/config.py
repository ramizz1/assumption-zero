"""Application configuration loaded from environment variables."""
from __future__ import annotations

import ipaddress
import socket
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"
LOCAL_ENV = Path(".env")


def is_public_http_url(value: str) -> bool:
    """Return whether a URL resolves only to public HTTP(S) addresses."""
    try:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username or parsed.password:
            return False

        hostname = parsed.hostname.rstrip(".").lower()
        if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
            return False

        try:
            addresses = [ipaddress.ip_address(hostname)]
        except ValueError:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
            }
        return bool(addresses) and all(address.is_global for address in addresses)
    except (OSError, ValueError):
        return False

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), str(LOCAL_ENV)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────
    app_name: str = "Assumption Zero"
    app_version: str = "0.1.0"
    debug: bool = False
    ssrf_protection_enabled: bool = False

    # ── AI Providers ──────────────────────────────────────────────
    # Selects which adapter to use as the primary provider.
    # "auto" = first configured provider, then the deterministic evidence baseline
    ai_provider: str = "auto"

    # ── Assumption Zero Beta / OpenRouter ────────────────────────
    # OpenRouter routes to 200+ open models via a single API.
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "google/gemma-4-26b-a4b-it:free"

    # ── Groq (Ultra-fast Llama 3.3 models) ──────────────────────
    # https://console.groq.com/keys
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    # ── OpenCode AI ──────────────────────────────────────────────
    opencode_api_key: Optional[str] = None
    opencode_base_url: str = "https://opencode.ai/api/v1"
    opencode_model: str = "opencode/claude-3.5-sonnet"

    # ── Ollama (local models) ────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # ── Custom / OpenAI-Compatible Provider ──────────────────────
    # Use this to plug in ChatGPT, Claude (via compatible proxy), Together AI,
    # Anyscale, LM Studio, vLLM self-hosted, or any OpenAI-spec API.
    # Set AI_PROVIDER=openai_compat to activate.
    openai_compatible_base_url: Optional[str] = None   # e.g. https://api.openai.com/v1
    openai_compatible_api_key: Optional[str] = None    # your API key
    openai_compatible_model: str = "gpt-4o-mini"       # model name to pass in the request

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

    @field_validator("debug", "ssrf_protection_enabled", mode="before")
    @classmethod
    def parse_environment_mode_as_bool(cls, value: object) -> object:
        """Accept common deployment-mode values without crashing at import time.

        Some hosts expose ``DEBUG=release`` or ``DEBUG=production`` instead of a
        conventional boolean. Treat production-like modes as false and
        development-like modes as true while leaving normal booleans to
        Pydantic.
        """
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "off", "disabled"}:
                return False
            if normalized in {"development", "develop", "dev", "debug", "on", "enabled"}:
                return True
        return value

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        allowed = {"mock", "beta", "openrouter", "ollama", "groq", "hybrid", "auto", "dual", "openai_compat", "openai", "opencode"}
        if v not in allowed:
            raise ValueError(f"ai_provider must be one of {allowed}, got: {v!r}")
        return v

    def masked(self) -> dict:
        """Return a copy with secrets replaced — safe for logging."""
        d = self.model_dump()
        for secret_key in ("openrouter_api_key", "github_token", "groq_api_key", "openai_compatible_api_key", "opencode_api_key"):
            if d.get(secret_key):
                d[secret_key] = "***"
        return d


@lru_cache
def get_settings() -> Settings:
    return Settings()
