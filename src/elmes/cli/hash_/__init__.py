"""Hash command for ELMES CLI."""

import hashlib
from pathlib import Path

import click


@click.command(
    "hash",
    help="Print the MD5 hash of a config file (used as result subdirectory name)",
)
@click.option(
    "--config",
    default="config.yaml",
    help="Path to the configuration file.",
    show_default=True,
)
def hash_(config: str):
    """Print the MD5 hash of the config file."""
    path = Path(config)
    if not path.exists():
        raise click.ClickException(f"Config file not found: {path}")

    content_md5 = hashlib.md5(path.read_bytes()).hexdigest()
    click.echo(content_md5)
