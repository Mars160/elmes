import json as jsonmodule
import asyncio
from tqdm.asyncio import tqdm

import click

from pathlib import Path

from langchain.globals import set_debug


def export_json_logic():
    from elmes.config import CONFIG

    input = CONFIG.globals.memory.path
    output = input

    dbfiles = []
    files = input.iterdir()
    for file in files:
        if file.suffix == ".db":
            dbfiles.append(file.absolute())

    from elmes.cli.export.exporter.json_ import aexport_json

    tasks = []
    for dbfile in dbfiles:
        task = aexport_json(dbfile)
        tasks.append(task)

    result = asyncio.run(tqdm.gather(*tasks))
    for input_path, obj in result:
        output_path = output / f"{input_path.stem}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            jsonmodule.dump(obj, f, ensure_ascii=False, indent=4)


@click.command(help="Export chat databases to JSON format")
@click.option(
    "--config", default="config.yaml", help="Directory containing chat databases"
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def json(config: str, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)
    export_json_logic()
