"""Experimental LangGraph workflow scaffold.

The first migration step intentionally keeps the graph minimal. It proves that
LangGraph can be imported, compiled, and invoked behind a feature flag without
changing the existing HelloAgents workflow.
"""

from __future__ import annotations

from typing import Iterator

from .state import ResearchState


class LangGraphWorkflowUnavailable(RuntimeError):
    """Raised when the optional LangGraph dependency is not installed."""


def _load_langgraph() -> tuple[object, str, str]:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise LangGraphWorkflowUnavailable(
            "LangGraph is not installed. Run dependency sync after installing "
            "the project requirements."
        ) from exc

    return StateGraph, START, END


class LangGraphWorkflow:
    """Feature-flagged scaffold used before migrating real research nodes."""

    def __init__(self) -> None:
        StateGraph, START, END = _load_langgraph()
        graph = StateGraph(ResearchState)
        graph.add_node("initialize", self._initialize)
        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", END)
        self._app = graph.compile()

    def invoke(self, topic: str) -> ResearchState:
        """Run the scaffold graph and return its final state."""

        initial_state: ResearchState = {
            "topic": topic,
            "status": "pending",
            "messages": [],
            "todo_items": [],
        }
        return self._app.invoke(initial_state)

    def stream(self, topic: str) -> Iterator[dict[str, object]]:
        """Yield existing-compatible SSE event payloads from the scaffold."""

        yield {"type": "status", "message": "Initializing LangGraph workflow"}
        state = self.invoke(topic)
        yield {
            "type": "status",
            "message": state.get("status", "initialized"),
        }
        yield {
            "type": "final_report",
            "report": state.get("report_markdown", ""),
            "note_id": None,
            "note_path": None,
        }
        yield {"type": "done"}

    @staticmethod
    def _initialize(state: ResearchState) -> ResearchState:
        topic = state.get("topic", "")
        return {
            "status": "langgraph_scaffold_ready",
            "messages": [*state.get("messages", []), "LangGraph scaffold initialized"],
            "report_markdown": (
                "# LangGraph scaffold\n\n"
                f"Topic: {topic}\n\n"
                "The experimental workflow is enabled, but real research nodes "
                "have not been migrated yet."
            ),
        }
