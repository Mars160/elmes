from typing import Optional, Dict, Any
from pydantic import BaseModel


# Model
class ModelConfig(BaseModel):
    api_base: Optional[str]
    api_key: Optional[str]
    kargs: Optional[Dict[str, Any]] = None
    model: Optional[str]
    name: str
    type: str = "openai"
