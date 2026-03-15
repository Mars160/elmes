from pydantic import BaseModel, Field


class Globals(BaseModel):
    concurrency: int = Field(default=16, description="全局并发数")
    model_call_limit: int = Field(default=5, description="模型调用次数限制")
