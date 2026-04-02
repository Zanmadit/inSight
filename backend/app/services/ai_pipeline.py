import json
import logging
import re
from decimal import Decimal
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings

logger = logging.getLogger(__name__)

CRITERIA = [
    "achievements",
    "extracurricular_activities",
    "leadership",
    "motivation",
    "growth_mindset",
    "clarity",
    "authenticity",
    "structure",
]

ESSAY_SCORE_SYSTEM = """You are an expert admissions reviewer for inVision U, a scholarship university that values leadership potential, growth mindset, and authentic motivation — not just formal achievements.

Your role is to provide ADVISORY feedback only. You are NOT making an admission decision. Score the essay on the 8 criteria provided. Be constructive, honest, and encouraging. Do not be harsh or dismissive. Never suggest the essay was AI-generated.

FAIRNESS RULES:
- Score only on the content of the essay (writing quality, examples, depth, authenticity).
- Do NOT penalise based on geography, school name, socioeconomic signals, or nationality.
- Focus on trajectory and potential, not just current achievement level.

Return ONLY a valid JSON array matching the schema. No extra text."""


def _score_to_status(score: int) -> str:
    return {1: "weak", 2: "needs_work", 3: "average", 4: "good", 5: "excellent"}.get(
        score, "average"
    )


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY or None, timeout=120)


class AIServiceUnavailableError(Exception):
    pass


class EssayReviewState(TypedDict, total=False):
    essay_text: str
    criteria_scores: list[dict[str, Any]]
    overall_score: float
    summary_feedback: str
    strongest_points: list[str]
    weakest_points: list[str]
    final_suggestion: str


async def _parse_essay(state: EssayReviewState) -> EssayReviewState:
    text = state.get("essay_text", "").strip()
    if not text:
        raise ValueError("Essay is empty")
    _ = len(text.split())
    return {"essay_text": text}


