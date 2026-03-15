"""Graph module for building and running agent workflows based on directions."""

from typing import Any

from elmes.graph.builder import GraphBuilder
from elmes.graph.nodes import AgentNode
from elmes.graph.router import Router, RouterNode, ensure_routers_registered
from elmes.graph.state import GraphState

__all__ = [
    "GraphBuilder",
    "AgentNode",
    "RouterNode",
    "Router",
    "GraphState",
    "ensure_routers_registered",
    "build_graph",
]


# Import here to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from pydantic_graph import BaseNode, Graph

    from elmes.config.directions import Direction


def build_graph(
    directions: list["Direction"],
    agents: dict[str, "Agent"],
    recursion_limit: int = 50,
) -> tuple["Graph[GraphState, None, Any]", "type[BaseNode[GraphState, None, Any]]"]:
    """Build a Graph from directions and agent configurations.

    Args:
        directions: List of Direction objects defining the flow
        agents: Dictionary of agent name to Agent instances
        recursion_limit: Maximum number of node executions

    Returns:
        Tuple of (Graph, start_node_class)
    """
    builder = GraphBuilder(directions, recursion_limit)

    for name, agent in agents.items():
        builder.register_agent(name, agent)

    graph, start_node = builder.build()
    builder.bind_agents(builder._node_map, agents)

    return graph, start_node


if __name__ == "__main__":
    from elmes.config import load_config
    from elmes.model import build_model
    from elmes.agent import build_agent
    from elmes.mcp import build_mcp

    config = load_config("config.yaml.example")

    model_dict = {}
    for model_name, model_config in config.models.items():
        model_dict[model_name] = build_model(model_config)

    mcp_dict = {}
    for mcp_name, mcp_config in config.mcps.items():
        mcp_dict[mcp_name] = build_mcp(mcp_config)

    agents = {}
    for agent_name, agent_config in config.agents.items():
        task_vars = config.tasks.content[0] if config.tasks.content else {}
        agents[agent_name] = build_agent(agent_config, model_dict, task_vars, mcp_dict)

    graph, start_node = build_graph(
        config.directions,
        agents,
        config.globals.recursion_limit,
    )

    print("Graph built successfully")
    print(f"Start node: {start_node.__name__}")
