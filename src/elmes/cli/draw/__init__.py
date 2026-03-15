"""Draw command for ELMES CLI - Visualize agent workflow."""

import click


def _generate_mermaid(config_obj, direction: str) -> str:
    """Generate mermaid flowchart code from directions config.

    Agent nodes: rounded rectangle  (name)
    Router nodes: diamond           {name}
    START/END:    circle            ([name])
    """
    import re

    def parse_direction(d):
        from_node = d.from_
        to_node = d.to_
        if not to_node.startswith("router:"):
            return from_node, to_node, None
        router_str = to_node[7:]
        m = re.match(r"(\w+)\((.+)\)", router_str)
        if not m:
            return from_node, to_node, None
        router_name = m.group(1)
        args_str = m.group(2)
        cfg: dict = {"router_name": router_name}
        for regex, vtype in [
            (r"(\w+)\s*=\s*\[(.*?)\]", "list"),
            (r'(\w+)\s*=\s*"([^"]*)"', "str"),
            (r"(\w+)\s*=\s*'([^']*)'", "str"),
            (r"(\w+)\s*=\s*(\w+)", "raw"),
        ]:
            for key, value in re.findall(regex, args_str):
                if key not in cfg:
                    if vtype == "list":
                        cfg[key] = re.findall(r'["\']([^"\']+)["\']', value)
                    else:
                        cfg[key] = value
        return from_node, router_name, cfg

    # Collect node types
    agent_nodes: set[str] = set()
    router_nodes: set[str] = set()
    for d in config_obj.directions:
        from_node, to_node, router_config = parse_direction(d)
        if from_node not in ("START", "END"):
            agent_nodes.add(from_node)
        if router_config:
            router_nodes.add(router_config["router_name"])
        elif to_node not in ("START", "END") and not router_config:
            agent_nodes.add(to_node)

    # Remove routers from agents set
    agent_nodes -= router_nodes

    lines: list[str] = []
    lines.append("---")
    lines.append("title: elmes workflow")
    lines.append("---")
    lines.append(f"flowchart {direction}")

    # Node shape declarations
    lines.append("  START([START])")
    lines.append("  END([END])")
    for name in agent_nodes:
        lines.append(f"  {name}({name})")
    for name in router_nodes:
        lines.append(f"  {name}({name})")

    # Edges
    for d in config_obj.directions:
        from_node, to_node, router_config = parse_direction(d)

        if router_config:
            router_name = router_config["router_name"]
            keywords = router_config.get("keywords", [])
            exists_to = router_config.get("exists_to", "END")
            else_to = router_config.get("else_to", "")
            kw_label = ", ".join(keywords)

            lines.append(f"  {from_node} --> {router_name}")
            lines.append(f"  {router_name} -.-> {exists_to}")
            if else_to:
                lines.append(f"  {router_name} -.-> {else_to}")
        else:
            lines.append(f"  {from_node} --> {to_node}")

    # Styles
    lines.append("")
    lines.append("  classDef agent fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f")
    lines.append(
        "  classDef router fill:#fef9c3,stroke:#f59e0b,stroke-dasharray:5 5,color:#78350f"
    )
    lines.append("  classDef terminal fill:#f3f4f6,stroke:#6b7280,color:#374151")
    if agent_nodes:
        lines.append(f"  class {','.join(sorted(agent_nodes))} agent")
    if router_nodes:
        lines.append(f"  class {','.join(sorted(router_nodes))} router")
    lines.append("  class START,END terminal")

    return "\n".join(lines)


@click.command(help="Draw agent workflow diagram")
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
    help="Diagram direction.",
)
@click.option("--debug", is_flag=True, help="Enable debug mode.")
def draw(
    config: str, output: str | None, print_code: bool, direction: str, debug: bool
):
    """Draw agent workflow diagram."""
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    from pathlib import Path
    from elmes.config import load_config

    config_path = Path(config)
    config_obj = load_config(str(config_path))

    code = _generate_mermaid(config_obj, direction)

    if print_code:
        click.echo(code)

    output_path = Path(output) if output else config_path.with_suffix(".png")

    if output_path.suffix == ".mmd":
        output_path.write_text(code, encoding="utf-8")
        click.echo(f"Mermaid code saved to: {output_path}")
        return

    # Save PNG via mermaid.ink
    try:
        import httpx
        import base64

        encoded = base64.urlsafe_b64encode(code.encode()).decode()
        url = f"https://mermaid.ink/img/{encoded}?type=png"
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        click.echo(f"Diagram saved to: {output_path}")
    except Exception as e:
        fallback = output_path.with_suffix(".mmd")
        fallback.write_text(code, encoding="utf-8")
        click.echo(
            f"Image generation failed ({e}), mermaid code saved to: {fallback}",
            err=True,
        )
