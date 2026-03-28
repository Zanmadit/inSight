"""FastAPI dependency injection providers.

All heavy objects (settings, LLM client, checkpointer, compiled graph)
are created once and cached for the lifetime of the process.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from langgraph.graph.state import CompiledStateGraph

from app.config import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton application settings."""
    return Settings()


def get_graph(request: Request) -> CompiledStateGraph:
    """Retrieve the pre-compiled evaluation graph stored on ``app.state``.

    The graph is built once during the application lifespan startup and
    attached to ``request.app.state.graph``.
    """
    return request.app.state.graph  # type: ignore[return-value]


SettingsDep = Annotated[Settings, Depends(get_settings)]
GraphDep = Annotated[CompiledStateGraph, Depends(get_graph)]
