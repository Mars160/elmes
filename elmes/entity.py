from typing import Dict, Any, Optional, List, Annotated
from pydantic import BaseModel
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.checkpoint.base import BaseCheckpointSaver

import uuid

MEMORY_ID = str(uuid.uuid4())


# Common
class State(TypedDict):
    messages: Annotated[list, add_messages]


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
    memory: AgentMemoryConfig = AgentMemoryConfig(enable=True, id=MEMORY_ID)

    checkpointer: Optional[Any] = None

    # 添加初始化方法
    def __init__(self, **data):
        super().__init__(**data)
        if self.memory.id is None:
            self.memory.id = MEMORY_ID


# Direction
class DirectionConfig(BaseModel):
    from_: str
    to: str
