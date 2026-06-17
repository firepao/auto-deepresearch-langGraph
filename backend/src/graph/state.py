"""State definitions for the LangGraph migration path."""

from __future__ import annotations

from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    """Shared state carried by the experimental LangGraph workflow."""

    topic: str
    status: str
    messages: list[str]
    todo_items: list[dict[str, Any]]
    report_markdown: str
    error: str
