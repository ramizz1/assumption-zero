"""
FastAPI application entry point.

Assumption Zero — The open-source MVP validation engine.
"""
from __future__ import annotations

import logging
import re

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from assumption_zero import __version__
from assumption_zero.api.routes import router
from assumption_zero.config import get_settings
from assumption_zero.storage import init_storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


def clean_error_message(msg: str) -> str:
    """Strip Pydantic boilerplate, type signatures, and URLs from error messages."""
    if not isinstance(msg, str):
        msg = str(msg)
    if "Value error, " in msg:
        msg = msg.split("Value error, ")[-1]
    msg = re.sub(r"For further information visit https://errors\.pydantic\.dev/[^\s]+", "", msg)
    msg = re.sub(r"\[type=[^\]]+\]", "", msg)
    msg = re.sub(r"^\d+ validation error(s)? for [^\n:]+:\s*", "", msg, flags=re.IGNORECASE)
    return msg.strip()


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

    # Clean Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        messages = []
        for err in exc.errors():
            raw_msg = err.get("msg", "")
            cleaned = clean_error_message(raw_msg)
            if cleaned and cleaned not in messages:
                messages.append(cleaned)
        clean_detail = " ".join(messages) if messages else "Invalid input provided. Please enter a valid startup idea."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": clean_detail, "message": clean_detail},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, list):
            detail = " ".join([clean_error_message(d.get("msg", "")) if isinstance(d, dict) else clean_error_message(str(d)) for d in detail])
        elif isinstance(detail, str):
            detail = clean_error_message(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "message": detail},
            headers=exc.headers,
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
        await init_storage()
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
