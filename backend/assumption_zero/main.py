"""
FastAPI application entry point.

Assumption Zero — The open-source MVP validation engine.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assumption_zero import __version__
from assumption_zero.api.routes import router
from assumption_zero.config import get_settings
from assumption_zero.models import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Assumption Zero",
        description=(
            "The open-source MVP validation engine. "
            "Stress-test your idea before you build it.\n\n"
            "**Disclaimer:** Assumption Zero provides decision support, not a prediction "
            "or substitute for real customer validation."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Accept"],
    )

    # Routes
    app.include_router(router)

    @app.on_event("startup")
    async def startup() -> None:
        await init_db()
        logger.info(
            "Assumption Zero v%s started | AI provider: %s | Debug: %s",
            __version__,
            settings.ai_provider,
            settings.debug,
        )

    @app.get("/")
    async def root() -> dict:
        return {
            "product": "Assumption Zero",
            "descriptor": "The open-source MVP validation engine",
            "version": __version__,
            "docs": "/docs",
            "disclaimer": (
                "Assumption Zero provides decision support, not a prediction "
                "or substitute for real customer validation."
            ),
        }

    return app


app = create_app()
