"""
FastAPI endpoint tests.
"""

from __future__ import annotations

import secrets
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from assumption_zero.api.routes import _parse_prompt_with_fallback
from assumption_zero.llm.mock_adapter import MockAdapter
from assumption_zero.main import app
from assumption_zero.schemas import PromptAnalysisRequest


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.headers.update({"X-Analysis-Owner": secrets.token_urlsafe(32)})
        yield c


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "ai_provider" in data
    assert "research_providers" in data


def test_health_no_secrets_exposed(client):
    resp = client.get("/api/health")
    text = resp.text
    # Secrets must never appear in API responses
    assert "GEMINI_API_KEY" not in text
    assert "openai_compatible_api_key" not in text
    assert "github_token" not in text


def test_create_analysis_returns_id(client):
    body = {
        "ai_provider": "groq",
        "groq_api_key": "test-groq-key",
        "idea": {
            "name": "TestProduct",
            "description": "Test description",
            "problem": "Test problem that is long enough",
            "target_customer": "Test customers",
            "geography": "US",
        }
    }
    # Patch run_analysis to avoid actually running the engine in tests
    with patch("assumption_zero.api.routes.run_analysis", new_callable=AsyncMock):
        resp = client.post("/api/analyses", json=body)
    assert resp.status_code == 202
    data = resp.json()
    assert "analysis_id" in data
    assert data["status"] == "pending"


def test_sync_analysis_requires_real_ai(client):
    resp = client.post(
        "/api/analyses/sync",
        json={
            "ai_provider": "mock",
            "idea": {
                "name": "TestProduct",
                "description": "Test description",
                "problem": "Test problem that is long enough",
                "target_customer": "Test customers",
                "geography": "US",
            },
        },
    )
    assert resp.status_code == 400
    assert "require a configured AI provider" in resp.json()["detail"]


def test_prompt_analysis_can_explicitly_run_without_ai(client):
    with patch("assumption_zero.api.routes.run_analysis", new_callable=AsyncMock) as run:
        resp = client.post(
            "/api/analyses/from-prompt",
            json={
                "ai_provider": "auto",
                "run_without_ai": True,
                "prompt": (
                    "ClinicFlow helps small dental clinics in Azerbaijan replace manual "
                    "appointment reminders with automated SMS scheduling."
                ),
            },
        )

    assert resp.status_code == 202
    assert resp.json()["parsed_idea"]["target_customer"]
    run.assert_awaited_once()
    assert run.await_args.kwargs["ai_provider_override"] == "mock"


def test_structured_analysis_can_explicitly_run_without_ai(client):
    with patch("assumption_zero.api.routes.run_analysis", new_callable=AsyncMock) as run:
        resp = client.post(
            "/api/analyses",
            json={
                "ai_provider": "auto",
                "run_without_ai": True,
                "idea": {
                    "name": "ClinicFlow",
                    "description": "Automated appointment reminders for dental clinics",
                    "problem": "Small clinics lose revenue when patients miss appointments",
                    "target_customer": "Small dental clinics",
                    "geography": "Azerbaijan",
                },
            },
        )

    assert resp.status_code == 202
    run.assert_awaited_once()
    assert run.await_args.kwargs["ai_provider_override"] == "mock"


def test_prompt_mock_provider_requires_explicit_without_ai_opt_in(client):
    resp = client.post(
        "/api/analyses/from-prompt",
        json={
            "ai_provider": "mock",
            "prompt": (
                "ClinicFlow helps small dental clinics in Azerbaijan replace manual "
                "appointment reminders with automated SMS scheduling."
            ),
        },
    )

    assert resp.status_code == 400
    assert "explicitly confirmed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_malformed_ai_prompt_structure_uses_deterministic_parser():
    provider = AsyncMock()
    provider.parse_raw_prompt.side_effect = ValueError("provider returned invalid JSON")
    body = PromptAnalysisRequest(
        ai_provider="groq",
        groq_api_key="test-groq-key",
        prompt=(
            "ClinicFlow helps small dental clinics in Azerbaijan replace manual "
            "appointment reminders with automated SMS scheduling."
        ),
    )

    with patch(
        "assumption_zero.api.routes.build_llm_adapter",
        side_effect=[provider, MockAdapter()],
    ):
        parsed = await _parse_prompt_with_fallback(body, "groq")

    assert parsed.name.startswith("ClinicFlow")
    assert parsed.geography == "Azerbaijan"


def test_get_nonexistent_analysis(client):
    resp = client.get("/api/analyses/nonexistent-id-12345")
    assert resp.status_code == 404


