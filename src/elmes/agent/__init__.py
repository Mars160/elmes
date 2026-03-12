from diskcache import Cache
from dataclasses import dataclass
from typing import Generator, Any

from elmes.client.interface import ClientInterface
from elmes.graph.node import GraphNodeInterface
from elmes.entity.message import Message
from elmes.entity.agent import AgentConfig
from elmes.entity.globals import MemoryConfig

import logging


@dataclass
class MemoryEntry:
    query: str
    query_from: str
    output: str
    reasoning: str | None = None


class Agent(GraphNodeInterface):
    def __init__(
        self,
        name: str,
        agent_id: str,
        agent_config: AgentConfig,
        memory_config: MemoryConfig,
        client: ClientInterface,
    ):
        self.name = name
        self.agent_id = agent_id

        self.agent_config = agent_config
        self.client = client
        self.logger = logging.getLogger(f"{self.agent_id}_{self.name}_agent")

        self.cache = Cache(f"{memory_config.path}/{self.agent_id}")

    async def generate(self, query: str, query_from: str) -> str | None:
        if self.agent_config.memory.enable:
            # 从cache中提取最后的对话历史
            messages: list[Message] = []
            for k in self.cache.iterkeys(reverse=True):
                memory_entry: MemoryEntry = self.cache[k]  # type: ignore
                messages.insert(
                    0, Message(role="assistant", content=memory_entry.output)
                )
                messages.insert(
                    0,
                    Message(
                        role="user",
                        content=f"{memory_entry.query_from}: {memory_entry.query}",
                    ),
                )
                if len(messages) == self.agent_config.memory.keep_turns * 2:
                    break
        else:
            messages = []
        messages.append(Message(role="user", content=query))

        messages = self.agent_config.prompt + messages
        response = await self.client.generate(messages)
        if response is not None:
            if "</think>" in response:
                splits = response.split("</think>")
                reasoning = splits[0]
                response = splits[1]
            else:
                reasoning = None
            self.cache.push(
                MemoryEntry(
                    query=query,
                    query_from=query_from,
                    output=response,
                    reasoning=reasoning,
                )
            )
        return response

    def iter_history(self) -> Generator[Message, Any, None]:
        """迭代器，按时间顺序返回对话历史"""
        for k in self.cache.iterkeys():
            memory_entry: MemoryEntry = self.cache[k]  # type: ignore
            yield Message(
                role=self.name,
                content=memory_entry.output,
                reasoning=memory_entry.reasoning,
            )

    async def run(self, *args, **kwargs) -> str | None:
        """
        参数:
           query: str, 用户输入
           query_from: str, 输入来源的标识，比如另一个agent的名字
        返回:
            response: str, 生成的回复
        """

        return await self.generate(*args, **kwargs)
