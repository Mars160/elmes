import click
from langchain.globals import set_debug


@click.command(help="Draw Agent workflow.")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to the configuration file"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def draw(config, debug=False):
    set_debug(debug)
    from elmes.config import load_conf
    from pathlib import Path

    config = Path(config)
    load_conf(config)

    from elmes.config import CONFIG
    from elmes.model import init_model_map
    from elmes.agent import init_agent_map
    from elmes.directions import apply_agent_direction

    # from langchain_core.runnables.graph import CurveStyle, NodeStyles, MermaidDrawMethod

    import asyncio

    models = init_model_map()
    task = CONFIG.tasks.variables[0]
    agents, _ = init_agent_map(models, task)
    agent, _ = asyncio.run(apply_agent_direction(agents, task=task))
    png = agent.get_graph().draw_mermaid_png()
    with open(f"{config.stem}.png", "wb") as wb:
        wb.write(png)
    # print(png)
