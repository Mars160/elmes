from typing import Any, Optional, List, Final
from pydantic import BaseModel

from elmes.entity.message import Message


# Agent
class SwitchConfig(BaseModel):
    swap_user_assistant: bool = True


class AgentMemoryConfig(BaseModel):
    enable: bool = True
    id: Optional[str] = None
    keep_turns: int = 3
    # when_switch: SwitchConfig = SwitchConfig()


class AgentConfig(BaseModel):
    model: str
    name: str
    system_prompt: Final[list[str] | str]
    retries: Optional[int] = 3
    memory: AgentMemoryConfig = AgentMemoryConfig(enable=True)

    checkpointer: Optional[Any] = None
