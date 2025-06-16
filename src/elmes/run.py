import asyncio

from tkinter import NONE
from typing import Dict, Optional

from tqdm.asyncio import tqdm

from langgraph.graph.state import CompiledStateGraph
from langgraph.errors import GraphRecursionError

from elmes.agent import init_agent_map
from elmes.config import CONFIG
from elmes.directions import apply_agent_direction
from elmes.entity import Prompt
from elmes.model import init_model_map
from elmes.utils import replace_prompt

from tenacity import RetryError


async def run(workers_num: int = CONFIG.globals.concurrency):
    sem = asyncio.Semaphore(workers_num)

    model_map = init_model_map()
    agents = []

    for task in CONFIG.tasks.variables:
        agent_map, task = init_agent_map(model_map, task)
        if CONFIG.tasks.start_prompt is not None:
            if task is not None:
                start_prompt = replace_prompt(CONFIG.tasks.start_prompt, task)
            else:
                start_prompt = CONFIG.tasks.start_prompt
        else:
            start_prompt = NONE
        agent, _ = await apply_agent_direction(agent_map, task=task)
        agents.append((agent, start_prompt))

    async def arun(
        agent: CompiledStateGraph, prompt: Optional[Prompt | Dict[str, str]]
    ):
        if isinstance(prompt, Prompt):
            n_prompt = prompt.model_dump()
        elif prompt is None:
            n_prompt = []
        else:
            n_prompt = prompt
        async with sem:
            try:
                await agent.ainvoke(
                    {"messages": n_prompt},
                    {
                        "configurable": {"thread_id": "0"},
                        "recursion_limit": CONFIG.globals.recursion_limit,
                    },
                    stream_mode="values",
                )
            except GraphRecursionError:
                print(
                    f"Recursion limit {CONFIG.globals.recursion_limit} reached for one task"
                )
                return
            except RetryError as e:
                exception = e.last_attempt.exception()
                if exception is not None:
                    raise exception
                else:
                    raise ValueError("Retry error occurred without exception")

    tasks = []
    for agent, prompt in agents:
        tasks.append(arun(agent, prompt))

    await tqdm.gather(*tasks)

    conns = CONFIG.context.conns
    for conn in conns:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
