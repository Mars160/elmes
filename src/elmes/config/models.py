from pydantic import BaseModel, Field


class Model(BaseModel):
    name: str = Field(..., description="模型名称")
    type: str = Field(..., description="模型类型，如openai等")
    api_key: str = Field(..., description="模型API密钥")
    base_url: str = Field(..., description="模型API基础URL")
    max_retries: int = Field(3, description="模型调用最大重试次数")
    kargs: dict = Field(default_factory=dict, description="其他模型参数")
    model: str = Field(..., description="模型名称，如gpt-4o-mini等")
