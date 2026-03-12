from elmes.graph.node import GraphNodeInterface, EndNode


class Graph(GraphNodeInterface):
    def __init__(self):
        self.nodes: dict[str, GraphNodeInterface] = {"END": EndNode()}
        self.directions = {}

    def add_node(self, node_id: str, node_instance: GraphNodeInterface):
        if node_id not in self.nodes:
            self.nodes[node_id] = node_instance
        else:
            raise ValueError(f"Node {node_id} already exists in the graph.")

    def add_edge(self, start_node_id: str, end_node_id: str):
        if start_node_id not in self.nodes:
            raise ValueError(f"Start node {start_node_id} does not exist in the graph.")

        if end_node_id not in self.nodes:
            raise ValueError(f"End node {end_node_id} does not exist in the graph.")

        if start_node_id not in self.directions:
            self.directions[start_node_id] = end_node_id
        else:
            raise ValueError(
                f"Start node {start_node_id} already has a direction defined."
            )

    def add_conditional_edges(
        self, start_node_id: str, router_node_id: str, path_map: dict[str, str]
    ):
        if start_node_id not in self.nodes:
            raise ValueError(f"Start node {start_node_id} does not exist in the graph.")

        if router_node_id not in self.nodes:
            raise ValueError(
                f"Router node {router_node_id} does not exist in the graph."
            )

        for end_node_id in path_map.values():
            if end_node_id not in self.nodes:
                raise ValueError(f"End node {end_node_id} does not exist in the graph.")

        if start_node_id not in self.directions:
            self.directions[start_node_id] = (router_node_id, path_map)
        else:
            raise ValueError(
                f"Start node {start_node_id} already has a direction defined."
            )

    def compile(self) -> bool:
        # 检查是否有START节点
        # 检查是否所有节点都有出边（除了END节点）
        # 检查END是否有入边
        
