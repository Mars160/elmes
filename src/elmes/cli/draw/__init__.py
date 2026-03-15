"""Draw command for ELMES CLI - Visualize agent workflow."""

import click


@click.command(help="Draw agent workflow diagram using pydantic-graph mermaid support")
@click.option(
    "--config",
    default="config.yaml",
    show_default=True,
    help="Path to the configuration file.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path (.png saves image via mermaid.ink, .mmd saves mermaid code). "
    "Defaults to <config_stem>.png.",
)
@click.option(
    "--print",
    "print_code",
    is_flag=True,
    default=False,
    help="Print mermaid code to stdout.",
)
@click.option(
    "--direction",
    type=click.Choice(["TB", "LR", "RL", "BT"]),
    default="LR",
    show_default=True,
    help="Diagram direction (TB=top-bottom, LR=left-right, RL=right-left, BT=bottom-top).",
)
@click.option("--debug", is_flag=True, help="Enable debug mode.")
def draw(
    config: str, output: str | None, print_code: bool, direction: str, debug: bool
):
    """Draw agent workflow diagram using pydantic-graph's mermaid support."""
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    from pathlib import Path
    from elmes.config import load_config
    from elmes.model import build_model
    from elmes.agent import build_agent
    from elmes.mcp import build_mcp
    from elmes.graph import build_graph, ensure_routers_registered

    config_path = Path(config)
    config_obj = load_config(str(config_path))
    ensure_routers_registered()

    model_dict = {n: build_model(m) for n, m in config_obj.models.items()}
    mcp_dict = {n: build_mcp(m) for n, m in config_obj.mcps.items()}

    task_variables = config_obj.tasks.content[0] if config_obj.tasks.content else {}
    agents = {
        n: build_agent(a, model_dict, task_variables, mcp_dict)
        for n, a in config_obj.agents.items()
    }

    graph, start_node = build_graph(
        config_obj.directions, agents, config_obj.globals.recursion_limit
    )

    code = graph.mermaid_code(start_node=start_node, direction=direction)

    if print_code:
        click.echo(code)

    output_path = Path(output) if output else config_path.with_suffix(".png")

    if output_path.suffix == ".mmd":
        output_path.write_text(code, encoding="utf-8")
        click.echo(f"Mermaid code saved to: {output_path}")
    else:
        try:
            image_bytes = graph.mermaid_image(
                start_node=start_node, direction=direction
            )
            output_path.write_bytes(image_bytes)
            click.echo(f"Diagram saved to: {output_path}")
        except Exception as e:
            # Fallback to mermaid code if image generation fails
            fallback = output_path.with_suffix(".mmd")
            fallback.write_text(code, encoding="utf-8")
            click.echo(
                f"Mermaid code saved to: {fallback} (image generation failed: {e})",
                err=True,
            )
