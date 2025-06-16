import json
import re
from typing import Dict, Any, Literal, Optional, List, Annotated, Tuple, Final
from pydantic import BaseModel, ConfigDict, Field, create_model
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pathlib import Path
from aiosqlite import Connection
from polyfactory.factories.pydantic_factory import ModelFactory


# Common
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Memory
class Memory(BaseModel):
    path: Path = Path(".")


# RetryConfig
class RetryConfig(BaseModel):
    attempt: int = 3
    interval: int = 3


# Global
class GlobalConfig(BaseModel):
    concurrency: int = 8
    recursion_limit: int = 25
    memory: Memory = Memory()
    retry: RetryConfig = RetryConfig()


# Model
class ModelConfig(BaseModel):
    api_base: Optional[str]
    api_key: Optional[str]
    kargs: Optional[Dict[str, Any]] = None
    model: Optional[str]
    type: str = "openai"


# Agent
class Prompt(BaseModel):
    role: Optional[str]
    content: str


class SwitchConfig(BaseModel):
    swap_user_assistant: bool = True


class AgentMemoryConfig(BaseModel):
    enable: bool = True
    id: Optional[str] = None
    keep_turns: int = 3
    # when_switch: SwitchConfig = SwitchConfig()


class AgentConfig(BaseModel):
    model: str
    prompt: Final[List[Prompt]]
    memory: AgentMemoryConfig = AgentMemoryConfig(enable=True)

    checkpointer: Optional[Any] = None


# Task
class TaskConfig(BaseModel):
    start_prompt: Final[Optional[Prompt]] = None
    variables: List[Dict[str, str]] = []


# Elmes Context
class ElmesContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    conns: List[Connection] = []


# ExportFormat
class ExportFormat(BaseModel):
    task: Dict[str, str]
    messages: List[Prompt] = []

    @staticmethod
    def from_json_file(file_path: Path | str) -> "ExportFormat":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ExportFormat(**data)

    def message_function(self, function_call: str) -> str:
        if function_call == "as_dialog()":
            strings = []
            for message in self.messages:
                if message.role is None:
                    continue
                strings.append(f"{message.role}: {message.content}")
            return "\n".join(strings)
        else:
            raise ValueError(f"Unsupported function call: {function_call}")

    def replace_template(self, template: str) -> str:
        """
        将输入的模板字符串中的占位符替换为实际值
        目前支持的占位符有：
        task.xxxx 代表task的某个字段
        messages.as_dialog() 代表对话形式的messages

        messages.as_dialog() 形式如下：
        teacher: xxxxxxx
        student: xxxxxxx
        """
        # 获取占位符，所有占位符都由{}包裹
        placeholders = re.findall(r"\{.+?\}", template)
        for placeholder in placeholders:
            # 获取占位符的名称，即{}中的内容
            placeholder_name = placeholder.strip("{}")
            # 获取占位符对应的值，根据占位符的名称从task或messages中获取
            if placeholder_name.startswith("task."):
                field_name = placeholder_name.split(".")[1]
                value = self.task[field_name]
            elif placeholder_name.startswith("messages."):
                message_name = placeholder_name.split(".")[1]
                # 如果是函数调用形式
                if "(" in message_name:
                    value = self.message_function(message_name)
                else:
                    raise Exception(f"Invalid message name: {message_name}")
            else:
                raise Exception(f"Invalid placeholder name: {placeholder_name}")
            # 将占位符替换为对应的值
            template = template.replace(placeholder, str(value))
        return template


# FormatField
class FormatField(BaseModel):
    field: str
    type: Literal["str", "int", "float", "bool", "dict"]
    description: str
    items: List["FormatField"] = []


# Evaluation
class EvalConfig(BaseModel):
    model: str
    name: Optional[str]
    prompt: List[Prompt]
    format: List[FormatField]
    format_mode: Literal["tool", "prompt"] = "tool"

    def format_to_json_schema(self) -> str:
        model = self.format_to_pydantic()
        json_schema = model.model_json_schema()
        return json.dumps(json_schema, ensure_ascii=False)

    def format_to_json_example(self) -> str:
        mmodel: type[BaseModel] = self.format_to_pydantic()

        class MMF(ModelFactory):
            __model__ = mmodel

        return MMF().build().json()

    def get_prompts(self) -> Tuple[str, List[Prompt]]:
        """获取系统提示和其他提示词"""
        system_prompt = ""
        other_prompt: List[Prompt] = []
        for p in self.prompt:
            if p.role == "system":
                if system_prompt != "":
                    raise ValueError("存在多个系统提示")
                system_prompt = p.content
            else:
                other_prompt.append(p)
        return system_prompt, other_prompt

    def format_to_pydantic(self) -> type[BaseModel]:
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
        ) -> type[BaseModel]:
            annotations = {}
            for f in fields:
                annotations[f.field] = field_type_from_format(f)
            return create_model(model_name, **annotations)

        return build_model_from_format(self.format, "GeneratedModel")


# Elmes
class ElmesConfig(BaseModel):
    globals: GlobalConfig
    models: Dict[str, ModelConfig]
    agents: Dict[str, AgentConfig]
    directions: List[str]
    tasks: TaskConfig
    evaluation: Optional[EvalConfig] = None

    context: ElmesContext = ElmesContext(conns=[])
