from elmes.graph.node import GraphNodeInterface, EndNode, StartNode
from elmes.graph.router import RouterNode
from elmes.entity.message import Message
from elmes.agent import Agent

import logging

END = "END"
START = "START"


class Graph(GraphNodeInterface):
    def __init__(self, recursion_limit: int = 40):
        self.nodes: dict[str, Agent | None | RouterNode | EndNode | StartNode] = {
            END: EndNode(END),
            START: StartNode(START),
        }
        self.directions: dict[str, str] = {}
        self.from_directions: dict[str, set[str]] = {}
        self.router_directions: dict[str, set[str]] = {}
        self.logger = logging.getLogger("graph-directions")
        self._checked = False
        self._all_nodes_not_none = False
        self._node_id_trace: list[str] = []  # 记录node_id的访问顺序，便于导出
        self.call_limit = recursion_limit

    def add_node(self, node_id: str):
        assert not self._checked, "Cannot add nodes after the graph has been checked."
        if node_id in [START, END]:
            return
        else:
            self.nodes[node_id] = None

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
        self, start_node_id: str, router_node_id: str, available_end_node_ids: set[str]
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

        if start_node_id not in self.directions:
            self.directions[start_node_id] = router_node_id
            if router_node_id not in self.from_directions:
                self.from_directions[router_node_id] = set()
            self.from_directions[router_node_id].add(start_node_id)
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
        if START in self.from_directions:
            raise ValueError("START node cannot have incoming edges.")
        if END in self.directions:
            raise ValueError("END node cannot have outgoing edges.")

        # 2. 检查每个节点的出入边
        for node_id in self.nodes:
            if node_id != START and node_id not in self.from_directions:
                raise ValueError(f"Node {node_id} does not have any incoming edges.")
            if (
                node_id != END
                and node_id not in self.directions
                and node_id not in self.router_directions
            ):
                raise ValueError(f"Node {node_id} does not have any outgoing edges.")

        # 3. 检查图的连通性：不仅要能到达END，还要确保没有不可达的孤立节点/分支
        visited = set()
        stack = [START]
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

        if END not in visited:
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

    def replace_node(self, new_node_map: dict[str, Agent | RouterNode]):
        """Check后替换节点实例，确保所有节点均不为None"""
        assert self._checked, "Graph must be checked before replacing nodes."
        replaced_nodes = set([START, END])  # START和END节点不允许被替换
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
        current_node_id: str = self.directions[START]  # pyright: ignore[reportAssignmentType]
        while current_node_id != END and self.call_limit > 0:
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
            elif isinstance(current_node, Agent):
                self.call_limit -= 1
                self._node_id_trace.append(current_node_id)
                response = await current_node.run(*args, **kwargs)
                # 清空args和kwargs，确保每个节点的输入独立
                args = ()
                kwargs = {
                    "query": response,
                    "query_from": current_node.name,
                }
                current_node_id = self.directions[current_node_id]
            else:
                raise TypeError(
                    f"Node {current_node_id}'s type is {type(current_node)} is not a valid executable node."
                )

        return None

    def export(self) -> list[Message]:
        """导出图的执行轨迹为Message列表，便于后续分析和调试"""
        messages = []
        for node_id in self._node_id_trace:
            node: Agent = self.nodes[node_id]  # pyright: ignore[reportAssignmentType]
            assert node is not None, (
                f"Node {node_id} should not be None when exporting."
            )
            assert isinstance(node, Agent), (
                f"Node {node_id} must be an instance of Agent."
            )

            message = next(node.iter_history(), None)
            assert message is not None, "Message should not be None when exporting."
            messages.append(message)
        return messages

    def clone(self) -> "Graph":
        assert self._checked, "Graph must be checked before cloning."
        assert not self._all_nodes_not_none, (
            "Graph with all nodes replaced cannot be cloned to ensure the independence of node instances between different graphs."
        )
        cloned_graph = Graph()
        cloned_graph.nodes = self.nodes.copy()  # 浅复制节点字典，节点实例保持不变
        cloned_graph.directions = self.directions.copy()  # 浅复制方向字典
        cloned_graph.router_directions = (
            self.router_directions.copy()
        )  # 浅复制路由方向字典
        cloned_graph._checked = self._checked  # 复制检查状态
        cloned_graph._all_nodes_not_none = self._all_nodes_not_none  # 复制节点替换状态
        return cloned_graph

    @staticmethod
    def from_direction_config(
        directions: list[str],
    ) -> tuple["Graph", dict[str, RouterNode]]:
        """根据给定的方向列表构建图，方向列表的格式为 ["START->A", "A->B", "B->END"]"""
        graph = Graph()
        router_nodes = {}
        for direction in directions:
            start_node_id, end_node_id = direction.split("->")
            start_node_id, end_node_id = start_node_id.strip(), end_node_id.strip()
            graph.add_node(start_node_id)
            if end_node_id.startswith("router:"):
                router_node_str = end_node_id.split("router:")[1]
                router_node_parts = router_node_str.split("(")
                router_node_id = router_node_parts[0]
                router_node_args_str = router_node_parts[1].strip()
                router_node_args_str = router_node_args_str.rstrip(")")  # 去掉末尾的")"
                # 尝试去import elmes.graph.router.{router_node_id}，如果成功则说明这个router节点是定义好的，否则抛出异常
                try:
                    __import__(f"elmes.graph.router.{router_node_id}")
                except ImportError:
                    try:
                        __import__(f"{router_node_id}")
                    except ImportError:
                        raise ImportError(
                            f"Router node {router_node_id} is neither defined in elmes.graph.router nor can be imported as a module, please ensure that the router node is properly defined and can be imported."
                        )
                assert router_node_id in RouterNode.router_table, (
                    f"Router node {router_node_id} is not defined in the router table."
                )
                graph.add_node(router_node_id)
                router_node_instance: RouterNode = eval(
                    f"RouterNode.router_table[router_node_id]({router_node_args_str})"
                )
                router_nodes[router_node_id] = router_node_instance
                graph.add_conditional_edges(
                    start_node_id, router_node_id, router_node_instance.available_ends
                )
            else:
                graph.add_node(end_node_id)
                graph.add_edge(start_node_id, end_node_id)
        graph.check()
        return graph, router_nodes


if __name__ == "__main__":
    graph, router_nodes = Graph.from_direction_config(
        [
            "START -> A",
            "A -> router:any_keyword_route(keywords=['hello', 'hi'], exists_to='GREET_AGENT', else_to=END)",
            "GREET_AGENT -> END",
        ]
    )
    print(graph.directions)
    print(graph.router_directions)
    print(router_nodes)
