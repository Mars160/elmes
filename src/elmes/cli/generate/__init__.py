import click

from pathlib import Path
from langchain.globals import set_debug

# set_debug(True)


@click.command("generate", help="Generate conversions for all tasks")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def generate(config: str, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)
    generate_logic()


def generate_logic():
    from elmes.run import run
    import asyncio

    asyncio.run(run())
