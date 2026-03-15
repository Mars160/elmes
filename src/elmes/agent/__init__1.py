from diskcache import Cache
from dataclasses import dataclass
from typing import Generator, Any
from copy import deepcopy

from elmes.client import Client
from elmes.graph.node import GraphNodeInterface
from elmes.entity.message import InputMessage, InputMessageContent
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
        agent_config: AgentConfig,
        memory_config: MemoryConfig,
        client: Client,
    ):
        self.name = name

        self.agent_config = agent_config
        self.memory_config = memory_config
        self.client = client

        self.prompt_replaced = False
        self.prompt = deepcopy(agent_config.prompt)

    def clone(self, task_variables: dict[str, str], task_id: int) -> "Agent":
        """根据task_variables克隆一个新的Agent实例，并替换prompt中的占位符"""
        agent = Agent(
            name=self.name,
            agent_config=self.agent_config,
            memory_config=self.memory_config,
            client=self.client,
        )
        agent.__setattr__("logger", logging.getLogger(f"{self.name}_{task_id}_agent"))
        agent.__setattr__("cache", Cache(f"{self.memory_config.path}/{task_id}"))
        for message in agent.prompt:
            if message.content is not None:
                for var_name, var_value in task_variables.items():
                    placeholder = f"{{{var_name}}}"
                    message.content = message.content.replace(placeholder, var_value)
        agent.prompt_replaced = True
        return agent

    async def generate(self, query: str, query_from: str) -> str | None:
        assert self.prompt_replaced, (
            "Prompt has placeholders that have not been replaced. Call apply_prompt() first."
        )
        if self.agent_config.memory.enable:
            # 从cache中提取最后的对话历史
            messages: list[InputMessage] = []
            for k in self.cache.iterkeys(reverse=True):  # pyright: ignore[reportAttributeAccessIssue]
                memory_entry: MemoryEntry = self.cache[k]  # type: ignore
                messages.insert(
                    0,
                    InputMessage(
                        role="assistant",
                        content=InputMessageContent(
                            type="text", text=memory_entry.output
                        ),
                    ),
                )
                messages.insert(
                    0,
                    InputMessage(
                        role="user",
                        content=InputMessageContent(
                            type="text",
                            text=f"{memory_entry.query_from}: {memory_entry.query}",
                        ),
                    ),
                )
                if len(messages) == self.agent_config.memory.keep_turns * 2:
                    break
        else:
            messages = []
        messages.append(
            InputMessage(
                role="user", content=InputMessageContent(type="text", text=query)
            )
        )

        messages = self.prompt + messages
        response = await self.client.generate(messages)
        if response is not None:
            if "</think>" in response:
                splits = response.split("</think>")
                reasoning = splits[0]
                response = splits[1]
            else:
                reasoning = None
            self.cache.push(  # pyright: ignore[reportAttributeAccessIssue]
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
        for k in self.cache.iterkeys():  # pyright: ignore[reportAttributeAccessIssue]
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
