from elmes.graph.node import GraphNodeInterface, EndNode, RouterNode, StartNode

import logging


class Graph(GraphNodeInterface):
    def __init__(self):
        self.nodes: dict[
            str, GraphNodeInterface | None | RouterNode | EndNode | StartNode
        ] = {"END": EndNode("END"), "START": StartNode("START")}
        self.directions: dict[str, str] = {}
        self.from_directions: dict[str, set[str]] = {}
        self.router_directions: dict[str, set[str]] = {}
        self.logger = logging.getLogger("directions")
        self._checked = False
        self._all_nodes_not_none = False

    def add_node(self, node_id: str):
        assert not self._checked, "Cannot add nodes after the graph has been checked."
        if node_id not in self.nodes:
            self.nodes[node_id] = None
        else:
            raise ValueError(f"Node {node_id} already exists in the graph.")

    def add_edge(self, start_node_id: str, end_node_id: str):
        assert not self._checked, "Cannot add edges after the graph has been checked."

        if start_node_id not in self.nodes:
            raise ValueError(f"Start node {start_node_id} does not exist in the graph.")

        if end_node_id not in self.nodes:
            raise ValueError(f"End node {end_node_id} does not exist in the graph.")

        if start_node_id not in self.directions:
            self.directions[start_node_id] = end_node_id
            if end_node_id not in self.from_directions:
                self.from_directions[end_node_id] = set()
            self.from_directions[end_node_id].add(start_node_id)
        else:
            raise ValueError(
                f"Start node {start_node_id} already has a direction defined."
            )

    def add_conditional_edges(
        self, start_node_id: str, router_node_id: str, available_end_node_ids: list[str]
    ):
        assert not self._checked, "Cannot add edges after the graph has been checked."
        self.logger.warning(
            f"elmes can't automatically check the validity of conditional edges, please ensure that the path_map is correct and router {router_node_id} is properly defined."
        )
        if start_node_id not in self.nodes:
            raise ValueError(f"Start node {start_node_id} does not exist in the graph.")

        if router_node_id not in self.nodes:
            raise ValueError(
                f"Router node {router_node_id} does not exist in the graph."
            )

        for end_node_id in available_end_node_ids:
            if end_node_id not in self.nodes:
                raise ValueError(f"End node {end_node_id} does not exist in the graph.")

        if start_node_id not in self.directions:
            self.directions[start_node_id] = router_node_id
            self.router_directions[router_node_id] = set(available_end_node_ids)
            for end_node_id in available_end_node_ids:
                if end_node_id not in self.from_directions:
                    self.from_directions[end_node_id] = set()
                self.from_directions[end_node_id].add(router_node_id)
        else:
            raise ValueError(
                f"Start node {start_node_id} already has a direction defined."
            )

    def check(self) -> bool:
        if self._checked:
            return True

        # 1. 检查起始与结束节点约束
        if "START" in self.from_directions:
            raise ValueError("START node cannot have incoming edges.")
        if "END" in self.directions:
            raise ValueError("END node cannot have outgoing edges.")

        # 2. 检查每个节点的出入边
        for node_id in self.nodes:
            if node_id != "START" and node_id not in self.from_directions:
                raise ValueError(f"Node {node_id} does not have any incoming edges.")
            if (
                node_id != "END"
                and node_id not in self.directions
                and node_id not in self.router_directions
            ):
                raise ValueError(f"Node {node_id} does not have any outgoing edges.")

        # 3. 检查图的连通性：不仅要能到达END，还要确保没有不可达的孤立节点/分支
        visited = set()
        stack = ["START"]
        while stack:
            current_node_id = stack.pop()
            if current_node_id in visited:
                continue
            visited.add(current_node_id)
            if current_node_id in self.directions:
                stack.append(self.directions[current_node_id])
            if current_node_id in self.router_directions:
                for next_node_id in self.router_directions[current_node_id]:
                    stack.append(next_node_id)

        if "END" not in visited:
            raise ValueError("END node is not reachable from START node.")

        # 检查是否所有注册的节点都在连通图中
        if len(visited) != len(self.nodes):
            unreachable_nodes = set(self.nodes.keys()) - visited
            raise ValueError(
                f"Graph contains unreachable nodes from START: {unreachable_nodes}"
            )

        # 4. 校验全部通过，清理临时状态
        self.from_directions.clear()
        self._checked = True
        return True

    def replace_node(self, new_node_map: dict[str, GraphNodeInterface | RouterNode]):
        """Check后替换节点实例，确保所有节点均不为None"""
        assert self._checked, "Graph must be checked before replacing nodes."
        replaced_nodes = set(["START", "END"])  # START和END节点不允许被替换
        for node_id, new_node in new_node_map.items():
            if node_id in self.nodes:
                self.nodes[node_id] = new_node
                replaced_nodes.add(node_id)
            else:
                self.logger.warning(
                    f"Node {node_id} does not exist in the graph, cannot replace."
                )
        # 检查是否所有节点都被替换了
        for node_id in self.nodes:
            if node_id not in replaced_nodes:
                raise ValueError(
                    f"Node {node_id} has not been replaced with an instance."
                )
        self._all_nodes_not_none = True

    async def run(self, *args, **kwargs):
        assert self._checked, "Graph must be checked before running."
        assert self._all_nodes_not_none, (
            "All nodes must be replaced with instances before running."
        )
        current_node_id: str = self.directions["START"]  # pyright: ignore[reportAssignmentType]
        while current_node_id != "END":
            current_node = self.nodes[current_node_id]
            if isinstance(current_node, RouterNode):
                next_node_id = await current_node.run(*args, **kwargs)  # pyright: ignore[reportOptionalMemberAccess]
                assert next_node_id is not None, (
                    "Router node must return a valid next node id."
                )
                if next_node_id not in self.router_directions[current_node_id]:
                    raise ValueError(
                        f"Router node {current_node_id} returned invalid next node id {next_node_id}."
                    )
                current_node_id = next_node_id
                continue
            else:
                assert isinstance(current_node, GraphNodeInterface), (
                    f"Node {current_node_id} must be an instance of GraphNodeInterface."
                )
                response = await current_node.run(*args, **kwargs)
                # 清空args和kwargs，确保每个节点的输入独立
                args = ()
                kwargs = {
                    "query": response,
                    "query_from": current_node.name,
                }
                current_node_id = self.directions[current_node_id]
        return None
