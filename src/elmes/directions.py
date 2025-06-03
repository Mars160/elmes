import asyncio
from typing import Dict, Any, Tuple, Optional
from uuid import uuid4
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

import aiosqlite

from elmes.entity import AgentConfig
from elmes.router import *  # noqa: F403
from elmes.config import CONFIG


def add_node_to_graph(graph: StateGraph, node_id: str, node_instance: Any) -> None:
    if node_id not in graph.nodes:
        graph.add_node(node_id, node_instance)
    else:
        pass


async def apply_agent_direction_from_dict(
    agent_map: Dict[str, Tuple[CompiledStateGraph, AgentConfig]],
    memory_id: Optional[str] = None,
    task: Optional[Dict[str, str]] = None,
) -> Tuple[CompiledStateGraph, str]:
    if memory_id is None:
        memory_id = str(uuid4())
    directions = CONFIG.directions
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
    CONFIG.globals.memory.path.mkdir(parents=True, exist_ok=True)
    path = CONFIG.globals.memory.path / f"{memory_id}.db"
    # conn = sqlite3.connect(f"{memory_id}.db", check_same_thread=False)
    if task is not None:
        async with aiosqlite.connect(path) as conn:
            sql = "create table task (key TEXT, value TEXT)"
            await conn.execute(sql)
            sql = "insert into task (key, value) values (?, ?)"
            for key, value in task.items():
                await conn.execute(sql, (key, value))
            await conn.commit()
        # await conn.close()
    conn = aiosqlite.connect(path, check_same_thread=False)
    CONFIG.context.conns.append(conn)

    memory = AsyncSqliteSaver(conn)
    return graph.compile(checkpointer=memory), memory_id


apply_agent_direction = apply_agent_direction_from_dict

if __name__ == "__main__":
    from elmes.model import init_model_map_from_dict
    from elmes.agent import init_agent_map_from_dict
    # from langchain.globals import set_debug

    # set_debug(True)

    async def main():
        model_map = init_model_map_from_dict()

        agent_map, task = init_agent_map_from_dict(
            model_map,
            {
                "image": "无法独立完成最基础的计算，阅读只能逐字识别没有理解，学科知识一无所知。课堂上经常发呆或睡觉，作业本脏乱不堪，老师批评时表现出完全的冷漠。",
                "question": "师徒两人装配自行车，师傅每天装配32辆，徒弟每天比师傅少装配8辆．经过多少天师傅比徒弟多装配56辆？",
            },
        )

        graph, memory_id = await apply_agent_direction_from_dict(agent_map, task=task)

        # print(graph.get_graph().draw_mermaid())

        msg = {
            "role": "user",
            "conent": "这是本次一对一辅导所要讲的习题: 师徒两人装配自行车，师傅每天装配32辆，徒弟每天比师傅少装配8辆．经过多少天师傅比徒弟多装配56辆？",
        }

        events = graph.stream(
            msg,
            {"configurable": {"thread_id": memory_id}},
            stream_mode="values",
        )
        for event in events:
            if len(event["messages"]) > 0:
                event["messages"][-1].pretty_print()

    asyncio.run(main())
