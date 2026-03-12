from pathlib import Path
from pydantic import BaseModel


# Memory
class MemoryConfig(BaseModel):
    path: Path = Path(".")


# RetryConfig
class RetryConfig(BaseModel):
    attempt: int = 3
    interval: int = 3


# Global
class GlobalConfig(BaseModel):
    concurrency: int = 8
    recursion_limit: int = 25
    memory: MemoryConfig = MemoryConfig()
    retry: RetryConfig = RetryConfig()
