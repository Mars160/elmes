from langchain.chat_models.base import BaseChatModel
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage, HumanMessage

from typing import Any, Dict, List, Callable, Optional, Tuple

from elmes.entity import AgentConfig
from elmes.utils import replace_prompt
from elmes.config import CONFIG


def _init_agent_from_dict(
    ac: AgentConfig,
    model_map: Dict[str, BaseChatModel],
    agent_name: str,
    dynamic_prompt_map: Optional[Dict[str, str]] = None,
) -> Callable[..., Dict[str, List[Any]]]:
    if dynamic_prompt_map is not None:
        ac.prompt = replace_prompt(ac.prompt, dynamic_prompt_map)  # type: ignore
    m = model_map[ac.model]

    def chatbot(state: AgentState) -> Dict[str, List[Any]]:
        # if len(state["messages"]) == 0:
        #     return {"messages": ac.prompt + [m.invoke(state["messages"])]}
        if state["messages"] == []:
            n_m = ac.prompt
        else:
            # n_m = state["messages"]
            n_m = []
            for item in state["messages"]:
                if item.name == agent_name:
                    item = AIMessage(content=item.content, type="ai")
                else:
                    item = HumanMessage(content=item.content, type="human")
                n_m.append(item)
            n_m = ac.prompt + n_m
        r = m.invoke(n_m)  # type: ignore
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
