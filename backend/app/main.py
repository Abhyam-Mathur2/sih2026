from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import BMIMException, bmim_exception_handler
from app.core.logging import get_logger

logger = get_logger("bmim")

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions
    logger.info("Starting BMIM backend app", env=settings.environment, debug=settings.debug)
    yield
    # Shutdown actions
    logger.info("Stopping BMIM backend app")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS configuration
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Exception handlers
app.add_exception_handler(BMIMException, bmim_exception_handler)


@app.get("/health", tags=["Health"], summary="Check API health status")
async def health_check() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "app": settings.app_name, "version": settings.app_version},
    )

# Include main API router
app.include_router(api_v1_router, prefix="/api/v1")
