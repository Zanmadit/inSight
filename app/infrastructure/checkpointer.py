"""Factory for LangGraph checkpoint persistence backends."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.checkpoint.memory import MemorySaver

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver

    from app.config import Settings


def create_checkpointer(settings: Settings) -> BaseCheckpointSaver:  # noqa: ARG001
    """Create a checkpoint saver for LangGraph state persistence.

    Parameters
    ----------
    settings : Settings
        Application settings (reserved for future use when switching to
        a durable backend such as ``AsyncPostgresSaver``).

    Returns
    -------
    BaseCheckpointSaver
        An in-memory saver suitable for development and testing.
        Swap to ``AsyncPostgresSaver`` for production deployments.
    """
    return MemorySaver()
