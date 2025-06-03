from typing import Dict, Any, Optional, List, Annotated
from pydantic import BaseModel, ConfigDict
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pathlib import Path
from aiosqlite import Connection


# Common
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Memory
class Memory(BaseModel):
    path: Path = Path(".")


# Global
class GlobalConfig(BaseModel):
    concurrency: int = 8
    recursion_limit: int = 25
    memory: Memory = Memory()


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


# Task
class TaskConfig(BaseModel):
    start_prompt: Prompt
    variables: List[Dict[str, str]] = []


# Elmes Context
class ElmesContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    conns: List[Connection] = []


# Elmes
class ElmesConfig(BaseModel):
    globals: GlobalConfig
    models: Dict[str, ModelConfig]
    agents: Dict[str, AgentConfig]
    directions: List[str]
    tasks: TaskConfig

    context: ElmesContext = ElmesContext(conns=[])
