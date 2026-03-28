"""Pydantic schemas for essay integrity / GenAI detection results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntegrityCheck(BaseModel):
    """Heuristic integrity analysis results for candidate essays."""

    ai_generated_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability that the essay was AI-generated (0-1).",
    )
    plagiarism_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability of plagiarism (0-1).",
    )
    flags: list[str] = Field(
        default_factory=list,
        description="Human-readable integrity concern flags.",
    )
    is_flagged: bool = Field(
        ...,
        description="True if the essay warrants manual review due to integrity concerns.",
    )
