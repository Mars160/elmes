from typing import Dict, Any, Literal, Optional, List, Annotated
from pydantic import BaseModel, ConfigDict, Field, create_model
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


# FormatField
class FormatField(BaseModel):
    field: str
    type: Literal["str", "int", "float", "bool", "dict"]
    description: str
    items: List["FormatField"] = []


# Evaluation
class EvalConfig(BaseModel):
    model: str
    prompt: List[Prompt]
    format: List[FormatField]

    def format_to_pydantic(self) -> BaseModel:
        def field_type_from_format(f: FormatField) -> tuple:
            """将FormatField转成pydantic字段元组（类型，Field信息）"""
            python_type_map = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
            }

            if f.type == "dict":
                nested_model = build_model_from_format(f.items, f.field)
                return nested_model, Field(..., description=f.description)
            else:
                py_type = python_type_map[f.type]
                return py_type, Field(..., description=f.description)

        def build_model_from_format(
            fields: List[FormatField], model_name: str = "DynamicModel"
        ) -> BaseModel:
            annotations = {}
            for f in fields:
                annotations[f.field] = field_type_from_format(f)
            return create_model(model_name, **annotations)  # type: ignore

        return build_model_from_format(self.format, "GeneratedModel")


# Elmes
class ElmesConfig(BaseModel):
    globals: GlobalConfig
    models: Dict[str, ModelConfig]
    agents: Dict[str, AgentConfig]
    directions: List[str]
    tasks: TaskConfig
    evaluation: EvalConfig

    context: ElmesContext = ElmesContext(conns=[])
