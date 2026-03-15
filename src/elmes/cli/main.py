import click

from elmes.cli.generate import generate
from elmes.cli.eval import eval
from elmes.cli.visualize import visualize
from elmes.cli.draw import draw
from elmes.cli.export import export
from elmes.cli.hash_ import hash_


@click.group()
def main():
    """ELMES CLI - Education Language Model Evaluation System"""
    pass


main.add_command(generate)
main.add_command(eval)
main.add_command(export)
main.add_command(visualize)
main.add_command(draw)
main.add_command(hash_)
