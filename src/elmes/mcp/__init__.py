from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerSSE, MCPServerStdio

from elmes.config.mcps import MCPStdio, MCPSSE, MCPStreamableHTTP


def build_mcp(
    mcp_config: MCPStdio | MCPSSE | MCPStreamableHTTP,
) -> MCPServerStdio | MCPServerSSE | MCPServerStreamableHTTP:
    """根据MCPConfig构建MCP实例"""
    if isinstance(mcp_config, MCPStdio):
        return MCPServerStdio(
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
