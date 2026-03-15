"""Generate command for ELMES CLI."""

import asyncio
import hashlib
import json
from pathlib import Path

import click
from pydantic_ai.messages import ModelMessagesTypeAdapter
from tqdm.asyncio import tqdm

from elmes.graph.state import GraphState


def _build_run_dir(config_path: Path, output_dir: Path) -> Path:
    """Build a subdirectory name based on MD5 of the config file content."""
    content_md5 = hashlib.md5(config_path.read_bytes()).hexdigest()
    return output_dir / content_md5


@click.command("generate", help="Generate conversations for all tasks")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.option(
    "--output",
    default=None,
    help="Directory to save intermediate results (defaults to globals.output_dir in config).",
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def generate(config: str, output: str | None, debug: bool):
    """Generate conversations for all tasks."""
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    from elmes.config import load_config

    path = Path(config)
    config_obj = load_config(str(path))
    output_dir = Path(output) if output else Path(config_obj.globals.output_dir)
    run_dir = _build_run_dir(path, output_dir)
    asyncio.run(generate_logic(config_obj, run_dir))


async def generate_logic(config, output_dir: Path):
    """Generate conversations based on configuration."""
    from elmes.model import build_model
    from elmes.graph import ensure_routers_registered

    # Ensure routers are registered (including custom routers)
    ensure_routers_registered()

    # Build models (shared across tasks, stateless)
    model_dict = {}
    for model_name, model_config in config.models.items():
        model_dict[model_name] = build_model(model_config)

    # Create tasks (each builds its own MCP + agents + graph independently)
    tasks = [
        run_single_task(task_idx, task_variables, config, model_dict)
        for task_idx, task_variables in enumerate(config.tasks.content)
    ]

    # Run all tasks concurrently
    results = await tqdm.gather(*tasks, desc="Generating conversations")

    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0
    for result in results:
        if "error" in result:
            click.echo(f"Task {result['task_idx']} failed: {result['error']}", err=True)
        else:
            _save_result(result, output_dir)
            success_count += 1

    click.echo(
        f"Generated {success_count}/{len(results)} conversations successfully, "
        f"saved to {output_dir}"
    )


def _save_result(result: dict, output_dir: Path) -> None:
    """Save a single task result to a JSON file."""
    task_idx = result["task_idx"]

    # Serialize messages using pydantic_ai's TypeAdapter (preserves full structure)
    serialized_messages = {}
    for agent_name, messages in result["messages"].items():
        serialized_messages[agent_name] = json.loads(
            ModelMessagesTypeAdapter.dump_json(messages)
        )

    state_obj = {
        "task_idx": task_idx,
        "task_variables": result["task_variables"],
        "node_trace": result["node_trace"],
        "messages": serialized_messages,
    }

    output_file = output_dir / f"task_{task_idx}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(state_obj, f, ensure_ascii=False, indent=2)


async def run_single_task(
    task_idx: int,
    task_variables: dict,
    config,
    model_dict: dict,
):
    """Run a single task to completion."""
    from elmes.agent import build_agent
    from elmes.mcp import build_mcp
    from elmes.graph import build_graph

    # Build MCPs independently per task to avoid concurrent cancel scope conflicts
    mcp_dict = {}
    for mcp_name, mcp_config in config.mcps.items():
        mcp_dict[mcp_name] = build_mcp(mcp_config)

    # Build agents for this task
    agents = {}
    for agent_name, agent_config in config.agents.items():
        agents[agent_name] = build_agent(
            agent_config, model_dict, task_variables, mcp_dict
        )

    # Build graph with agents bound
    graph, start_node = build_graph(
        config.directions,
        agents,
        config.globals.recursion_limit,
    )

    # Initialize state with start prompt
    state = GraphState()
    state.query = config.tasks.start_prompt.format(**task_variables)

    # Run graph using pydantic-graph's run method
    try:
        await graph.run(start_node(), state=state)
        return {
            "task_idx": task_idx,
            "task_variables": task_variables,
            "node_trace": state.node_trace,
            "messages": state.messages,
        }
    except Exception as e:
        click.echo(f"Error running task {task_idx}: {e}", err=True)
        return {
            "task_idx": task_idx,
            "error": str(e),
        }
