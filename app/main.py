from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.db.session import dispose_engine
from app.features.auth import router as auth_router
from app.features.health import router as health_router

VERSION = "1.0.0"


def _validate_cors_failsafe(settings: Settings) -> None:
    """AC-6 / TC-101-6: ENV=prod + CORS_ORIGINS=* -> boot gagal."""
    if settings.ENV == "prod" and "*" in settings.CORS_ORIGINS:
        raise RuntimeError(
            "CORS_ORIGINS cannot contain '*' when ENV=prod. "
            "Specify explicit origins or remove the wildcard."
        )


def _resolve_cors_origins(settings: Settings) -> list[str]:
    """Dev: izinkan localhost. Staging/Prod: whitelist dari env."""
    if settings.ENV == "dev":
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ]
    return settings.CORS_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown hooks."""
    settings = get_settings()
    configure_logging(settings.ENV)
    _validate_cors_failsafe(settings)
    yield
    await dispose_engine()


def _register_exception_handlers(app: FastAPI) -> None:
    """AC-9: format error konsisten."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # TC-101-14: tidak expose stack trace
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        )


def create_app() -> FastAPI:
    settings = get_settings()

    # AC-2 / TC-101-7: /docs hanya di dev
    docs_url: str | None = "/docs" if settings.ENV == "dev" else None
    redoc_url: str | None = "/redoc" if settings.ENV == "dev" else None
    openapi_url: str | None = "/openapi.json" if settings.ENV == "dev" else None

    app = FastAPI(
        title="NUTRI Backend",
        version=VERSION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # Middleware order: CORS di luar, logging di dalam
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_cors_origins(settings),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    _register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)

    return app


app = create_app()
