from langchain.chat_models.base import BaseChatModel
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage, HumanMessage

from typing import Any, Dict, List, Callable, Optional, Tuple, Awaitable
from tenacity import retry, stop_after_attempt, wait_fixed

from elmes.entity import AgentConfig
from elmes.utils import replace_prompt, remove_think
from elmes.config import CONFIG

import copy


def _init_agent_from_dict(
    ac: AgentConfig,
    model_map: Dict[str, BaseChatModel],
    agent_name: str,
    dynamic_prompt_map: Optional[Dict[str, str]] = None,
) -> Callable[..., Awaitable[Dict[str, List[Any]]]]:
    if dynamic_prompt_map is not None:
        ac_prompt = replace_prompt(ac.prompt, dynamic_prompt_map)
    else:
        ac_prompt = copy.deepcopy(ac.prompt)  # fix shallow copy导致的数据错误
    m = model_map[ac.model]

    @retry(
        stop=stop_after_attempt(CONFIG.globals.retry.attempt),
        wait=wait_fixed(CONFIG.globals.retry.interval),
    )
    async def chatbot(state: AgentState) -> Dict[str, List[Any]]:
        if state["messages"] == []:
            n_m = ac_prompt
        else:
            n_m = []
            for item in state["messages"]:
                content = remove_think(item.content)
                if item.name == agent_name:
                    item = AIMessage(content=content, type="ai")  # type: ignore
                else:
                    item = HumanMessage(content=content, type="human")  # type: ignore
                n_m.append(item)
            if len(n_m) > ac.memory.keep_turns * 2 + 1:
                n_m = n_m[-ac.memory.keep_turns * 2 - 1 :]
            n_m = ac_prompt + n_m
        r = await m.ainvoke(n_m)  # type: ignore
        r.name = agent_name
        return {"messages": [r]}

    return chatbot


def init_agent_map_from_dict(
    model_map: Dict[str, BaseChatModel],
    dynamic_prompt_map: Optional[Dict[str, str]] = None,
) -> Tuple[Dict[str, Tuple[CompiledStateGraph, AgentConfig]], Optional[Dict[str, str]]]:
    result = {}
    acs = CONFIG.agents
    for k, v in acs.items():
        ac = v
        if ac.memory.enable:
            # conn = sqlite3.connect(f"{k}_checkpoint.sqlite", check_same_thread=False)
            # memory = SqliteSaver(conn)
            memory = True
        else:
            memory = None
        model = _init_agent_from_dict(ac, model_map, k, dynamic_prompt_map)
        graph = StateGraph(AgentState)
        graph.add_node("agent", model)
        graph.add_edge(START, "agent")
        graph.add_edge("agent", END)
        result[k] = (graph.compile(checkpointer=memory), ac)
    return result, dynamic_prompt_map


init_agent_map = init_agent_map_from_dict
