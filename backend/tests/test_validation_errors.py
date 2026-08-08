"""
Tests for clean validation error handling in FastAPI backend.
"""
from fastapi.testclient import TestClient
from assumption_zero.main import app, clean_error_message

client = TestClient(app)


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
    response = client.post("/api/verify-keys", json={"provider": "mock"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provider"] == "mock"
    assert "Successfully" in data["message"]


def test_verify_keys_missing_key_returns_400():
    response = client.post("/api/verify-keys", json={"provider": "openai_compat", "openaiKey": ""})
    assert response.status_code == 400
    data = response.json()
    assert "API key is missing" in data["detail"]
