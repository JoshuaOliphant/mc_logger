# ABOUTME: FastAPI ASGI middleware for automatic request/response logging
# ABOUTME: Provides zero-configuration instrumentation with header redaction

"""FastAPI middleware for automatic request/response logging."""

import time
import traceback
from typing import Callable, Optional, Set

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from mc_logger.context import set_request_id, reset_request_id, clear_context
from mc_logger.core import get_logger


# Sensitive headers to redact
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-csrf-token",
    "x-auth-token",
}

# Default paths to exclude from logging
DEFAULT_EXCLUDE_PATHS = {"/health", "/healthz", "/ping", "/_health"}


class MCLoggerMiddleware(BaseHTTPMiddleware):
    """ASGI middleware for automatic request/response logging."""

    def __init__(
        self,
        app,
        logger=None,
        exclude_paths: Optional[Set[str]] = None,
    ):
        """Initialize middleware with optional logger and exclude paths."""
        super().__init__(app)
        self.logger = logger or get_logger()
        self.exclude_paths = exclude_paths or DEFAULT_EXCLUDE_PATHS

    def _redact_headers(self, headers: dict) -> dict:
        """Redact sensitive header values."""
        redacted = {}
        for key, value in headers.items():
            if key.lower() in SENSITIVE_HEADERS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        return redacted

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with automatic logging."""
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Set request ID from header or generate new one
        request_id_header = request.headers.get("x-request-id")
        token = set_request_id(request_id_header)

        # Get the actual request_id that was set (generated or from header)
        from mc_logger.context import get_request_id
        actual_request_id = get_request_id() or ""

        start_time = time.time()

        try:
            # Log request start
            self.logger.log(
                level="INFO",
                message="request.start",
                source="middleware",
                metadata={
                    "method": request.method,
                    "path": str(request.url.path),
                    "query_params": dict(request.query_params),
                    "headers": self._redact_headers(dict(request.headers)),
                    "client": request.client.host if request.client else None,
                },
            )

            # Execute request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            slow_request = duration_ms > 1000

            # Log request complete
            self.logger.log(
                level="INFO",
                message="request.complete",
                source="middleware",
                metadata={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "slow_request": slow_request,
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = actual_request_id

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request error
            self.logger.log(
                level="ERROR",
                message="request.error",
                source="middleware",
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                    "duration_ms": duration_ms,
                },
            )

            # Re-raise exception
            raise

        finally:
            # Reset context
            reset_request_id(token)
            clear_context()


def instrument_fastapi(
    app: FastAPI,
    logger=None,
    exclude_paths: Optional[Set[str]] = None,
):
    """Add MC Logger middleware to FastAPI application."""
    app.add_middleware(
        MCLoggerMiddleware,
        logger=logger,
        exclude_paths=exclude_paths,
    )
