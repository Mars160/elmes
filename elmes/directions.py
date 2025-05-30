from typing import Dict, Any, Sequence, Union, Tuple
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.checkpoint.sqlite import SqliteSaver

import sqlite3

from entity import AgentConfig, MEMORY_ID
from router import *  # noqa: F403


def add_node_to_graph(graph: StateGraph, node_id: str, node_instance: Any) -> None:
    if node_id not in graph.nodes:
        graph.add_node(node_id, node_instance)
    else:
        pass


def apply_agent_direction_from_dict(
    cfg: Union[Dict[str, Any], Sequence[str]],
    agent_map: Dict[str, Tuple[CompiledStateGraph, AgentConfig]],
) -> CompiledStateGraph:
    if isinstance(cfg, dict):
        directions = cfg.get("directions")
        if not directions:
            raise ValueError("No 'directions' provided in the configuration.")
    else:
        directions = cfg
    graph = StateGraph(AgentState)
    for node_id, node_instance in agent_map.items():
        graph.add_node(node_id, node_instance[0])

    for direction in directions:
        start_node, end_node = (i.strip() for i in direction.split("->"))
        if start_node == "START":
            start_node = START
        if end_node.startswith("router:"):
            function_call = end_node[len("router:") :]
            route, path_map = eval(function_call)
            end_node = end_node.replace(":", "_")
            graph.add_conditional_edges(start_node, route, path_map)
            continue
            # add_node_to_graph(graph, end_node, route)
        elif end_node == "END":
            end_node = END
        else:
            agent_config = agent_map[end_node][1]
            pregel_instance = agent_map[end_node][0]
            if not pregel_instance or not agent_config:
                raise ValueError(f"Invalid configuration for {end_node}.")
        graph.add_edge(start_node, end_node)
    conn = sqlite3.connect("agent_graph.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    return graph.compile(checkpointer=memory)


if __name__ == "__main__":
    from elmes.utils import parse_yaml
    from pathlib import Path
    from elmes.model import init_model_map_from_dict
    from elmes.agent import init_agent_map_from_dict
    # from langchain.globals import set_debug

    # set_debug(True)

    models = parse_yaml(
        Path(__file__).parent.parent / "guided_teaching" / "models.yaml"
    )["models"]
    model_map = init_model_map_from_dict(models)

    agents = parse_yaml(
        Path(__file__).parent.parent / "guided_teaching" / "agents.yaml"
    )["agents"]
    agent_map = init_agent_map_from_dict(
        agents,
        model_map,
        {
            "image": "无法独立完成最基础的计算，阅读只能逐字识别没有理解，学科知识一无所知。课堂上经常发呆或睡觉，作业本脏乱不堪，老师批评时表现出完全的冷漠。",
            "question": "师徒两人装配自行车，师傅每天装配32辆，徒弟每天比师傅少装配8辆．经过多少天师傅比徒弟多装配56辆？",
        },
    )

    directions = parse_yaml(
        Path(__file__).parent.parent / "guided_teaching" / "directions.yaml"
    )
    graph = apply_agent_direction_from_dict(directions, agent_map)
    # print(graph.get_graph().draw_mermaid())

    msg = {
        "role": "user",
        "conent": "这是本次一对一辅导所要讲的习题: 师徒两人装配自行车，师傅每天装配32辆，徒弟每天比师傅少装配8辆．经过多少天师傅比徒弟多装配56辆？",
    }

    events = graph.stream(
        msg,
        {"configurable": {"thread_id": MEMORY_ID}},
        stream_mode="values",
    )
    for event in events:
        if len(event["messages"]) > 0:
            event["messages"][-1].pretty_print()
