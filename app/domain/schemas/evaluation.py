"""Pydantic schemas for the final synthesizer evaluation output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ComponentScores(BaseModel):
    """Breakdown of scores by evaluation dimension."""

    essay_quality: float = Field(
        ..., ge=0.0, le=10.0, description="Essay quality score (0-10).",
    )
    leadership: float = Field(
        ..., ge=0.0, le=10.0, description="Leadership evidence score (0-10).",
    )
    learning_agility: float = Field(
        ..., ge=0.0, le=10.0, description="Learning agility score (0-10).",
    )
    distance_traveled: float = Field(
        ..., ge=0.0, le=10.0, description="Distance traveled / trajectory score (0-10).",
    )
    integrity: float = Field(
        ..., ge=0.0, le=10.0, description="Integrity / authenticity score (0-10, higher is better).",
    )


class FinalEvaluation(BaseModel):
    """Final explainable evaluation produced by the synthesizer node."""

    overall_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Composite candidate score (1-100).",
    )
    recommendation: Literal[
        "strong_admit", "admit", "waitlist", "deny"
    ] = Field(
        ...,
        description="Admissions recommendation tier.",
    )
    explanation: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation justifying the score and recommendation.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in the evaluation (0-1).",
    )
    component_scores: ComponentScores = Field(
        ...,
        description="Breakdown of scores by evaluation dimension.",
    )
