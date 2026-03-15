"""JSON exporter for conversation data."""

import json
from pathlib import Path
from typing import Any


def _extract_agent_reply(
    response_msg: dict, next_request_msg: dict | None
) -> list[dict]:
    """Extract one agent reply turn as a structured content list.

    A turn consists of:
    - tool-call parts from the response
    - tool-return parts from the immediately following request (if any)
    - text parts from the response

    Returns a list of content items, each with a 'type' field.
    """
    content: list[dict[str, Any]] = []

    # Collect tool-calls from response
    tool_call_ids: set[str] = set()
    for part in response_msg.get("parts", []):
        kind = part.get("part_kind")
        if kind == "thinking":
            content.append(
                {
                    "type": "thinking",
                    "thinking": part.get("content"),
                }
            )
        elif kind == "tool-call":
            try:
                args = json.loads(part.get("args", "{}"))
            except (json.JSONDecodeError, TypeError):
                args = part.get("args")
            content.append(
                {
                    "type": "tool-call",
                    "tool_name": part.get("tool_name"),
                    "args": args,
                    "tool_call_id": part.get("tool_call_id"),
                }
            )
            if part.get("tool_call_id"):
                tool_call_ids.add(part["tool_call_id"])

    # Collect tool-returns from the following request (matched by tool_call_id)
    if next_request_msg and tool_call_ids:
        for part in next_request_msg.get("parts", []):
            kind = part.get("part_kind")
            if kind == "tool-return" and part.get("tool_call_id") in tool_call_ids:
                content.append(
                    {
                        "type": "tool-return",
                        "tool_name": part.get("tool_name"),
                        "result": part.get("content"),
                        "tool_call_id": part.get("tool_call_id"),
                        "outcome": part.get("outcome"),
                    }
                )

    # Collect text parts from response
    for part in response_msg.get("parts", []):
        kind = part.get("part_kind")
        if kind == "text":
            text = part.get("content", "")
            if text:
                content.append({"type": "text", "text": text})

    return content


def _extract_agent_replies(messages: list[dict]) -> list[list[dict]]:
    """Extract each agent visit as a structured content list.

    Each element corresponds to one visit in node_trace (one response turn).
    """
    replies: list[list[dict]] = []
    for i, msg in enumerate(messages):
        if msg.get("kind") != "response":
            continue
        next_msg = messages[i + 1] if i + 1 < len(messages) else None
        content = _extract_agent_reply(msg, next_msg)
        if content:
            replies.append(content)
    return replies


def load_task_state(task_file: Path) -> dict[str, Any]:
    """Load a task intermediate state file."""
    with open(task_file, encoding="utf-8") as f:
        return json.load(f)


async def aexport_json(input_path: Path) -> tuple[Path, dict[str, Any]]:
    """Export a single task state file to a structured JSON object.

    Args:
        input_path: Path to the task_N.json intermediate state file.

    Returns:
        Tuple of (input_path, exported_data)
    """
    state = load_task_state(input_path)

    # Extract each agent's reply turns
    agents: dict[str, list[list[dict]]] = {}
    for agent_name, raw_messages in state.get("messages", {}).items():
        agents[agent_name] = _extract_agent_replies(raw_messages)

    # Build flat conversation ordered by node_trace
    node_trace = state.get("node_trace", [])
    reply_index: dict[str, int] = {name: 0 for name in agents}
    conversation: list[dict[str, Any]] = []

    for agent_name in node_trace:
        if agent_name not in agents:
            continue
        idx = reply_index[agent_name]
        replies = agents[agent_name]
        if idx < len(replies):
            conversation.append({"role": agent_name, "content": replies[idx]})
            reply_index[agent_name] = idx + 1

    obj = {
        "task_idx": state.get("task_idx"),
        "task_variables": state.get("task_variables", {}),
        "node_trace": node_trace,
        "conversation": conversation,
    }

    return input_path, obj
