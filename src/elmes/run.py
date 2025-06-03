import asyncio

from typing import Dict

from tqdm.asyncio import tqdm

from langgraph.graph.state import CompiledStateGraph

from elmes.agent import init_agent_map
from elmes.config import CONFIG
from elmes.directions import apply_agent_direction
from elmes.entity import Prompt
from elmes.model import init_model_map
from elmes.utils import replace_prompt


async def run(workers_num: int = CONFIG.globals.concurrency):
    sem = asyncio.Semaphore(workers_num)

    model_map = init_model_map()
    agents = []

    for task in CONFIG.tasks.variables:
        agent_map, task = init_agent_map(model_map, task)
        if task is not None:
            start_prompt = replace_prompt(CONFIG.tasks.start_prompt, task)[0]
        else:
            start_prompt = CONFIG.tasks.start_prompt
        agent, _ = await apply_agent_direction(agent_map, task=task)
        agents.append((agent, start_prompt))

    async def arun(agent: CompiledStateGraph, prompt: Prompt | Dict[str, str]):
        if isinstance(prompt, Prompt):
            prompt = prompt.model_dump()
        async with sem:
            await agent.ainvoke(
                prompt,
                {
                    "configurable": {"thread_id": "0"},
                    "recursion_limit": CONFIG.globals.recursion_limit,
                },
                stream_mode="values",
            )

    tasks = []
    for agent, prompt in agents:
        tasks.append(arun(agent, prompt))

    await tqdm.gather(*tasks)

    conns = CONFIG.context.conns
    for conn in conns:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
