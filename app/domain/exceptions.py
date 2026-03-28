"""Domain-level exception hierarchy for the evaluation service."""

from __future__ import annotations


class EvaluationError(Exception):
    """Base exception for all evaluation-domain errors."""

    def __init__(self, detail: str, error_code: str = "EVALUATION_ERROR") -> None:
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class LLMError(EvaluationError):
    """Raised when an LLM API call fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, error_code="LLM_ERROR")


class GraphExecutionError(EvaluationError):
    """Raised when the LangGraph execution encounters an unrecoverable error."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, error_code="GRAPH_EXECUTION_ERROR")


class ThreadNotFoundError(EvaluationError):
    """Raised when a resume is attempted on a non-existent thread."""

    def __init__(self, thread_id: str) -> None:
        super().__init__(
            detail=f"Thread '{thread_id}' not found or has no pending checkpoint.",
            error_code="THREAD_NOT_FOUND",
        )
