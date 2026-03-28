"""Async graph node functions for the candidate evaluation workflow.

Each node receives the shared ``CandidateState`` and a LangGraph
``RunnableConfig``.  The LLM client is passed via
``config["configurable"]["llm"]`` to keep the application layer
decoupled from infrastructure.
"""

from __future__ import annotations

import hashlib
import logging
import statistics
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from app.application.state import CandidateState
from app.domain.exceptions import LLMError
from app.domain.schemas.essay import EssayAnalysis
from app.domain.schemas.evaluation import FinalEvaluation
from app.domain.schemas.trajectory import TrajectoryAnalysis

logger = logging.getLogger(__name__)


def _get_llm(config: RunnableConfig) -> ChatOpenAI:
    """Extract the LLM client from the run configuration."""
    llm: ChatOpenAI | None = config.get("configurable", {}).get("llm")
    if llm is None:
        raise LLMError("LLM client was not provided in the graph configuration.")
    return llm


# ---------------------------------------------------------------------------
# Node 1 — Essay Analysis
# ---------------------------------------------------------------------------

async def analyze_essays_node(
    state: CandidateState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Analyse candidate essays for leadership and learning-agility evidence.

    Parameters
    ----------
    state : CandidateState
        Current graph state containing ``raw_essays``.
    config : RunnableConfig
        LangGraph runtime configuration carrying the LLM client.

    Returns
    -------
    dict[str, Any]
        Partial state update with the ``essay_analysis`` key populated.

    Notes
    -----
    Uses ``ChatOpenAI.with_structured_output(EssayAnalysis)`` to guarantee
    the response conforms to the ``EssayAnalysis`` Pydantic schema.
    """
    llm = _get_llm(config)
    structured_llm = llm.with_structured_output(EssayAnalysis)

    essays_text = "\n\n---\n\n".join(state["raw_essays"])
    system_prompt = (
        "You are an expert university admissions essay evaluator. "
        "Your task is to extract verbatim quotes from the candidate's essays "
        "that demonstrate either LEADERSHIP or LEARNING AGILITY. "
        "For each quote, explain why it evidences the trait. "
        "Then provide an overall leadership score and learning-agility score "
        "(each 0-10) and a brief narrative summary."
    )

    try:
        result: EssayAnalysis = await structured_llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Candidate essays:\n\n{essays_text}"),
            ]
        )
    except Exception as exc:
        logger.exception("Essay analysis LLM call failed for candidate %s", state.get("candidate_id"))
        raise LLMError(f"Essay analysis failed: {exc}") from exc

    logger.info(
        "Essay analysis complete for candidate %s — leadership=%.1f, agility=%.1f",
        state.get("candidate_id"),
        result.leadership_score,
        result.agility_score,
    )
    return {"essay_analysis": result.model_dump()}


# ---------------------------------------------------------------------------
# Node 2 — Trajectory / Distance-Traveled Analysis
# ---------------------------------------------------------------------------

async def analyze_trajectory_node(
    state: CandidateState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Evaluate the candidate's achievement trajectory relative to context.

    Uses zero-shot reasoning to assess "Distance Traveled" — how
    impressive the candidate's accomplishments are given their
    socio-economic and educational background.

    Parameters
    ----------
    state : CandidateState
        Current graph state containing ``raw_structured_data``.
    config : RunnableConfig
        LangGraph runtime configuration carrying the LLM client.

    Returns
    -------
    dict[str, Any]
        Partial state update with the ``trajectory_analysis`` key populated.
    """
    llm = _get_llm(config)
    structured_llm = llm.with_structured_output(TrajectoryAnalysis)

    import json
    profile_text = json.dumps(state["raw_structured_data"], indent=2)

    system_prompt = (
        "You are an expert university admissions evaluator specializing in "
        "holistic review. Evaluate the candidate's achievements relative to "
        "their context (socio-economic background, school resources, geographic "
        "constraints). This is called 'Distance Traveled' assessment.\n\n"
        "Identify key achievements, note contextual factors, then assign a "
        "Distance Traveled score from 0 to 10 and explain your reasoning."
    )

    try:
        result: TrajectoryAnalysis = await structured_llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Candidate structured profile:\n\n{profile_text}"),
            ]
        )
    except Exception as exc:
        logger.exception("Trajectory analysis LLM call failed for candidate %s", state.get("candidate_id"))
        raise LLMError(f"Trajectory analysis failed: {exc}") from exc

    logger.info(
        "Trajectory analysis complete for candidate %s — distance_traveled=%.1f",
        state.get("candidate_id"),
        result.distance_traveled_score,
    )
    return {"trajectory_analysis": result.model_dump()}


# ---------------------------------------------------------------------------
# Node 3 — Integrity / GenAI Detection (heuristic mock)
# ---------------------------------------------------------------------------

