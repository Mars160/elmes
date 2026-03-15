from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models import Model as PydanticAIModel
from pydantic_ai.settings import ModelSettings
from openai import AsyncOpenAI

from elmes.config import Model


def build_model(model_config: Model) -> PydanticAIModel:
    """根据ModelConfig和RetryConfig构建OpenAIChatModel实例"""
    if model_config.type == "openai":
        client = AsyncOpenAI(
            api_key=model_config.api_key,
            base_url=model_config.base_url,
            max_retries=model_config.max_retries or 3,
        )
        provider = OpenAIProvider(openai_client=client)
        model = OpenAIChatModel(
            model_name=model_config.model,
            provider=provider,
            settings=ModelSettings(**(model_config.kargs or {})),
        )

        return model
    else:
        raise ValueError(f"Unsupported model type: {model_config.type}")
