import sqlite3
from typing import Tuple, Dict, Any
from pathlib import Path
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.base import Checkpoint


async def aexport_json(input_path: Path) -> Tuple[Path, Dict[str, Any]]:
    conn = sqlite3.connect(input_path)
    cursor = conn.cursor()
    sql = "select checkpoint_ns, checkpoint_id, parent_checkpoint_id, checkpoint from checkpoints"
    cursor.execute(sql)
    results = cursor.fetchall()[-1]
    cns, cid, pcid, c = results
    jps = JsonPlusSerializer()
    checkpoint: Checkpoint = jps.loads_typed(("msgpack", c))
    messages = []
    for m in checkpoint.get("channel_values")["messages"]:
        if m.name is None:
            continue
        if "</think>" in m.content:
            content_split = m.content.split("</think>")
            reasoning = content_split[0].strip()
            response = content_split[1].strip()
        else:
            reasoning = ""
            response = m.content.strip()
        messages.append({"role": m.name, "content": response, "reasoning": reasoning})

    sql = "select key, value from task"
    cursor.execute(sql)
    results = cursor.fetchall()
    obj = {"task": {}, "messages": messages}

    for key, value in results:
        obj["task"][key] = value

    return input_path, obj
