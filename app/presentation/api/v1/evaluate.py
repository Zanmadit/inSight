"""Candidate evaluation endpoints (v1).

POST /evaluate          — start a new evaluation (pauses for human review)
POST /evaluate/{id}/resume — resume after human review
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.domain.exceptions import EvaluationError, ThreadNotFoundError
from app.domain.schemas.candidate import (
    EvaluateRequest,
    EvaluateResponse,
    ResumeRequest,
    ResumeResponse,
)
from app.presentation.dependencies import GraphDep, SettingsDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


def _build_config(thread_id: str, settings: SettingsDep) -> dict[str, Any]:
    """Construct the LangGraph invocation config."""
    from app.infrastructure.llm import create_llm_client

    return {
        "configurable": {
            "thread_id": thread_id,
            "llm": create_llm_client(settings),
        }
    }


@router.post(
    "",
    response_model=EvaluateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start candidate evaluation",
    description=(
        "Submit candidate data to begin the AI evaluation pipeline. "
        "The graph executes essay analysis, trajectory analysis, and "
        "integrity checks in parallel, then pauses before the "
        "synthesizer for human review."
    ),
)
async def start_evaluation(
    body: EvaluateRequest,
    graph: GraphDep,
    settings: SettingsDep,
) -> EvaluateResponse:
    thread_id = str(uuid4())
    config = _build_config(thread_id, settings)

    initial_state: dict[str, Any] = {
        "candidate_id": body.candidate_id,
        "raw_structured_data": body.structured_data,
        "raw_essays": body.essays,
    }

    try:
        result = await graph.ainvoke(initial_state, config)
    except EvaluationError:
        raise
    except Exception as exc:
        logger.exception("Graph invocation failed for thread %s", thread_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation pipeline error: {exc}",
        ) from exc

    return EvaluateResponse(
        thread_id=thread_id,
        status="interrupted_before_synthesis",
        state=result,
    )


@router.post(
    "/{thread_id}/resume",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume evaluation after human review",
    description=(
        "Resume the paused evaluation graph. Optionally supply "
        "human-review annotations that the synthesizer will consider "
        "when producing the final score."
    ),
)
async def resume_evaluation(
    thread_id: str,
    body: ResumeRequest,
    graph: GraphDep,
    settings: SettingsDep,
) -> ResumeResponse:
    config = _build_config(thread_id, settings)

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.next:
        raise ThreadNotFoundError(thread_id)

    if body.human_review is not None:
        await graph.aupdate_state(config, {"human_review": body.human_review})

    try:
        result = await graph.ainvoke(None, config)
    except EvaluationError:
        raise
    except Exception as exc:
        logger.exception("Graph resume failed for thread %s", thread_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume pipeline error: {exc}",
        ) from exc

    final_evaluation = result.get("final_evaluation", {})

    return ResumeResponse(
        thread_id=thread_id,
        status="completed",
        final_evaluation=final_evaluation,
    )
