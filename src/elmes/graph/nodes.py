"""Graph node definitions."""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, GraphRunContext

from elmes.graph.state import GraphState


class AgentNode(BaseNode[GraphState, None, Any]):
    """Node that wraps a pydantic-ai Agent."""

    agent: Agent
    agent_name: str
    next_node: type[BaseNode[GraphState, None, Any]] | None = None

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> BaseNode[GraphState, None, Any] | End[Any]:
        """Run the agent and return the next node."""
        message_history = ctx.state.messages.get(self.agent_name, [])

        result = await self.agent.run(
            ctx.state.query,
            message_history=message_history,
        )

        ctx.state.messages[self.agent_name] = result.all_messages()
        ctx.state.query = str(result.output)
        ctx.state.query_from = self.agent_name
        ctx.state.node_trace.append(self.agent_name)

        if self.next_node is None:
            return End(None)
        return self.next_node()
