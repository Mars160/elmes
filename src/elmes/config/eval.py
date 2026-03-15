from pydantic import BaseModel, Field
from elmes.config.models import Model


class Eval(BaseModel):
    name: str = Field(..., description="任务名称")
    fields: list["EvalField"] = Field(..., description="要评价的字段")
    judge_model: Model = Field(..., description="评判模型配置")
    target: str = Field(..., description="被评估的对象名")


class EvalField(BaseModel):
    name: str = Field(..., description="字段名称")
    rubric: str = Field(..., description="评分细则")
    reason: bool = Field(False, description="是否需要评分理由")
