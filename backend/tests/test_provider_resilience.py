"""Regression tests for model failover and client-safe provider failures."""
from __future__ import annotations

from collections.abc import Iterable

import httpx
import pytest

from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.llm import (
    groq_adapter,
    ollama_adapter,
    openai_compat_adapter,
    opencode_adapter,
    openrouter_adapter,
)
from assumption_zero.llm.base import LLMAdapter
from assumption_zero.llm.fallback_adapter import FallbackChainAdapter
from assumption_zero.llm.groq_adapter import GroqAdapter
from assumption_zero.llm.ollama_adapter import OllamaAdapter
from assumption_zero.llm.openai_compat_adapter import OpenAICompatAdapter
from assumption_zero.llm.opencode_adapter import OpencodeAdapter
from assumption_zero.llm.openrouter_adapter import OpenRouterAdapter
from assumption_zero.schemas import IdeaInput, PerspectiveName
from assumption_zero.security import public_provider_error, public_provider_status
from assumption_zero.services.analysis_service import build_llm_adapter


class FakeClient:
    def __init__(self, responses: Iterable[httpx.Response], payloads: list[dict]) -> None:
        self._responses = iter(responses)
        self._payloads = payloads

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def post(self, _url: str, *, json: dict) -> httpx.Response:
        self._payloads.append(json)
        return next(self._responses)

    async def get(self, _url: str) -> httpx.Response:
        return response(503, {"error": "catalog unavailable"})


def response(status: int, body: dict) -> httpx.Response:
    return httpx.Response(status, json=body, request=httpx.Request("POST", "https://provider.test"))


class CatalogClient:
    def __init__(self, catalog: dict, responses: Iterable[httpx.Response]) -> None:
        self.catalog = catalog
        self.responses = iter(responses)
        self.get_urls: list[str] = []
        self.post_urls: list[str] = []
        self.payloads: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, url: str) -> httpx.Response:
        self.get_urls.append(url)
        return response(200, self.catalog)

    async def post(self, url: str, *, json: dict) -> httpx.Response:
        self.post_urls.append(url)
        self.payloads.append(json)
        return next(self.responses)


@pytest.mark.asyncio
async def test_openrouter_uses_smart_router_and_reports_actual_model(monkeypatch):
    payloads: list[dict] = []
    actual_model = "z-ai/glm-5.2:free"
    client = FakeClient(
        [response(200, {"model": actual_model, "choices": [{"message": {"content": "{}"}}]})],
        payloads,
    )
    monkeypatch.setattr(openrouter_adapter.httpx, "AsyncClient", lambda **_kwargs: client)

    content, used_model = await OpenRouterAdapter(api_key="runtime-key")._chat(
        [{"role": "user", "content": "test"}]
    )

    assert content == "{}"
    assert used_model == actual_model
    assert payloads[0]["model"] == "openrouter/auto"


@pytest.mark.asyncio
async def test_openrouter_explicit_model_falls_back_to_live_router(monkeypatch):
    payloads: list[dict] = []
    client = FakeClient(
        [
            response(404, {"error": {"message": "model unavailable"}}),
            response(
                200,
                {
                    "model": "qwen/current:free",
                    "choices": [{"message": {"content": "{}"}}],
                },
            ),
        ],
        payloads,
    )
    monkeypatch.setattr(openrouter_adapter.httpx, "AsyncClient", lambda **_kwargs: client)

    await OpenRouterAdapter(api_key="runtime-key", model="vendor/chosen-model")._chat(
        [{"role": "user", "content": "test"}]
    )

    assert [payload["model"] for payload in payloads] == [
        "vendor/chosen-model",
        "openrouter/free",
    ]


@pytest.mark.asyncio
async def test_groq_rate_limit_tries_next_model(monkeypatch):
    payloads: list[dict] = []
    client = FakeClient(
        [
            response(429, {"error": {"message": "busy"}}),
            response(
                200,
                {
                    "model": "openai/gpt-oss-120b",
                    "choices": [{"message": {"content": "{}"}}],
                },
            ),
        ],
        payloads,
    )
    monkeypatch.setattr(groq_adapter.httpx, "AsyncClient", lambda **_kwargs: client)

    content, used_model = await GroqAdapter(api_key="runtime-key")._chat(
        [{"role": "user", "content": "test"}]
    )

    assert content == "{}"
    assert used_model == "openai/gpt-oss-120b"
    assert [payload["model"] for payload in payloads[:2]] == [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
    ]


@pytest.mark.asyncio
async def test_groq_uses_a_newly_discovered_chat_model(monkeypatch):
    client = CatalogClient(
        {"data": [{"id": "future-text-200b", "active": True}]},
        [response(200, {"model": "future-text-200b", "choices": [{"message": {"content": "OK"}}]})],
    )
    monkeypatch.setattr(groq_adapter.httpx, "AsyncClient", lambda **_kwargs: client)

    _, used_model = await GroqAdapter(api_key="runtime-key", model="auto")._chat(
        [{"role": "user", "content": "test"}]
    )

    assert used_model == "future-text-200b"
    assert client.payloads[0]["model"] == "future-text-200b"


