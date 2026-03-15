from pydantic import BaseModel, Field
from elmes.config.models import Model


class Agent(BaseModel):
    name: str = Field(..., description="agent名称")
    model: Model = Field(..., description="agent使用的模型配置")
    system_prompt: str = Field(..., description="agent的系统提示词")
    retries: int = Field(3, description="agent调用模型失败后的重试次数")
    tools: list[str] = Field(default_factory=list, description="agent可调用的工具列表")
