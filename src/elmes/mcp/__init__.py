import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.message import SessionMessage
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerSSE, MCPServerStdio

from elmes.config.mcps import MCPStdio, MCPSSE, MCPStreamableHTTP

_DEVNULL = open(os.devnull, "w")


class _QuietMCPServerStdio(MCPServerStdio):
    """MCPServerStdio that suppresses subprocess stderr output."""

    @asynccontextmanager  # type: ignore[override]
    async def client_streams(
        self,
    ) -> AsyncIterator[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
        ]
    ]:
        server = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env,
            cwd=self.cwd,
        )
        async with stdio_client(server=server, errlog=_DEVNULL) as (
            read_stream,
            write_stream,
        ):
            yield read_stream, write_stream


def build_mcp(
    mcp_config: MCPStdio | MCPSSE | MCPStreamableHTTP,
) -> MCPServerStdio | MCPServerSSE | MCPServerStreamableHTTP:
    """根据MCPConfig构建MCP实例"""
    if isinstance(mcp_config, MCPStdio):
        return _QuietMCPServerStdio(
            command=mcp_config.command,
            args=mcp_config.args,
            env=mcp_config.env,
            timeout=mcp_config.timeout,
            max_retries=mcp_config.max_retries,
        )
    elif isinstance(mcp_config, MCPSSE):
        return MCPServerSSE(
            url=mcp_config.url,
            headers=mcp_config.headers,
            timeout=mcp_config.timeout,
            max_retries=mcp_config.max_retries,
        )
    elif isinstance(mcp_config, MCPStreamableHTTP):
        return MCPServerStreamableHTTP(
            url=mcp_config.url,
            headers=mcp_config.headers,
            timeout=mcp_config.timeout,
            max_retries=mcp_config.max_retries,
        )
    else:
        raise ValueError(f"Unsupported MCP config type: {type(mcp_config)}")
