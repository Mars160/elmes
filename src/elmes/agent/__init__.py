from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model as PydanticAIModel
from pydantic_ai.mcp import MCPServer

from elmes.config import Agent as AgentConfig


def build_agent(
    agent_config: AgentConfig,
    model_dict: dict[str, PydanticAIModel],
    task_variables: dict[str, str],
    mcp_dict: dict[str, MCPServer],
) -> Agent:
    """根据AgentConfig和ModelConfig构建Agent实例"""
    system_prompt = agent_config.system_prompt
    formated_system_prompt = system_prompt.format(**task_variables)
    tools = []
    for tool_name in agent_config.tools or []:
        if tool_name not in mcp_dict:
            raise ValueError(f"Tool {tool_name} is not defined in mcp_dict")
        tools.append(mcp_dict[tool_name])
    agent = Agent(
        model=model_dict.get(agent_config.model.name),
        name=agent_config.name,
        retries=agent_config.retries or 3,
        instructions=formated_system_prompt,
        toolsets=tools,
    )

    return agent


if __name__ == "__main__":
    from elmes.config import load_config
    from elmes.model import build_model
    from elmes.mcp import build_mcp

    config = load_config("config.yaml.example")
    model_dict = {}
    for model_name, model_config in config.models.items():
        model_dict[model_name] = build_model(model_config)

    mcp_dict = {}
    for mcp_name, mcp_config in config.mcps.items():
        mcp_dict[mcp_name] = build_mcp(mcp_config)

    for agent_name, agent_config in config.agents.items():
        agent = build_agent(agent_config, model_dict, config.tasks.content[0], mcp_dict)
        print(f"Agent {agent_name} built successfully: {agent.__dict__}")
