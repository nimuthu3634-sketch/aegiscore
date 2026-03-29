from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": _request_id(request)},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation failed", "errors": exc.errors(), "request_id": _request_id(request)},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Database integrity error", extra={"request_id": _request_id(request)}, exc_info=exc)
        return JSONResponse(
            status_code=409,
            content={
                "detail": "A database integrity constraint was violated",
                "errors": ["A unique or relational constraint blocked the requested change."],
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc), "request_id": _request_id(request)})

    @app.exception_handler(TypeError)
    async def type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc), "request_id": _request_id(request)})

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API exception", extra={"request_id": _request_id(request)}, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": _request_id(request)},
        )
