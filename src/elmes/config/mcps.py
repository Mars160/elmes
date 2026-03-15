from pydantic import BaseModel, Field
from typing import Literal, Annotated


class MCP:
    @staticmethod
    def from_dict(data: dict):
        mcp_type = data.get("type")
        if mcp_type == "stdio":
            return MCPStdio(**data)
        elif mcp_type == "http-with-sse":
            return MCPSSE(**data)
        elif mcp_type == "streamable-http":
            return MCPStreamableHTTP(**data)
        else:
            raise ValueError(f"Unsupported MCP type: {mcp_type}")


class MCPBase(BaseModel):
    timeout: int = Field(30, description="MCP服务器调用超时时间（秒）")
    max_retries: int = Field(3, description="MCP服务器调用失败后的最大重试次数")


class MCPStdio(MCPBase):
    type: Literal["stdio"] = Field("stdio", description="MCP服务器的类型，固定为stdio")
    command: str = Field(..., description="启动MCP服务器的命令")
    args: list[str] = Field(
        default_factory=list, description="启动MCP服务器的命令行参数"
    )
    env: dict[str, str] = Field(
        default_factory=dict, description="MCP服务器的环境变量配置"
    )


class MCPSSE(MCPBase):
    type: Literal["http-with-sse"] = Field(
        "http-with-sse", description="MCP服务器的类型，固定为http-with-sse"
    )
    url: str = Field(..., description="MCP服务器的URL地址")
    headers: dict[str, str] = Field(
        default_factory=dict, description="MCP服务器的HTTP请求头配置"
    )


class MCPStreamableHTTP(MCPBase):
    type: Literal["streamable-http"] = Field(
        "streamable-http", description="MCP服务器的类型，固定为streamable-http"
    )
    url: str = Field(..., description="MCP服务器的URL地址")
    headers: dict[str, str] = Field(
        default_factory=dict, description="MCP服务器的HTTP请求头配置"
    )


MCPUnion = Annotated[
    MCPStdio | MCPSSE | MCPStreamableHTTP,
    Field(
        discriminator="type",
        description="MCP服务器的配置，支持stdio、http-with-sse、streamable-http三种类型",
    ),
]

if __name__ == "__main__":
    import yaml

    with open("config.yaml.example", "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    data = config_dict.get("mcps", None)
    if data:
        for mcp_name, mcp_config in data.items():
            mcp_instance = MCP.from_dict(mcp_config)
            print(f"MCP {mcp_name} parsed successfully: {mcp_instance.__dict__}")
