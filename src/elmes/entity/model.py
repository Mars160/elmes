from typing import Optional, Dict, Any
from pydantic import BaseModel


# Model
class ModelConfig(BaseModel):
    api_base: Optional[str]
    api_key: Optional[str]
    max_retries: Optional[int] = 3
    kargs: Optional[Dict[str, Any]] = None
    model: str
    name: str
    type: str = "openai"
