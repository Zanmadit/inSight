"""Pydantic schemas for LLM-structured essay analysis output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EssayQuote(BaseModel):
    """A verbatim quote extracted from a candidate essay with trait attribution."""

    quote: str = Field(
        ...,
        min_length=1,
        description="Verbatim excerpt from the candidate's essay.",
    )
    trait: Literal["leadership", "learning_agility"] = Field(
        ...,
        description="The trait this quote demonstrates.",
    )
    reasoning: str = Field(
        ...,
        min_length=1,
        description="Explanation of why this quote evidences the trait.",
    )


class EssayAnalysis(BaseModel):
    """Structured output returned by the essay analysis LLM call."""

    quotes: list[EssayQuote] = Field(
        ...,
        min_length=1,
        description="Verbatim quotes demonstrating leadership or learning agility.",
    )
    leadership_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Score for leadership evidence (0-10).",
    )
    agility_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Score for learning agility evidence (0-10).",
    )
    summary: str = Field(
        ...,
        min_length=1,
        description="Brief narrative summary of essay quality.",
    )
