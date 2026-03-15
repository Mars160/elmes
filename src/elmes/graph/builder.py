"""Graph builder for constructing workflows from direction configurations."""

from __future__ import annotations

import re
from typing import Any

from pydantic_ai import Agent
from pydantic_graph import BaseNode, Graph

from elmes.config.directions import Direction
from elmes.graph.nodes import AgentNode
from elmes.graph.router import Router, RouterNode, ensure_routers_registered
from elmes.graph.state import GraphState


class GraphBuilder:
    """Builds a Graph from direction configurations."""

    START = "START"
    END = "END"

    def __init__(self, directions: list[Direction], recursion_limit: int = 50):
        self.directions = directions
        self.recursion_limit = recursion_limit
        self._node_map: dict[str, type[BaseNode[GraphState, None, Any]]] = {}
        self._agent_nodes: dict[str, type[AgentNode]] = {}
        self._router_nodes: dict[str, type[RouterNode]] = {}
        self._router_instances: dict[str, Router] = {}
        self._agents: dict[str, Agent] = {}

        # Ensure built-in routers are registered
        ensure_routers_registered()

    def register_agent(self, name: str, agent: Agent) -> None:
        self._agents[name] = agent

    def _parse_direction(
        self, direction: Direction
    ) -> tuple[str, str, dict[str, Any] | None]:
        from_node = direction.from_
        to_node = direction.to_

        if to_node.startswith("router:"):
            router_str = to_node[7:]
            return self._parse_router_direction(from_node, router_str)

        return from_node, to_node, None

    def _parse_router_direction(
        self, from_node: str, router_str: str
    ) -> tuple[str, str, dict[str, Any]]:
        match = re.match(r"(\w+)\((.+)\)", router_str)
        if not match:
            raise ValueError(f"Invalid router format: {router_str}")

        router_name = match.group(1)
        args_str = match.group(2)

        config: dict[str, Any] = {"router_name": router_name}

        # Parse all keyword arguments dynamically
        # Support patterns: key=value, key="value", key=['a', 'b'], key=True/False
        patterns = [
            (r"(\w+)\s*=\s*\[(.*?)\]", "list"),  # list: keywords=["a", "b"]
            (r'(\w+)\s*=\s*"([^"]*)"', "str"),  # string: target="value"
            (r"(\w+)\s*=\s*'([^']*)'", "str"),  # single quote string
            (r"(\w+)\s*=\s*(\w+)", "raw"),  # raw value: target=END
        ]
        for regex, value_type in patterns:
            for key, value in re.findall(regex, args_str):
                if value_type == "list":
                    items = re.findall(r'["\']([^"\']+)["\']', value)
                    config[key] = items
                elif value_type == "str":
                    config[key] = value
                else:  # raw
                    config[key] = value

        return from_node, router_name, config

    def _build_node_classes(self) -> list[type[BaseNode[GraphState, None, Any]]]:
        node_classes: list[type[BaseNode[GraphState, None, Any]]] = []

        # First pass: identify all nodes
        for direction in self.directions:
            from_node, to_node, router_config = self._parse_direction(direction)

            if from_node not in [self.START, self.END]:
                self._agent_nodes.setdefault(from_node, None)  # type: ignore

            if to_node not in [self.START, self.END] and router_config is None:
                self._agent_nodes.setdefault(to_node, None)  # type: ignore

            if router_config:
                router_name = router_config["router_name"]
                self._router_nodes[router_name] = None  # type: ignore

        # Second pass: build router nodes
        for direction in self.directions:
            from_node, to_node, router_config = self._parse_direction(direction)

            if router_config:
                router_name = router_config["router_name"]
                # Create router instance
                router_class = Router.get_router(router_name)

                # Filter config to only include router-specific args
                router_args = {
                    k: v for k, v in router_config.items() if k != "router_name"
                }
                router_instance = router_class(**router_args)
                self._router_instances[router_name] = router_instance

        # Third pass: build agent -> next_node name mapping from directions
        agent_next_map: dict[str, str] = {}
        for direction in self.directions:
            from_node, to_node, router_config = self._parse_direction(direction)
            if from_node not in [self.START, self.END]:
                if router_config:
                    # Next node is a router
                    router_name = router_config["router_name"]
                    agent_next_map[from_node] = router_name
                elif to_node not in [self.START, self.END]:
                    # Next node is another agent
                    agent_next_map[from_node] = to_node

        # Fourth pass: create node classes
        # Create agent node classes first (without next_node)
        for node_name in self._agent_nodes:
            node_class = self._create_agent_node_class(node_name, None)
            self._agent_nodes[node_name] = node_class  # type: ignore
            self._node_map[node_name] = node_class
            node_classes.append(node_class)

        # Create router node classes (agents may reference them, routers reference agents)
        for router_name, router in self._router_instances.items():
            # Build router table with actual agent node classes
            router_table: dict[str, type[BaseNode[GraphState, None, Any]]] = {}
            for target in router.available_targets:
                if target != self.END and target in self._agent_nodes:
                    router_table[target] = self._agent_nodes[target]

            node_class = self._create_router_node_class(
                router_name, router, router_table
            )
            self._router_nodes[router_name] = node_class  # type: ignore
            self._node_map[router_name] = node_class
            node_classes.append(node_class)

        # Update agent node classes with next_node (now all nodes exist in _node_map)
        for node_name in self._agent_nodes:
            next_node_name = agent_next_map.get(node_name)
            if next_node_name:
                next_node_class = self._node_map.get(next_node_name)
                if next_node_class:
                    self._agent_nodes[node_name].next_node = next_node_class

        return node_classes

    def _create_agent_node_class(
        self,
        node_name: str,
        next_node: type[BaseNode[GraphState, None, Any]] | None = None,
    ) -> type[AgentNode]:
        """Create a dynamic AgentNode subclass."""
        class_dict = {
            "agent": None,
            "agent_name": node_name,
            "next_node": next_node,
        }

        node_class = type(
            f"{node_name}Node",
            (AgentNode,),
            class_dict,
        )

        return node_class  # type: ignore

    def _create_router_node_class(
        self,
        router_name: str,
        router: Router,
        router_table: dict[str, type[BaseNode[GraphState, None, Any]]],
    ) -> type[RouterNode]:
        """Create a dynamic RouterNode subclass."""

        # Create a closure to capture router and router_table
        def init_method(self):
            self.router = router
            self.router_table = router_table

        node_class = type(
            f"{router_name}Node",
            (RouterNode,),
            {
                "__init__": init_method,
            },
        )

        return node_class  # type: ignore

    def build(
        self,
    ) -> tuple[Graph[GraphState, None, Any], type[BaseNode[GraphState, None, Any]]]:
        node_classes = self._build_node_classes()

        if not node_classes:
            raise ValueError("No nodes found in directions")

        start_target = None
        for direction in self.directions:
            if direction.from_ == self.START:
                start_target = direction.to_
                break

        if start_target is None:
            raise ValueError("No START direction found")

        if start_target.startswith("router:"):
            _, router_name, _ = self._parse_direction(
                Direction(from_=self.START, to_=start_target)
            )
            start_node_class = self._node_map.get(router_name)
        else:
            start_node_class = self._node_map.get(start_target)

        if start_node_class is None:
            raise ValueError(f"Start node '{start_target}' not found")

        graph = Graph(nodes=node_classes)

        return graph, start_node_class

    def bind_agents(
        self,
        node_map: dict[str, type[BaseNode[GraphState, None, Any]]],
        agents: dict[str, Agent],
    ) -> None:
        for node_name, node_class in node_map.items():
            if issubclass(node_class, AgentNode):
                if node_name in agents:
                    node_class.agent = agents[node_name]
                    node_class.agent_name = node_name
