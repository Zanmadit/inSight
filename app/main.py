"""FastAPI application factory for the Candidate Selection Support System."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.application.graph import build_evaluation_graph
from app.config import Settings
from app.domain.exceptions import EvaluationError, ThreadNotFoundError
from app.infrastructure.checkpointer import create_checkpointer
from app.presentation.api.v1.router import router as v1_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialise shared resources on startup."""
    settings = Settings()

    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    checkpointer = create_checkpointer(settings)
    graph = build_evaluation_graph(checkpointer)

    app.state.settings = settings
    app.state.graph = graph

    logger.info("Evaluation graph compiled — ready to accept requests")
    yield


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(
        title="Intelligent Candidate Selection Support System",
        description=(
            "Explainable AI microservice for university admissions evaluation. "
            "Supports human-in-the-loop review before final scoring."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Exception handlers ------------------------------------------------

    @app.exception_handler(ThreadNotFoundError)
    async def _thread_not_found_handler(
        _request: Request,
        exc: ThreadNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    @app.exception_handler(EvaluationError)
    async def _evaluation_error_handler(
        _request: Request,
        exc: EvaluationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    @app.exception_handler(ValidationError)
    async def _validation_error_handler(
        _request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_code": "VALIDATION_ERROR"},
        )

    # ---- Routes -------------------------------------------------------------

    @app.get(
        "/health",
        status_code=status.HTTP_200_OK,
        tags=["system"],
        summary="Health check",
    )
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    app.include_router(v1_router)

    return app


app = create_app()
