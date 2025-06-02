from langchain.chat_models.base import BaseChatModel
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage, HumanMessage

from typing import Any, Dict, List, Union, Callable, Optional, Tuple
from entity import AgentConfig
from utils import replace_prompt


def _init_agent_from_dict(
    cfg: Union[Dict[str, Union[str, List[Dict[str, str]]]], AgentConfig],
    model_map: Dict[str, BaseChatModel],
    agent_name: str,
    dynamic_prompt_map: Optional[Dict[str, str]] = None,
) -> Callable[..., Dict[str, List[Any]]]:
    if type(cfg) is not AgentConfig:
        ac = AgentConfig(**cfg)  # type: ignore
    else:
        ac = cfg
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
    cfg: Dict[str, Any],
    model_map: Dict[str, BaseChatModel],
    dynamic_prompt_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Tuple[CompiledStateGraph, AgentConfig]]:
    result = {}
    if "agents" in cfg:
        cfg = cfg["agents"]
    for k, v in cfg.items():
        ac = AgentConfig(**v)
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
    return result


if __name__ == "__main__":
    from elmes.utils import parse_yaml
    from pathlib import Path
    from elmes.model import init_model_map_from_dict

    models = parse_yaml(
        Path(__file__).parent.parent / "guided_teaching" / "models.yaml"
    )["models"]
    model_map = init_model_map_from_dict(models)

    agents = parse_yaml(
        Path(__file__).parent.parent / "guided_teaching" / "agents.yaml"
    )["agents"]
    b = init_agent_map_from_dict(
        agents, model_map, {"image": "西瓜", "question": "菠萝"}
    )

    teacher, ac = b["teacher"]

    a = teacher.invoke(
        {"messages": [{"role": "user", "content": "上海今天天气咋样"}]},
        {"configurable": {"thread_id": ac.memory.id}},
    )
    print(a)
