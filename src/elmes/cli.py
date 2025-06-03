import click

from pathlib import Path


@click.command("generate")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
def generate(config: str):
    from elmes.config import load_conf
    from elmes.run import run

    import asyncio

    path = Path(config)
    load_conf(path)

    asyncio.run(run())


@click.command()
@click.option("--input-dir", default="input", help="Directory containing input")
@click.option("--output-dir", default="output", help="Directory to save output")
def result(input_dir: str, output_dir: str):
    input = Path(input_dir)
    output = Path(output_dir)
    if not input.exists():
        raise ValueError(f"Input directory {input} Not Exists!")
    output.mkdir(parents=True, exist_ok=True)
    raise NotImplementedError("Not Implemented Yet!")


@click.group()
def main():
    pass


main.add_command(generate)
main.add_command(result)
