from abc import ABC, abstractmethod
from elmes.entity import ModelConfig, RetryConfig
from elmes.entity.message import Message
from pydantic import BaseModel
from typing import Type
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

import logging


class ClientInterface(ABC):
    def __init__(
        self, model_config: ModelConfig, model_name: str, retry_config: RetryConfig
    ):
        self.model_config = model_config
        self.model_name = model_name
        self.retry_config = retry_config
        self.logger = logging.getLogger(self.model_name + "-client")
        self.model = model_config.model

    @abstractmethod
    async def _generate(self, messages: list[Message]) -> str:
        pass

    @abstractmethod
    async def _generate_structured(
        self, messages: list[Message], response_model: Type[BaseModel]
    ) -> BaseModel:
        pass

    async def generate(self, messages: list[Message]) -> str | None:
        """封装了重试逻辑的公开接口"""
        # 使用 AsyncRetrying 动态读取 self 中的配置
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.retry_config.attempt),
            wait=wait_fixed(self.retry_config.interval),
            # 可以根据需要添加 reraise=True 以抛出最终的异常
            reraise=True,
        ):
            with attempt:
                return await self._generate(messages)
            self.logger.warning(
                f"Attempt {attempt.retry_state.attempt_number} failed. Retrying..."
            )

    async def generate_structured(
        self, messages: list[Message], response_model: Type[BaseModel]
    ) -> BaseModel | None:
        """结构化生成的重试封装"""
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.retry_config.attempt),
            wait=wait_fixed(self.retry_config.interval),
            reraise=True,
        ):
            with attempt:
                return await self._generate_structured(messages, response_model)
            self.logger.warning(
                f"Attempt {attempt.retry_state.attempt_number} failed. Retrying..."
            )
