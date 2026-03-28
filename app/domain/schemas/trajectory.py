"""Pydantic schemas for LLM-structured trajectory analysis output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrajectoryAnalysis(BaseModel):
    """Structured output for evaluating a candidate's achievement trajectory
    relative to their socio-economic and educational context (Distance Traveled).
    """

    distance_traveled_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Score representing achievement relative to context (0-10).",
    )
    achievements: list[str] = Field(
        ...,
        description="Key achievements extracted from structured data.",
    )
    contextual_factors: list[str] = Field(
        ...,
        description="Contextual factors that frame the candidate's achievements.",
    )
    reasoning: str = Field(
        ...,
        min_length=1,
        description="Zero-shot reasoning narrative explaining the score.",
    )
