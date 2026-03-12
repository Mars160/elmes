from typing import Type, Optional, Dict, Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from elmes.client import Client
from elmes.entity import ModelConfig
from elmes.entity.globals import RetryConfig
from elmes.entity.message import Message


class OpenAIClient(Client):
    def __init__(self, model_config: ModelConfig, retry_config: RetryConfig):
        super().__init__(model_config, retry_config)
        self.client = AsyncOpenAI(
            api_key=model_config.api_key,
            base_url=model_config.api_base,
        )

    async def _generate(self, messages: list[Message]) -> str:
        openai_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        kargs: Optional[Dict[str, Any]] = self.model_config.kargs
        if kargs is None:
            kargs = {}

        response = await self.client.chat.completions.create(
            model=self.model_config.model,  # pyright: ignore[reportArgumentType]
            messages=openai_messages,  # pyright: ignore[reportArgumentType]
            **kargs,
        )  # type: ignore

        content = response.choices[0].message.content
        assert content is not None, "Content is None"
        return content

    async def _generate_structured(
        self, messages: list[Message], response_model: Type[BaseModel]
    ) -> BaseModel:
        openai_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        kargs: Optional[Dict[str, Any]] = self.model_config.kargs
        if kargs is None:
            kargs = {}

        response = await self.client.chat.completions.parse(
            model=self.model_config.model,  # pyright: ignore[reportArgumentType]
            messages=openai_messages,  # pyright: ignore[reportArgumentType]
            response_format=response_model,
            **kargs,
        )

        parsed = response.choices[0].message.parsed
        assert parsed is not None, "Parsed response is None"
        return parsed
