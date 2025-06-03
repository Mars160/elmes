from typing import Dict, Any, Optional, List, Annotated
from pydantic import BaseModel
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


# Common
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Global
class GlobalConfig(BaseModel):
    recursion_limit: int = 25


# Model
class ModelConfig(BaseModel):
    api_base: Optional[str]
    api_key: Optional[str]
    kargs: Optional[Dict[str, Any]] = None
    model: Optional[str]
    type: str = "openai"


# Agent
class Prompt(BaseModel):
    role: str
    content: str


class SwitchConfig(BaseModel):
    swap_user_assistant: bool = True


class AgentMemoryConfig(BaseModel):
    enable: bool = True
    id: Optional[str] = None
    when_switch: SwitchConfig = SwitchConfig()


class AgentConfig(BaseModel):
    model: str
    prompt: List[Prompt]
    memory: AgentMemoryConfig = AgentMemoryConfig(enable=True)

    checkpointer: Optional[Any] = None


# Direction
class DirectionConfig(BaseModel):
    from_: str
    to: str


# Task
class TaskConfig(BaseModel):
    start_prompt: List[Prompt]
    variables: List[Dict[str, str]] = []