@pytest.mark.asyncio
async def test_opencode_migrates_legacy_url_and_selects_current_free_chat_model(monkeypatch):
    client = CatalogClient(
        {
            "data": [
                {"id": "gpt-5.6-sol"},
                {"id": "nemotron-3-ultra-free"},
            ]
        },
        [
            response(
                200,
                {
                    "model": "nemotron-3-ultra-free",
                    "choices": [{"message": {"content": "OK"}}],
                },
            )
        ],
    )
    monkeypatch.setattr(opencode_adapter.httpx, "AsyncClient", lambda **_kwargs: client)
    adapter = OpencodeAdapter(
        api_key="runtime-key",
        model="auto",
        base_url="https://opencode.ai/api/v1",
    )

    _, used_model = await adapter._chat([{"role": "user", "content": "test"}])

    assert used_model == "nemotron-3-ultra-free"
    assert client.get_urls == ["https://opencode.ai/zen/v1/models"]
    assert client.post_urls == ["https://opencode.ai/zen/v1/chat/completions"]


def test_opencode_preserves_current_inference_api_url():
    adapter = OpencodeAdapter(
        api_key="runtime-key",
        model="auto",
        base_url="https://opencode.ai/inference/openai/v1",
    )

    assert adapter._base_url() == "https://opencode.ai/inference/openai/v1"


@pytest.mark.asyncio
async def test_openai_compatible_discovers_model_and_ignores_non_chat_models(monkeypatch):
    client = CatalogClient(
        {"data": [{"id": "whisper-audio"}, {"id": "vendor-current-chat"}]},
        [
            response(
                200,
                {
                    "model": "vendor-current-chat",
                    "choices": [{"message": {"content": "OK"}}],
                },
            )
        ],
    )
    monkeypatch.setattr(openai_compat_adapter.httpx, "AsyncClient", lambda **_kwargs: client)
    adapter = OpenAICompatAdapter(
        api_key="runtime-key",
        model="auto",
        base_url="https://provider.example/v1",
    )

    _, used_model = await adapter._chat([{"role": "user", "content": "test"}])

    assert used_model == "vendor-current-chat"
    assert client.payloads[0]["model"] == "vendor-current-chat"


@pytest.mark.asyncio
async def test_ollama_selects_largest_installed_model(monkeypatch):
    client = CatalogClient(
        {
            "models": [
                {"name": "small-local", "size": 1},
                {"name": "large-local", "size": 10},
            ]
        },
        [
            response(
                200,
                {"model": "large-local", "choices": [{"message": {"content": "OK"}}]},
            )
        ],
    )
    monkeypatch.setattr(ollama_adapter.httpx, "AsyncClient", lambda **_kwargs: client)

    _, used_model = await OllamaAdapter(model="auto")._chat(
        [{"role": "user", "content": "test"}]
    )

    assert used_model == "large-local"
    assert client.payloads[0]["model"] == "large-local"


def test_auto_mode_preserves_provider_specific_runtime_keys():
    adapter = build_llm_adapter(
        provider_override="auto",
        api_keys={"groq": "groq-only", "openrouter": "openrouter-only"},
        allow_mock_fallback=False,
    )

    assert isinstance(adapter, FallbackChainAdapter)
    groq = next(item for item in adapter.adapters if isinstance(item, GroqAdapter))
    openrouter = next(item for item in adapter.adapters if isinstance(item, OpenRouterAdapter))
    assert groq._api_key() == "groq-only"
    assert openrouter._api_key() == "openrouter-only"
    assert all(item.model_id != "deterministic-baseline" for item in adapter.adapters)


@pytest.mark.parametrize(
    ("failure", "status", "phrase"),
    [
        ("HTTP 429 for secret/model", 429, "capacity"),
        ("invalid API key HTTP 401 sk-secret", 400, "rejected"),
        ("connection timeout at https://private.example", 502, "temporarily"),
    ],
)
def test_public_provider_errors_are_classified_without_internal_details(failure, status, phrase):
    message = public_provider_error(RuntimeError(failure))
    assert phrase in message.casefold()
    assert public_provider_status(RuntimeError(failure)) == status
    assert "secret/model" not in message
    assert "sk-secret" not in message
    assert "private.example" not in message


class ExplodingAdapter(LLMAdapter):
    @property
    def model_id(self) -> str:
        return "fallback-chain(openrouter/secret-model)"

    @property
    def is_available(self) -> bool:
        return True

    async def analyze_perspective(self, *_args, **_kwargs):
        raise RuntimeError("HTTP 429 at https://provider.test using sk-secret")


@pytest.mark.asyncio
async def test_engine_stores_one_safe_error_without_perspective_or_model_names():
    engine = AnalysisEngine([], ExplodingAdapter())
    idea = IdeaInput(
        name="Demand Probe",
        description="Test demand safely",
        problem="Founders lack demand evidence",
        target_customer="Independent founders",
        geography="Global",
    )
    errors: list[str] = []

    output = await engine._safe_perspective(
        PerspectiveName.SKEPTICAL_INVESTOR,
        idea,
        [],
        errors,
    )

    assert output is None
    assert errors == [public_provider_error(RuntimeError("HTTP 429"))]
    assert "skeptical" not in errors[0].casefold()
    assert "openrouter" not in errors[0].casefold()
    assert "secret" not in errors[0].casefold()
