"""backend/api/errors.py — shared API error type and exception handlers.

Guarantees every error response has the shape {"error": "...", "code": "..."}
(architecture doc Part 13) — never a raw stack trace, and never FastAPI's
default validation-error list shape.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raise from a route to produce a clean {"error","code"} response.

    Args:
        status_code: the HTTP status to respond with.
        message: a plain-language error message, safe to show a user.
        code: a short machine-readable error code (e.g. "user_not_found").
    """

    def __init__(self, status_code: int, message: str, code: str) -> None:
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so every error path returns {"error","code"} JSON.

    Complexity: O(1) per request (handler dispatch is not routed here).
    """

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        """Convert a route-raised APIError into its {"error","code"} response."""
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message, "code": exc.code})

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Normalize FastAPI/Starlette's own HTTPException into the same shape."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc.detail), "code": "http_error"},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Normalize pydantic/FastAPI request-validation errors to a 400 (not 422)."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid request parameters", "code": "validation_error"},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all: never let a raw stack trace reach the client."""
        logger.exception("[api] Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "code": "internal_error"},
        )
