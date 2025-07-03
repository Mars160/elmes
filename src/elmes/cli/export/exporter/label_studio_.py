from pathlib import Path
from typing import Dict, Any, List

from elmes.cli.export.exporter.json_ import aexport_json

async def aexport_label_studio(input_path: Path) -> Dict[str, Any]:
    _, json_obj = await aexport_json(input_path)
    msgs = []
    for msg in json_obj["messages"]:
        msgs.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    return {
        "data": {
            "messages": msgs,
            "task_id": input_path.stem
        }
    }