def test_list_analyses_returns_list(client):
    resp = client.get("/api/analyses")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_demo_endpoint_is_precomputed_and_token_free(client):
    with patch("assumption_zero.api.routes.run_analysis", new_callable=AsyncMock) as run:
        resp = client.post("/api/demo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis_id"] == "demo-legalmind-local"
    assert data["status"] == "complete"
    assert data.get("demo") is True
    assert data.get("bundled") is True
    run.assert_not_awaited()


def test_demo_never_uses_browser_groq_key(client):
    with patch("assumption_zero.api.routes.run_analysis", new_callable=AsyncMock) as run:
        resp = client.post(
            "/api/demo",
            json={
                "ai_provider": "auto",
                "groq_api_key": "browser-groq-key",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["bundled"] is True
    run.assert_not_awaited()


def test_create_analysis_invalid_input(client):
    # Missing required fields
    body = {
        "idea": {
            "name": "Bad",
            # missing problem, target_customer, geography
        }
    }
    resp = client.post("/api/analyses", json=body)
    assert resp.status_code == 422


def test_input_too_long_rejected(client):
    body = {
        "idea": {
            "name": "A" * 201,  # Exceeds 200 char limit
            "description": "desc",
            "problem": "problem here for testing",
            "target_customer": "test customer",
            "geography": "US",
        }
    }
    resp = client.post("/api/analyses", json=body)
    assert resp.status_code == 422


def test_prompt_length_and_provider_are_bounded(client):
    too_long = client.post("/api/analyses/from-prompt", json={"prompt": "idea " * 1200})
    assert too_long.status_code == 422

    invalid_provider = client.post(
        "/api/analyses",
        json={
            "ai_provider": "unknown-provider",
            "idea": {
                "name": "BoundedProduct",
                "description": "A concrete product description",
                "problem": "A concrete customer problem that needs solving",
                "target_customer": "Small teams",
                "geography": "US",
            },
        },
    )
    assert invalid_provider.status_code == 422


def test_analysis_list_limit_is_bounded(client):
    assert client.get("/api/analyses?limit=0").status_code == 422
    assert client.get("/api/analyses?limit=101").status_code == 422
@pytest.mark.asyncio
async def test_user_bulleted_prompt_parsing():
    body = PromptAnalysisRequest(
        prompt=(
            "• What it is: A personalized AI study companion for university students.\n"
            "• The Problem It Solves: Students struggle to retain lectures and cram inefficiently before exams.\n"
            "• How It Works: Students upload lecture slides or audio; the AI generates customized flashcards, quizzes, and spaced-repetition schedules."
        ),
        run_without_ai=True,
    )
    parsed = await _parse_prompt_with_fallback(body, "mock")
    assert parsed.name
    assert "study" in parsed.name.lower() or "companion" in parsed.name.lower()
    assert "students" in parsed.target_customer.lower()
    assert "cram" in parsed.problem.lower()
    assert parsed.solution and "flashcards" in parsed.solution.lower()


@pytest.mark.asyncio
async def test_ai_provider_runtime_error_uses_deterministic_parser():
    provider = AsyncMock()
    provider.parse_raw_prompt.side_effect = RuntimeError("AI provider rate limited 429")
    body = PromptAnalysisRequest(
        ai_provider="groq",
        groq_api_key="test-groq-key",
        prompt="MedSchedule replaces paper appointment books for rural clinics in Texas.",
    )
    with patch(
        "assumption_zero.api.routes.build_llm_adapter",
        side_effect=[provider, MockAdapter()],
    ):
        parsed = await _parse_prompt_with_fallback(body, "groq")

    assert parsed.name.startswith("MedSchedule")
    assert "clinics" in parsed.target_customer.lower()


def test_gibberish_prompt_rejection_message(client):
    resp = client.post(
        "/api/analyses/from-prompt",
        json={"prompt": "asdfghjkl zxcvbnm", "run_without_ai": True},
    )
    assert resp.status_code in (400, 422)
    assert "gibberish" in resp.json()["detail"].lower()
def test_auto_mode_without_keys_runs_seamlessly(client):
    with patch("assumption_zero.api.routes.run_analysis", new_callable=AsyncMock) as run:
        resp = client.post(
            "/api/analyses/from-prompt",
            json={
                "ai_provider": "auto",
                "prompt": (
                    "• What it is: A personalized AI study companion for university students.\n"
                    "• The Problem It Solves: Students struggle to retain lectures and cram inefficiently before exams.\n"
                    "• How It Works: Students upload lecture slides or audio; the AI generates customized flashcards."
                ),
            },
        )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["parsed_idea"]["name"]
    run.assert_awaited_once()
