"""LangGraph state definition for the candidate evaluation workflow."""

from __future__ import annotations

from typing import Any, TypedDict


class CandidateState(TypedDict, total=False):
    """Shared state threaded through every node in the evaluation graph.

    Each parallel analysis node writes to its own dedicated key so no
    ``Annotated`` reducers are required — there are no concurrent writes
    to the same key.
    """

    candidate_id: str
    raw_structured_data: dict[str, Any]
    raw_essays: list[str]
    essay_analysis: dict[str, Any]
    trajectory_analysis: dict[str, Any]
    integrity_flags: dict[str, Any]
    final_evaluation: dict[str, Any]
    human_review: dict[str, Any] | None
