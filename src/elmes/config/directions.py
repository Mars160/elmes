from pydantic import BaseModel, Field


class Direction(BaseModel):
    from_: str = Field(..., description="信息的发送方node名称")
    to_: str = Field(..., description="信息的接收方node名称")
