"""LangGraph evaluation graph builder.

Constructs the candidate-evaluation state graph with:
- Three parallel analysis nodes (fan-out from START)
- A synthesizer node that consumes all three (fan-in)
- ``interrupt_before=["synthesizer"]`` for human-in-the-loop review
"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.application.nodes import (
    analyze_essays_node,
    analyze_trajectory_node,
    check_integrity_node,
    synthesizer_node,
)
from app.application.state import CandidateState


def build_evaluation_graph(checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
    """Build and compile the candidate evaluation LangGraph.

    Parameters
    ----------
    checkpointer : BaseCheckpointSaver
        Persistence backend for graph state.  Use ``MemorySaver`` for
        development or ``AsyncPostgresSaver`` for production.

    Returns
    -------
    CompiledStateGraph
        A compiled, ready-to-invoke graph instance.
    """
    graph = StateGraph(CandidateState)

    graph.add_node("analyze_essays", analyze_essays_node)
    graph.add_node("analyze_trajectory", analyze_trajectory_node)
    graph.add_node("check_integrity", check_integrity_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "analyze_essays")
    graph.add_edge(START, "analyze_trajectory")
    graph.add_edge(START, "check_integrity")

    graph.add_edge("analyze_essays", "synthesizer")
    graph.add_edge("analyze_trajectory", "synthesizer")
    graph.add_edge("check_integrity", "synthesizer")

    graph.add_edge("synthesizer", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["synthesizer"],
    )
