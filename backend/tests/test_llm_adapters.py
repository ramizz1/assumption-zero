"""
Unit tests for all LLM adapters in Assumption Zero.
"""
import pytest
from assumption_zero.llm import (
    MockAdapter,
    OllamaAdapter,
    GroqAdapter,
    OpenRouterAdapter,
    OpencodeAdapter,
    OpenAICompatAdapter,
    HybridLLMAdapter,
    BetaAdapter,
)
from assumption_zero.services.analysis_service import build_llm_adapter


def test_build_all_llm_adapters():
    providers = ["mock", "ollama", "groq", "openrouter", "opencode", "openai_compat", "hybrid", "beta", "custom"]
    for p in providers:
        adapter = build_llm_adapter(
            provider_override=p,
            api_key_override="test_key_123",
            base_url_override="http://localhost:11434"
        )
        assert adapter is not None
        assert hasattr(adapter, "parse_raw_prompt")
        assert hasattr(adapter, "analyze_perspective")


@pytest.mark.asyncio
async def test_mock_adapter_parse_prompt():
    adapter = MockAdapter()
    idea = await adapter.parse_raw_prompt("Legal AI meeting summarizer for law firms in US")
    assert idea is not None
    assert len(idea.name) > 0
    assert len(idea.problem) > 0
    assert len(idea.target_customer) > 0


@pytest.mark.asyncio
async def test_gibberish_rejection_in_adapters():
    adapter = MockAdapter()
    with pytest.raises(ValueError) as exc:
        await adapter.parse_raw_prompt("the")
    assert "gibberish" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_fallback_chain_adapter():
    from assumption_zero.llm.fallback_adapter import FallbackChainAdapter
    mock = MockAdapter()
    chain = FallbackChainAdapter([mock])
    assert chain.is_available is True
    idea = await chain.parse_raw_prompt("Legal AI meeting summarizer for law firms in US")
    assert idea is not None
    assert len(idea.name) > 0
