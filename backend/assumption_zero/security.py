"""Security primitives for the public API and untrusted provider content."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from collections import defaultdict, deque
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

OWNER_HEADER = "X-Analysis-Owner"
_OWNER_TOKEN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_CONTROL_CHARACTERS = dict.fromkeys(
    [*range(0x00, 0x09), 0x0B, 0x0C, *range(0x0E, 0x20), 0x7F],
    None,
)
_DISPLAY_SPOOFING_CHARACTERS = dict.fromkeys(
    [
        0x061C,
        0x200B,
        0x200C,
        0x200D,
        0x200E,
        0x200F,
        0x202A,
        0x202B,
        0x202C,
        0x202D,
        0x202E,
        0x2060,
        0x2066,
        0x2067,
        0x2068,
        0x2069,
        0xFEFF,
    ],
    None,
)

_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{8,}"),
    re.compile(r"\b(?:sk-(?:or-v1-)?|gsk_|gh[opusr]_)[A-Za-z0-9_-]{8,}"),
    re.compile(
        r"(?i)(\b(?:api[_-]?key|token|authorization|secret)\b\s*[=:]\s*)"
        r"(?:Bearer\s+)?[^\s,;\"']{4,}"
    ),
    re.compile(r"(?i)([?&](?:api[_-]?key|token|access_token|secret)=)[^&#\s]+"),
)


def sanitize_untrusted_text(value: str) -> str:
    """Remove invisible control/spoofing characters while preserving normal text."""
    return value.translate(_CONTROL_CHARACTERS).translate(_DISPLAY_SPOOFING_CHARACTERS).strip()


def redact_sensitive_text(value: object, *, limit: int = 500) -> str:
    """Return log-safe text with common credential formats removed."""
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            text = pattern.sub(r"\1[REDACTED]", text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return sanitize_untrusted_text(text)[:limit]


def hash_owner_token(token: str | None) -> str:
    """Validate a browser capability token and return its one-way hash."""
    candidate = (token or "").strip()
    if not _OWNER_TOKEN.fullmatch(candidate):
        raise ValueError("A valid analysis owner token is required.")
    return hashlib.sha256(candidate.encode("utf-8")).hexdigest()


_AI_CAPACITY_MESSAGE = (
    "No AI generation capacity is available for this key right now. It may have reached "
    "its token or rate limit. Wait briefly, check the provider balance, or choose another provider."
)
_AI_AUTH_MESSAGE = (
    "The AI provider rejected the configured key. Re-enter or verify it in AI Setup."
)
_AI_UNAVAILABLE_MESSAGE = (
    "The AI service is temporarily unavailable. Your key was not stored or exposed. "
    "Try again shortly or choose another provider."
)
_AI_GENERIC_MESSAGE = (
    "The AI service could not complete the analysis. Verify AI Setup and try again."
)


def public_provider_error(error: object | None = None) -> str:
    """Classify an internal provider failure into a fixed, non-sensitive message.

    Upstream response bodies, URLs, provider names, model IDs, and perspective names
    are deliberately never copied into client-visible text.
    """
    text = str(error or "").casefold()
    if any(
        marker in text
        for marker in ("http 402", "http 429", "rate limit", "ratelimit", "quota", "credit")
    ):
        return _AI_CAPACITY_MESSAGE
    if any(
        marker in text
        for marker in ("http 401", "unauthorized", "invalid api key", "key rejected")
    ):
        return _AI_AUTH_MESSAGE
    if any(
        marker in text
        for marker in (
            "timeout",
            "timed out",
            "connection",
            "network",
            "unreachable",
            "http 500",
            "http 502",
            "http 503",
            "http 504",
        )
    ):
        return _AI_UNAVAILABLE_MESSAGE
    return _AI_GENERIC_MESSAGE


def public_provider_status(error: object | None = None) -> int:
    """Map an internal provider failure to an honest HTTP status without leaking it."""
    message = public_provider_error(error)
    if message == _AI_CAPACITY_MESSAGE:
        return 429
    if message == _AI_AUTH_MESSAGE:
        return 400
    return 502


class SecurityMiddleware:
    """Bound request bodies, rate-limit abuse, and attach browser security headers.

    The rate limiter is intentionally dependency-free and per application instance.
    Distributed deployments should additionally enforce platform/WAF rate limits.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_body_bytes: int = 65_536,
        write_limit_per_minute: int = 10,
        read_limit_per_minute: int = 120,
    ) -> None:
        self.app = app
        self.max_body_bytes = max(1_024, max_body_bytes)
        self.write_limit = max(1, write_limit_per_minute)
        self.read_limit = max(self.write_limit, read_limit_per_minute)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", ""))

        if method != "OPTIONS" and not self._allow_request(method, path, headers):
            await self._json_error(
                scope,
                receive,
                send,
                429,
                "Too many requests. Wait one minute and try again.",
                {"Retry-After": "60"},
            )
            return

        replay_receive = receive
        if method in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            more_body = True
            while more_body:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                body.extend(chunk)
                if len(body) > self.max_body_bytes:
                    await self._json_error(
                        scope,
                        receive,
                        send,
                        413,
                        f"Request body exceeds the {self.max_body_bytes // 1024} KB limit.",
                    )
                    return
                more_body = bool(message.get("more_body", False))

            delivered = False

            async def replay_body() -> Message:
                nonlocal delivered
                if delivered:
                    return await receive()
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            replay_receive = replay_body

        async def secure_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers.setdefault("X-Content-Type-Options", "nosniff")
                response_headers.setdefault("X-Frame-Options", "DENY")
                response_headers.setdefault("Referrer-Policy", "no-referrer")
                response_headers.setdefault(
                    "Permissions-Policy",
                    "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
                )
                response_headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
                if path.startswith("/api"):
                    response_headers.setdefault("Cache-Control", "no-store")
                    response_headers.setdefault(
                        "Content-Security-Policy",
                        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
                    )
                forwarded_proto = headers.get("x-forwarded-proto", "")
                if scope.get("scheme") == "https" or forwarded_proto == "https":
                    response_headers.setdefault(
                        "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
                    )
            await send(message)

        await self.app(scope, replay_receive, secure_send)

    def _allow_request(self, method: str, path: str, headers: Headers) -> bool:
        now = time.monotonic()
        window_start = now - 60.0
        is_expensive = method in {"POST", "PUT", "PATCH", "DELETE"}
        limit = self.write_limit if is_expensive else self.read_limit
        raw_owner = headers.get(OWNER_HEADER, "")
        identity = hashlib.sha256(raw_owner[:256].encode("utf-8")).hexdigest()
        key = f"{'write' if is_expensive else 'read'}:{path.split('?')[0]}:{identity}"

        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= window_start:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            if len(self._requests) > 10_000:
                self._requests = defaultdict(
                    deque,
                    {k: v for k, v in self._requests.items() if v and v[-1] > window_start},
                )
        return True

    @staticmethod
    async def _json_error(
        scope: Scope,
        receive: Receive,
        send: Send,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        response = JSONResponse(
            {"detail": detail, "message": detail},
            status_code=status_code,
            headers=headers,
        )
        await response(scope, receive, send)


def untrusted_json(value: Any) -> str:
    """Serialize data without allowing it to change surrounding prompt structure."""
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return (
        serialized.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
