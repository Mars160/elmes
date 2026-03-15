from pathlib import Path
from typing import Any

from elmes.cli.export.exporter.json_ import aexport_json


async def aexport_label_studio(input_path: Path) -> dict[str, Any]:
    """Export a single task state file to Label Studio format."""
    _, json_obj = await aexport_json(input_path)

    return {
        "data": {
            "task_idx": json_obj.get("task_idx"),
            "task_variables": json_obj.get("task_variables", {}),
            "node_trace": json_obj.get("node_trace", []),
            "messages": json_obj.get("conversation", []),
        }
    }
