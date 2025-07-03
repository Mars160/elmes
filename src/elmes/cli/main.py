import click
from langchain.globals import set_debug

from elmes.cli.generate import generate, generate_logic
from elmes.cli.eval import eval, eval_logic
from elmes.cli.visualize import visualize
from elmes.cli.draw import draw
from elmes.cli.export import export
from elmes.cli.export.json_ import export_json_logic


@click.command(
    help="Run the pipeline to generate, export JSON files, and evaluate the results."
)
@click.option(
    "--config", type=click.Path(exists=True), help="Path to the configuration file"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def pipeline(config, debug=False):
    set_debug(debug)
    from elmes.config import load_conf

    load_conf(config)
    generate_logic()
    export_json_logic()
    eval_logic(avg=True)


@click.group()
def main():
    pass


main.add_command(generate)
main.add_command(export)
main.add_command(eval)
main.add_command(pipeline)

main.add_command(visualize)

main.add_command(draw)
