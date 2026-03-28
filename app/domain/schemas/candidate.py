"""Pydantic schemas for the candidate evaluation API request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    """Payload submitted to start a candidate evaluation."""

    candidate_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the candidate.",
    )
    structured_data: dict[str, Any] = Field(
        ...,
        description=(
            "Structured candidate profile data (GPA, test scores, "
            "extracurriculars, demographics, etc.)."
        ),
    )
    essays: list[str] = Field(
        ...,
        min_length=1,
        description="One or more candidate essays to evaluate.",
    )


class EvaluateResponse(BaseModel):
    """Response returned after the graph pauses at the human-review checkpoint."""

    thread_id: str = Field(
        ...,
        description="Unique thread identifier used to resume evaluation.",
    )
    status: str = Field(
        ...,
        description="Current graph execution status.",
    )
    state: dict[str, Any] = Field(
        ...,
        description=(
            "Snapshot of graph state at the interrupt point, containing "
            "essay_analysis, trajectory_analysis, and integrity_flags."
        ),
    )


class ResumeRequest(BaseModel):
    """Payload submitted by an admissions officer to resume evaluation."""

    human_review: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional human review notes, overrides, or annotations "
            "to feed into the synthesizer."
        ),
    )


class ResumeResponse(BaseModel):
    """Response returned after the graph completes final evaluation."""

    thread_id: str = Field(
        ...,
        description="Thread identifier for this evaluation run.",
    )
    status: str = Field(
        ...,
        description="Final graph execution status.",
    )
    final_evaluation: dict[str, Any] = Field(
        ...,
        description="Complete explainable evaluation produced by the synthesizer.",
    )