async def _score_criteria(state: EssayReviewState) -> EssayReviewState:
    essay = state["essay_text"]
    llm = _get_llm()
    schema_hint = json.dumps(
        [
            {
                "criteria": "achievements",
                "score": 3,
                "max_score": 5,
                "status": "average",
                "recommendation": "...",
            }
        ]
    )
    human = (
        f"Criteria (must include all 8 exactly once, in any order): {CRITERIA}.\n"
        f"Each item: criteria name, score 1-5 integer, max_score 5, status matching score, recommendation string.\n"
        f"Example shape: {schema_hint}\n\nEssay:\n{essay}"
    )
    try:
        msg = await llm.ainvoke(
            [SystemMessage(content=ESSAY_SCORE_SYSTEM), HumanMessage(content=human)]
        )
        raw = (msg.content or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
    except Exception as e:
        logger.exception("Essay criteria scoring failed: %s", e)
        raise AIServiceUnavailableError(
            "AI service temporarily unavailable. Please try again in a moment."
        ) from e
    if not isinstance(data, list) or len(data) != 8:
        raise AIServiceUnavailableError(
            "AI service temporarily unavailable. Please try again in a moment."
        )
    seen = set()
    fixed: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        crit = item.get("criteria")
        if crit not in CRITERIA or crit in seen:
            continue
        seen.add(str(crit))
        try:
            sc = int(item.get("score", 0))
        except (TypeError, ValueError):
            sc = 3
        sc = max(1, min(5, sc))
        fixed.append(
            {
                "criteria": crit,
                "score": sc,
                "max_score": 5,
                "status": _score_to_status(sc),
                "recommendation": str(item.get("recommendation", "")),
            }
        )
    if len(fixed) != 8:
        for c in CRITERIA:
            if c not in seen:
                fixed.append(
                    {
                        "criteria": c,
                        "score": 3,
                        "max_score": 5,
                        "status": "average",
                        "recommendation": "Not enough signal in the essay for this dimension.",
                    }
                )
                seen.add(c)
        fixed = fixed[:8]
    return {"criteria_scores": fixed}


async def _generate_summary(state: EssayReviewState) -> EssayReviewState:
    criteria = state.get("criteria_scores") or []
    total_score = sum(int(c["score"]) for c in criteria)
    total_max = sum(int(c.get("max_score", 5)) for c in criteria)
    overall = round((total_score / total_max) * 10, 1) if total_max else 0.0
    essay = state["essay_text"]
    llm = _get_llm()
    sys = (
        "You help applicants improve admissions essays. "
        "Return ONLY valid JSON with keys: summary_feedback (string, 2-3 sentences), "
        "strongest_points (array of exactly 3 strings, each max 15 words), "
        "weakest_points (array of exactly 3 strings, each max 15 words), "
        "final_suggestion (string, 1-2 sentences, single most impactful improvement)."
    )
    human = (
        f"Overall score on 0-10 scale (for context): {overall}. Criteria detail: {json.dumps(criteria)}\n\n"
        f"Essay:\n{essay}"
    )
    try:
        msg = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=human)])
        raw = (msg.content or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
    except Exception as e:
        logger.exception("Essay summary generation failed: %s", e)
        raise AIServiceUnavailableError(
            "AI service temporarily unavailable. Please try again in a moment."
        ) from e
    summary_feedback = str(data.get("summary_feedback", ""))
    strongest = data.get("strongest_points") or []
    weakest = data.get("weakest_points") or []
    final_suggestion = str(data.get("final_suggestion", ""))
    while len(strongest) < 3:
        strongest.append("Continue refining specificity and examples.")
    while len(weakest) < 3:
        weakest.append("Add clearer evidence and structure.")
    return {
        "overall_score": overall,
        "summary_feedback": summary_feedback,
        "strongest_points": [str(x) for x in strongest[:3]],
        "weakest_points": [str(x) for x in weakest[:3]],
        "final_suggestion": final_suggestion,
    }


def build_essay_review_graph():
    graph = StateGraph(EssayReviewState)
    graph.add_node("parse_essay", _parse_essay)
    graph.add_node("score_criteria", _score_criteria)
    graph.add_node("generate_summary", _generate_summary)
    graph.set_entry_point("parse_essay")
    graph.add_edge("parse_essay", "score_criteria")
    graph.add_edge("score_criteria", "generate_summary")
    graph.add_edge("generate_summary", END)
    return graph.compile()


async def run_essay_review_graph(essay_text: str) -> dict[str, Any]:
    app = build_essay_review_graph()
    out = await app.ainvoke({"essay_text": essay_text})
    return {
        "review_json": out.get("criteria_scores") or [],
        "overall_score": Decimal(str(out.get("overall_score", 0))),
        "summary_feedback": out.get("summary_feedback", ""),
        "strongest_points": out.get("strongest_points") or [],
        "weakest_points": out.get("weakest_points") or [],
        "final_suggestion": out.get("final_suggestion", ""),
    }


class CandidateScoringState(TypedDict, total=False):
    profile_id: str
    essay_text: str
    gpa: float
    video_transcript: str | None
    latest_essay_review: dict[str, Any]
    essay_component_score: float
    video_component_score: float
    profile_component_score: float
    final_ai_score: float
    ai_summary: str


VIDEO_SCORE_SYSTEM = """You are evaluating a spoken video interview transcript from a university applicant.
Score the transcript on three dimensions: communication clarity, motivation/passion, and use of specific examples.
Each dimension: 0–10. Return ONLY a JSON object: {"clarity": N, "motivation": N, "examples": N}
Be lenient with language errors — many applicants are non-native English speakers. Score content and intent, not grammar.
FAIRNESS: Do not penalise accent signals, regional idioms, or informal speech patterns."""


async def _score_essay_component(state: CandidateScoringState) -> CandidateScoringState:
    review = state.get("latest_essay_review") or {}
    overall = float(review.get("overall_score", 0))
    essay_component = (overall / 10.0) * 50.0
    return {"essay_component_score": essay_component}


async def _score_video_component(state: CandidateScoringState) -> CandidateScoringState:
    transcript = (state.get("video_transcript") or "").strip()
    if not transcript:
        return {"video_component_score": 0.0}
    llm = _get_llm()
    human = f"Transcript only (score content, not demographics):\n{transcript}"
    try:
        msg = await llm.ainvoke(
            [SystemMessage(content=VIDEO_SCORE_SYSTEM), HumanMessage(content=human)]
        )
        raw = (msg.content or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        c = float(data.get("clarity", 0))
        m = float(data.get("motivation", 0))
        e = float(data.get("examples", 0))
    except Exception as e:
        logger.warning("Video scoring LLM failed, using zeros: %s", e)
        c = m = e = 0.0
    for name, val in (("clarity", c), ("motivation", m), ("examples", e)):
        if val < 0 or val > 10:
            logger.warning("Video score %s out of range, clamping", name)
    c = max(0, min(10, c))
    m = max(0, min(10, m))
    e = max(0, min(10, e))
    return {"video_component_score": c + m + e}


async def _aggregate_score(state: CandidateScoringState) -> CandidateScoringState:
    gpa = state.get("gpa")
    if gpa is not None:
        profile_component = min((float(gpa) / 5.0) * 20.0, 20.0)
    else:
        profile_component = 10.0
    essay_part = float(state.get("essay_component_score", 0))
    video_part = float(state.get("video_component_score", 0))
    final = essay_part + video_part + profile_component
    final = round(final, 1)
    return {
        "profile_component_score": profile_component,
        "final_ai_score": final,
    }


async def _write_explanation(state: CandidateScoringState) -> CandidateScoringState:
    llm = _get_llm()
    gpa_val = state.get("gpa")
    sys = (
        "Write an advisory explanation for admissions staff. "
        "Return ONLY plain text (no JSON). 3-5 sentences. "
        "Explain which components contributed most to the total and why, and highlight strongest signals. "
        'End with exactly: "This score is advisory only. The final decision rests with the admissions committee."'
    )
    human = (
        "Scoring inputs for explanation (do not mention IIN, city, or demographics):\n"
        f"- Essay component (0-50): {state.get('essay_component_score')}\n"
        f"- Video component (0-30): {state.get('video_component_score')}\n"
        f"- Profile component from GPA normalization (0-20): {state.get('profile_component_score')}\n"
        f"- Total (0-100): {state.get('final_ai_score')}\n"
        f"- Raw GPA used only in profile component (number): {gpa_val}\n"
    )
    try:
        msg = await llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=human)])
        text = (msg.content or "").strip()
    except Exception as e:
        logger.exception("Explanation generation failed: %s", e)
        raise
    return {"ai_summary": text}


def build_candidate_scoring_graph():
    graph = StateGraph(CandidateScoringState)
    graph.add_node("score_essay_component", _score_essay_component)
    graph.add_node("score_video_component", _score_video_component)
    graph.add_node("aggregate_score", _aggregate_score)
    graph.add_node("write_explanation", _write_explanation)
    graph.set_entry_point("score_essay_component")
    graph.add_edge("score_essay_component", "score_video_component")
    graph.add_edge("score_video_component", "aggregate_score")
    graph.add_edge("aggregate_score", "write_explanation")
    graph.add_edge("write_explanation", END)
    return graph.compile()


async def run_candidate_scoring_graph(
    profile_id: str,
    essay_text: str,
    gpa: float | None,
    video_transcript: str | None,
    latest_essay_review: dict[str, Any],
) -> dict[str, Any]:
    app = build_candidate_scoring_graph()
    init: CandidateScoringState = {
        "profile_id": profile_id,
        "essay_text": essay_text,
        "video_transcript": video_transcript,
        "latest_essay_review": latest_essay_review,
    }
    if gpa is not None:
        init["gpa"] = float(gpa)
    out = await app.ainvoke(init)
    return {"final_ai_score": out.get("final_ai_score"), "ai_summary": out.get("ai_summary", "")}