async def check_integrity_node(
    state: CandidateState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Run heuristic integrity checks on candidate essays.

    This is a **mock / heuristic** node that does not call an LLM.
    It computes simple text-statistics signals (sentence-length variance,
    vocabulary richness, deterministic hash-based noise) and returns
    probability scores for AI-generation and plagiarism.

    Parameters
    ----------
    state : CandidateState
        Current graph state containing ``raw_essays``.
    config : RunnableConfig
        Unused — included for LangGraph node signature compatibility.

    Returns
    -------
    dict[str, Any]
        Partial state update with the ``integrity_flags`` key populated.
    """
    combined_text = " ".join(state["raw_essays"])
    words = combined_text.split()
    sentences = [s.strip() for s in combined_text.replace("!", ".").replace("?", ".").split(".") if s.strip()]

    word_count = len(words)
    unique_ratio = len(set(w.lower() for w in words)) / max(word_count, 1)

    sentence_lengths = [len(s.split()) for s in sentences]
    length_variance = statistics.variance(sentence_lengths) if len(sentence_lengths) > 1 else 0.0

    digest = hashlib.sha256(combined_text.encode()).hexdigest()
    hash_noise = int(digest[:8], 16) / 0xFFFFFFFF

    ai_prob = round(max(0.0, min(1.0, 0.5 - unique_ratio + 0.1 * hash_noise)), 3)
    plagiarism_prob = round(max(0.0, min(1.0, 0.3 - (length_variance / 100) + 0.05 * hash_noise)), 3)

    flags: list[str] = []
    if ai_prob > 0.6:
        flags.append("HIGH_AI_GENERATED_PROBABILITY")
    if plagiarism_prob > 0.5:
        flags.append("HIGH_PLAGIARISM_PROBABILITY")
    if unique_ratio < 0.35:
        flags.append("LOW_VOCABULARY_DIVERSITY")

    is_flagged = len(flags) > 0

    logger.info(
        "Integrity check for candidate %s — ai_prob=%.3f, plagiarism_prob=%.3f, flagged=%s",
        state.get("candidate_id"),
        ai_prob,
        plagiarism_prob,
        is_flagged,
    )
    return {
        "integrity_flags": {
            "ai_generated_probability": ai_prob,
            "plagiarism_probability": plagiarism_prob,
            "flags": flags,
            "is_flagged": is_flagged,
        }
    }


# ---------------------------------------------------------------------------
# Node 4 — Synthesizer (Lead Evaluator)
# ---------------------------------------------------------------------------

async def synthesizer_node(
    state: CandidateState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Produce the final explainable evaluation by synthesizing all analyses.

    Acts as the "Lead Evaluator": reads essay analysis, trajectory
    analysis, integrity flags, and any human-review annotations, then
    generates a composite score (1-100) with an explainable recommendation.

    Parameters
    ----------
    state : CandidateState
        Full graph state after the three parallel analysis nodes and
        optional human review.
    config : RunnableConfig
        LangGraph runtime configuration carrying the LLM client.

    Returns
    -------
    dict[str, Any]
        Partial state update with the ``final_evaluation`` key populated.
    """
    llm = _get_llm(config)
    structured_llm = llm.with_structured_output(FinalEvaluation)

    import json
    context_parts = [
        f"## Essay Analysis\n{json.dumps(state.get('essay_analysis', {}), indent=2)}",
        f"## Trajectory Analysis\n{json.dumps(state.get('trajectory_analysis', {}), indent=2)}",
        f"## Integrity Flags\n{json.dumps(state.get('integrity_flags', {}), indent=2)}",
    ]
    human_review = state.get("human_review")
    if human_review:
        context_parts.append(
            f"## Human Reviewer Notes\n{json.dumps(human_review, indent=2)}"
        )

    context_block = "\n\n".join(context_parts)

    system_prompt = (
        "You are the Lead Evaluator for a university admissions committee. "
        "You have received analyses from three specialist evaluators (essay "
        "analysis, trajectory/distance-traveled analysis, and an integrity "
        "check). You may also have notes from a human admissions officer.\n\n"
        "Synthesize all inputs into a SINGLE final evaluation:\n"
        "1. An overall score from 1 to 100.\n"
        "2. A recommendation: strong_admit, admit, waitlist, or deny.\n"
        "3. A clear, explainable narrative justifying your decision.\n"
        "4. Your confidence level (0-1).\n"
        "5. Component scores breaking down contributions from each dimension.\n\n"
        "Be transparent and cite specific evidence from the analyses."
    )

    try:
        result: FinalEvaluation = await structured_llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Candidate ID: {state.get('candidate_id')}\n\n{context_block}"),
            ]
        )
    except Exception as exc:
        logger.exception("Synthesizer LLM call failed for candidate %s", state.get("candidate_id"))
        raise LLMError(f"Synthesizer evaluation failed: {exc}") from exc

    logger.info(
        "Synthesis complete for candidate %s — score=%d, recommendation=%s",
        state.get("candidate_id"),
        result.overall_score,
        result.recommendation,
    )
    return {"final_evaluation": result.model_dump()}
