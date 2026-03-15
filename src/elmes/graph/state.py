"""Graph state definitions."""

from dataclasses import dataclass, field

from pydantic_ai.messages import ModelMessage


@dataclass
class GraphState:
    """State shared across all nodes in the graph."""

    query: str = ""
    query_from: str = ""
    messages: dict[str, list[ModelMessage]] = field(default_factory=dict)
    node_trace: list[str] = field(default_factory=list)
