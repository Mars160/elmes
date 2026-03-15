"""Export JSON command for ELMES CLI."""

import asyncio
import json as jsonmodule
from pathlib import Path

import click
from tqdm.asyncio import tqdm


@click.command(help="Export generated conversations to JSON format")
@click.option("--config", default="config.yaml", help="Path to the configuration file")
@click.option(
    "--input",
    "input_dir",
    default=None,
    help="Directory containing intermediate task_N.json files (defaults to globals.output_dir in config).",
)
@click.option(
    "--output",
    "output_dir",
    default=None,
    help="Output directory (defaults to --input directory).",
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def json(config: str, input_dir: str | None, output_dir: str | None, debug: bool):
    """Export generated conversations to JSON format."""
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    from elmes.config import load_config
    from elmes.cli.generate import _build_run_dir

    config_path = Path(config)
    config_obj = load_config(config)
    input_path = (
        Path(input_dir)
        if input_dir
        else _build_run_dir(config_path, Path(config_obj.globals.output_dir))
    )
    output_path = Path(output_dir) if output_dir else input_path

    task_files = sorted(
        f
        for f in input_path.glob("task_*.json")
        if f.stem.removeprefix("task_").isdigit()
    )
    if not task_files:
        click.echo(f"No task_*.json files found in {input_path}", err=True)
        return

    from elmes.cli.export.exporter.json_ import aexport_json

    tasks = [aexport_json(f) for f in task_files]
    results = asyncio.run(tqdm.gather(*tasks, desc="Exporting to JSON"))

    output_path.mkdir(parents=True, exist_ok=True)
    for input_file, obj in results:
        output_file = output_path / f"{input_file.stem}_export.json"
        with open(output_file, "w", encoding="utf-8") as f:
            jsonmodule.dump(obj, f, ensure_ascii=False, indent=2)
        click.echo(f"Exported: {output_file}")
