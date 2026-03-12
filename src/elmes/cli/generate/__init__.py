from elmes.config import ElmesConfig
from elmes.agent import Agent
from elmes.graph import Graph
from elmes.client import Client

from tqdm.asyncio import tqdm

import click
import asyncio

from pathlib import Path


@click.command("generate", help="Generate conversions for all tasks")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def generate(config: str, debug: bool):
    from elmes.config import load_conf

    path = Path(config)
    config_obj = load_conf(path)
    generate_logic(config_obj, debug)


def generate_logic(config: ElmesConfig, debug: bool):
    clients = {}
    for model_name, model_config in config.models.items():
        clients[model_name] = Client.from_model_config(
            model_config, config.globals.retry
        )

    agents = {}
    for agent_name, agent_config in config.agents.items():
        model_name = agent_config.model
        if model_name not in clients:
            raise ValueError(f"Model {model_name} not found for agent {agent_name}")
        client = clients[model_name]
        agents[agent_name] = Agent(
            name=agent_name,
            agent_config=agent_config,
            memory_config=config.globals.memory,
            client=client,
        )

    graph, router_node_map = Graph.from_direction_config(config.directions)
    graphs = []
    # 根据task数量复制图，并替换节点
    for task_id, task in enumerate(config.tasks.variables):
        cloned_graph = graph.clone()
        graph_agents = {}
        for agent in agents:
            graph_agents[agent] = agents[agent].clone(
                task_variables=task, task_id=task_id
            )
        cloned_graph.replace_node({**graph_agents, **router_node_map})
        graphs.append(cloned_graph)
        # TODO: 实现tasks.start_prompt的替换
