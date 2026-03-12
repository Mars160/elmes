from elmes.config import ElmesConfig

import click

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
    from elmes.run import run
    import asyncio

    asyncio.run(run())
