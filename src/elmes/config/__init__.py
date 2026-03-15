from elmes.config.globals import Globals
from elmes.config.agents import Agent
from elmes.config.models import Model
from elmes.config.tasks import Task
from elmes.config.eval import Eval
from elmes.config.directions import Direction
from elmes.config.mcps import MCPUnion, MCP

from pydantic import BaseModel, Field


class Elmes(BaseModel):
    globals: Globals = Field(..., description="全局配置")
    models: dict[str, Model] = Field(..., description="模型配置列表")
    agents: dict[str, Agent] = Field(..., description="agent配置列表")
    directions: list[Direction] = Field(
        ..., description="信息传递方向列表，如[student->teacher, teacher->student]"
    )
    tasks: Task = Field(..., description="任务配置列表")
    evals: Eval = Field(..., description="评估配置列表")
    mcps: dict[str, MCPUnion] = Field(
        default_factory=dict, description="MCP服务器配置列表"
    )


def load_config(config_path: str) -> Elmes:
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    globals_config = config_dict.get("globals", {})
    globals = Globals(**globals_config)

    models_config = config_dict.get("models", {})
    models = {
        model_name: Model(name=model_name, **model_config)
        for model_name, model_config in models_config.items()
    }

    agents_config = config_dict.get("agents", {})
    agents = {}
    for agent_name, agent_config in agents_config.items():
        assert "model" in agent_config, f"agent {agent_name}配置必须包含model字段"
        model_name = agent_config["model"]
        if model_name not in models:
            raise ValueError(
                f"agent {agent_name}使用的模型{model_name}未在models中定义"
            )
        agent_config["model"] = models[model_name]
        agents[agent_name] = Agent(name=agent_name, **agent_config)

    direction_strs = config_dict.get("directions", [])
    directions = []
    for direction_str in direction_strs:
        assert " -> " in direction_str, (
            f"direction {direction_str}格式错误，必须包含->，且前后必须有空格"
        )
        from_, to_ = direction_str.split(" -> ")
        directions.append(Direction(from_=from_, to_=to_))

    tasks_config = config_dict.get("tasks", None)
    assert tasks_config is not None, "配置文件必须包含tasks字段"
    tasks = Task.from_dict(tasks_config)

    evals_config = config_dict.get("evaluation", None)
    assert evals_config is not None, "配置文件必须包含evaluation字段"
    judge_model = evals_config.get("judge_model", None)
    if judge_model is None:
        raise ValueError("evaluation配置必须包含judge_model字段")
    if judge_model not in models:
        raise ValueError(
            f"evaluation配置中judge_model字段指定的模型{judge_model}未在models中定义"
        )
    evals_config["judge_model"] = models[judge_model]
    evals = Eval(**evals_config)

    mcps_config = config_dict.get("mcps", {})
    mcps = {
        mcp_name: MCP.from_dict(mcp_config)
        for mcp_name, mcp_config in mcps_config.items()
    }

    return Elmes(
        globals=globals,
        models=models,
        agents=agents,
        directions=directions,
        tasks=tasks,
        evals=evals,
        mcps=mcps,
    )


if __name__ == "__main__":
    config = load_config("config.yaml.example")
    print(config)
