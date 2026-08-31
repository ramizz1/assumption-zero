"""
Tests for clean validation error handling in FastAPI backend.
"""

from fastapi.testclient import TestClient

from assumption_zero.config import Settings, is_public_http_url
from assumption_zero.main import app, clean_error_message

client = TestClient(
    app,
    headers={"X-Analysis-Owner": "test_owner_token_0123456789_ABCDEFGH"},
)


def test_clean_error_message_helper():
    raw_pydantic_err = (
        "1 validation error for IdeaInput name Value error, Invalid startup prompt 'the': "
        "The input text appears to be random characters or gibberish. Please enter a clear product or business idea. "
        "[type=value_error, input_value='the', input_type=str] "
        "For further information visit https://errors.pydantic.dev/2.13/v/value_error"
    )
    cleaned = clean_error_message(raw_pydantic_err)
    assert "Invalid startup prompt 'the'" in cleaned
    assert "pydantic.dev" not in cleaned
    assert "[type=" not in cleaned
    assert "1 validation error" not in cleaned


def test_gibberish_prompt_endpoint_returns_clean_error():
    response = client.post("/api/analyses/from-prompt", json={"prompt": "the"})
    assert response.status_code == 422 or response.status_code == 400
    data = response.json()
    detail = data.get("detail", "")
    assert "gibberish" in detail.lower()
    assert "pydantic.dev" not in detail
    assert "[type=" not in detail
    assert "1 validation error" not in detail


def test_empty_prompt_returns_clean_error():
    response = client.post("/api/analyses/from-prompt", json={"prompt": "  "})
    assert response.status_code == 422 or response.status_code == 400
    data = response.json()
    detail = data.get("detail", "")
    assert isinstance(detail, str)
    assert len(detail) > 0
    assert "pydantic.dev" not in detail


def test_verify_keys_endpoint_success():
    response = client.post("/api/verify-keys", json={"ai_provider": "mock"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provider"] == "mock"
    assert "no external AI provider" in data["message"]


def test_verify_keys_missing_key_returns_400():
    response = client.post(
        "/api/verify-keys",
        json={"ai_provider": "openai_compat", "openai_api_key": ""},
    )
    assert response.status_code == 400
    data = response.json()
    assert "API key is missing" in data["detail"]


def test_provider_probe_rejects_bad_key_without_echoing_it(monkeypatch):
    from assumption_zero.llm.groq_adapter import GroqAdapter

    async def reject_key(_self):
        raise RuntimeError("AI provider rejected the API key (HTTP 401).")

    monkeypatch.setattr(GroqAdapter, "verify_connection", reject_key)
    sentinel = "TEST_KEY_MUST_NOT_BE_ECHOED"
    response = client.post(
        "/api/verify-keys",
        json={"ai_provider": "groq", "groq_api_key": sentinel},
    )

    assert response.status_code == 400
    assert "rejected" in response.json()["detail"].casefold()
    assert sentinel not in response.text


def test_ollama_configured_default_url_is_not_rejected_as_runtime_override(monkeypatch):
    from assumption_zero.llm.ollama_adapter import OllamaAdapter

    async def verify_local_model(_self):
        return "installed-local-model"

    monkeypatch.setattr(OllamaAdapter, "verify_connection", verify_local_model)
    response = client.post(
        "/api/verify-keys",
        json={
            "ai_provider": "ollama",
            "ollama_base_url": "http://localhost:11434",
        },
    )

    assert response.status_code == 200
    assert "installed-local-model" in response.json()["message"]


def test_release_debug_value_does_not_break_startup():
    settings = Settings(_env_file=None, debug="release")
    assert settings.debug is False


def test_ssrf_url_filter_blocks_local_and_non_http_targets():
    assert is_public_http_url("http://127.0.0.1:11434") is False
    assert is_public_http_url("http://169.254.169.254/latest/meta-data") is False
    assert is_public_http_url("file:///etc/passwd") is False
    assert is_public_http_url("https://8.8.8.8") is True
