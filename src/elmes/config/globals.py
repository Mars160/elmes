from pydantic import BaseModel, Field


class Globals(BaseModel):
    concurrency: int = Field(default=16, description="全局并发数")
    recursion_limit: int = Field(default=50, description="图递归深度限制")
    output_dir: str = Field(default="./generated", description="generate结果保存路径")
