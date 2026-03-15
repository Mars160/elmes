from pydantic_ai import Agent
from pydantic_ai.models import Model

from elmes.entity.agent import AgentConfig


def build_agent(agent_config: AgentConfig, model: Model) -> Agent:
    """根据AgentConfig和ModelConfig构建Agent实例"""
    return Agent(
        model=model,
        name=agent_config.name,
        retries=agent_config.retries or 3,
        system_prompt=agent_config.system_prompt,
    )
