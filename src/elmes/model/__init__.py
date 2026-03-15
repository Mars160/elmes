from elmes.entity.model import ModelConfig
from elmes.entity.globals import RetryConfig

from pydantic_ai.models import Model


def build_model(model_config: ModelConfig, retry_config: RetryConfig) -> Model:
    """根据ModelConfig和RetryConfig构建模型实例"""
    if model_config.type == "openai":
        from elmes.model.openai import build_model

        return build_model(model_config, retry_config)
    else:
        raise ValueError(f"Unsupported model type: {model_config.type}")
