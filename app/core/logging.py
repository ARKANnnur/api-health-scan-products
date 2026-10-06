import logging
import sys
import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


def configure_logging(env: str = "dev") -> None:
    """Configure structlog: JSON di prod, pretty console di dev."""

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    processors: list[structlog.typing.Processor] = shared_processors.copy()
    if env == "prod":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Bind request context & log setiap request dengan latency."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )

        logger = structlog.get_logger()

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            structlog.contextvars.bind_contextvars(latency_ms=latency_ms)
            logger.exception("request_failed")
            raise

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        structlog.contextvars.bind_contextvars(latency_ms=latency_ms)

        if response.status_code >= 500:
            logger.error("request_completed", status_code=response.status_code)
        elif response.status_code >= 400:
            logger.warning("request_completed", status_code=response.status_code)
        else:
            logger.info("request_completed", status_code=response.status_code)

        response.headers["X-Request-ID"] = request_id
        return response