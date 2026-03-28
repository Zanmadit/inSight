"""Version 1 API router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.v1.evaluate import router as evaluate_router

router = APIRouter(prefix="/api/v1")
router.include_router(evaluate_router)
