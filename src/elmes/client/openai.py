from typing import Type, Optional, Dict, Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from elmes.client import Client
from elmes.entity import ModelConfig
from elmes.entity.globals import RetryConfig
from elmes.entity.message import (
    InputMessage,
    GeneratedMessage,
    ToolCall,
    ToolCallContent,
    StructuredGeneratedMessage,
)


class OpenAIClient(Client):
    def __init__(self, model_config: ModelConfig, retry_config: RetryConfig):
        super().__init__(model_config, retry_config)
        self.client = AsyncOpenAI(
            api_key=model_config.api_key,
            base_url=model_config.api_base,
        )

    async def _generate(self, messages: list[InputMessage]) -> GeneratedMessage:
        openai_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        kargs: Optional[Dict[str, Any]] = self.model_config.kargs
        if kargs is None:
            kargs = {}

        response: ChatCompletion = await self.client.chat.completions.create(
            model=self.model_config.model,  # pyright: ignore[reportArgumentType]
            messages=openai_messages,  # pyright: ignore[reportArgumentType]
            **kargs,
        )  # type: ignore

        assert response.choices and len(response.choices) > 0, (
            "No choices returned from OpenAI"
        )

        if (
            response.choices[0].message.tool_calls is not None
            and len(response.choices[0].message.tool_calls) > 0
        ):
            tool_calls = []
            for tool_call in response.choices[0].message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        function=ToolCallContent(
                            name=tool_call.function.name,  # pyright: ignore[reportAttributeAccessIssue]
                            arguments=tool_call.function.arguments,  # pyright: ignore[reportAttributeAccessIssue]
                        ),
                    )
                )
        else:
            tool_calls = None

        return GeneratedMessage(
            role="assistant",
            content=response.choices[0].message.content,
            tool_calls=tool_calls,
        )

    async def _generate_structured(
        self, messages: list[InputMessage], response_model: Type[BaseModel]
    ) -> StructuredGeneratedMessage:
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
        return StructuredGeneratedMessage(role="assistant", content=parsed)
