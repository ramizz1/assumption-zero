"""Small helpers for selecting usable text models from provider catalogs."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

_NON_CHAT_MARKERS = (
    "audio",
    "embed",
    "guard",
    "image",
    "moderation",
    "orpheus",
    "realtime",
    "safeguard",
    "speech",
    "transcri",
    "tts",
    "whisper",
)


def catalog_model_ids(payload: object) -> list[str]:
    """Extract active model IDs from an OpenAI-compatible catalog response."""
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        return []

    model_ids: list[str] = []
    for item in payload["data"]:
        if not isinstance(item, dict) or item.get("active") is False:
            continue
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id.strip() and model_id not in model_ids:
            model_ids.append(model_id.strip())
    return model_ids


def looks_like_chat_model(model_id: str) -> bool:
    normalized = model_id.casefold()
    return not any(marker in normalized for marker in _NON_CHAT_MARKERS)


def ordered_models(
    discovered: Iterable[str],
    *,
    configured: str | None = None,
    preferred: Iterable[str] = (),
    compatible: Callable[[str], bool] = looks_like_chat_model,
) -> list[str]:
    """Order configured, preferred, then remaining discovered compatible models."""
    available = [model for model in discovered if compatible(model)]
    available_set = set(available)
    result: list[str] = []

    def add(model: str | None, *, require_discovered: bool = False) -> None:
        if not model or model.casefold() == "auto" or model in result:
            return
        if require_discovered and model not in available_set:
            return
        if compatible(model):
            result.append(model)

    # An explicit setting is an instruction, even when a catalog endpoint is
    # missing or temporarily incomplete. Runtime failures still fall through.
    add(configured)
    for model in preferred:
        add(model, require_discovered=bool(available_set))
    for model in available:
        add(model)
    return result


def completion_content(payload: Any) -> str | None:
    """Read the first text completion without trusting provider response shape."""
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) and content.strip() else None
