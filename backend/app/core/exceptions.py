from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class BMIMException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(BMIMException):
    def __init__(self, resource: str, id: str | int | None = None) -> None:
        msg = f"{resource} not found" if id is None else f"{resource} '{id}' not found"
        super().__init__(msg, status_code=404)


class AuthenticationError(BMIMException):
    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message, status_code=401)


class AuthorizationError(BMIMException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, status_code=403)


class ValidationError(BMIMException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class ConflictError(BMIMException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


async def bmim_exception_handler(request: Request, exc: BMIMException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": type(exc).__name__},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred", "type": type(exc).__name__},
    )

def register_exception_handlers(app) -> None:
    app.add_exception_handler(BMIMException, bmim_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
