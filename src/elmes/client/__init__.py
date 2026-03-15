from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Type
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from diskcache import Cache
from hashlib import md5
from json import dumps

from elmes.entity.model import ModelConfig
from elmes.entity.globals import RetryConfig
from elmes.entity.message import (
    InputMessage,
    StructuredGeneratedMessage,
    GeneratedMessage,
)

import logging


class Client(ABC):
    def __init__(self, model_config: ModelConfig, retry_config: RetryConfig):
        self.model_config = model_config
        self.model_name = model_config.name
        self.retry_config = retry_config
        self.logger = logging.getLogger(self.model_config.name + "-client")

        kargs_str = (
            dumps(model_config.kargs, sort_keys=True) if model_config.kargs else ""
        )
        cache_key = f"{kargs_str}"
        self.cache_key = md5(cache_key.encode()).hexdigest()

        self.cache = Cache(f".elmes-cache/client/{self.model_config.model}")

    @staticmethod
    def from_model_config(
        model_config: ModelConfig, retry_config: RetryConfig
    ) -> "Client":
        """根据ModelConfig中的model字段动态选择Client实现"""
        if model_config.type == "openai":
            from elmes.client.openai import OpenAIClient

            return OpenAIClient(model_config, retry_config)
        else:
            raise ValueError(f"Unsupported model: {model_config.model}")

    @abstractmethod
    async def _generate(self, messages: list[InputMessage]) -> GeneratedMessage:
        pass

    @abstractmethod
    async def _generate_structured(
        self, messages: list[InputMessage], response_model: Type[BaseModel]
    ) -> StructuredGeneratedMessage:
        pass

    async def generate(self, messages: list[InputMessage]) -> GeneratedMessage:
        """封装了重试逻辑的公开接口"""
        messages_str = dumps([{"role": m.role, "content": m.content} for m in messages])
        cache_key = f"{self.cache_key}_{md5(messages_str.encode()).hexdigest()}"
        if cache_key in self.cache:
            self.logger.warning("Cache hit for messages. Returning cached response.")
            return self.cache[cache_key]  # type: ignore
        # 使用 AsyncRetrying 动态读取 self 中的配置
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.retry_config.attempt),
            wait=wait_fixed(self.retry_config.interval),
            # 可以根据需要添加 reraise=True 以抛出最终的异常
            reraise=True,
        ):
            with attempt:
                response = await self._generate(messages)
                self.cache[cache_key] = response  # type: ignore
                return response
            self.logger.warning(
                f"Attempt {attempt.retry_state.attempt_number} failed. Retrying..."
            )
        raise RuntimeError("Failed to generate response after retries.")

    async def generate_structured(
        self, messages: list[InputMessage], response_model: Type[BaseModel]
    ) -> StructuredGeneratedMessage:
        """结构化生成的重试封装"""
        messages_str = dumps([{"role": m.role, "content": m.content} for m in messages])
        cache_key = f"struct_{self.cache_key}_{md5(messages_str.encode()).hexdigest()}"
        if cache_key in self.cache:
            self.logger.warning("Cache hit for messages. Returning cached response.")
            return self.cache[cache_key]  # type: ignore
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.retry_config.attempt),
            wait=wait_fixed(self.retry_config.interval),
            reraise=True,
        ):
            with attempt:
                response = await self._generate_structured(messages, response_model)
                self.cache[cache_key] = response  # type: ignore
                return response
            self.logger.warning(
                f"Attempt {attempt.retry_state.attempt_number} failed. Retrying..."
            )
        raise RuntimeError("Failed to generate structured response after retries.")
