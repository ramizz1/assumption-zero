"""Vercel entrypoint for the Assumption Zero FastAPI service."""

from __future__ import annotations

import os

# Vercel's filesystem is immutable outside /tmp. Synchronous production routes
# read their result in the same invocation, so temporary storage is sufficient
# and no submitted API key or report is persisted by the hosting layer.
os.environ.setdefault("AZERO_DATA_DIR", "/tmp/assumption-zero")
os.environ.setdefault("SSRF_PROTECTION_ENABLED", "true")
os.environ.setdefault(
    "CORS_ORIGINS",
    '["https://assumption-zero-demo.vercel.app",'
    '"https://assumption-zero-demo-richardalmeydas-projects.vercel.app",'
    '"http://localhost:5173"]',
)

from assumption_zero.main import app  # noqa: E402

__all__ = ["app"]
