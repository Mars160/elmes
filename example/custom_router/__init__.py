"""
Custom Router 使用示例 - 在 ELMES 中使用自定义 Router

这个示例展示了如何在 ELMES 项目中使用自定义 Router。
"""

# 步骤 1: 导入你的自定义 Router
# 在你的主程序或 __init__.py 中导入自定义 router 模块
# 这会自动注册 router
from example.custom_router.turn_limit_router import TurnLimitRouter, ScoreBasedRouter

# 步骤 2: 确保 routers 已注册
from elmes.graph.router import ensure_routers_registered

ensure_routers_registered()

# 步骤 3: 查看已注册的 routers
from elmes.graph.router import Router

print("Available routers:", Router.list_routers())


# 示例配置 (config_with_custom_router.yaml)
CONFIG_EXAMPLE = """
# 一些全局字段
globals:
  concurrency: 16
  recursion_limit: 50

# 定义模型
models:
  teacher_model:
    type: openai
    api_key: <YOUR API KEY>
    base_url: <YOUR API BASE>
    model: gpt-4o-mini

  student_model:
    type: openai
    api_key: <YOUR API KEY>
    base_url: <YOUR API BASE>
    model: gpt-4o-mini

  evaluator_model:
    type: openai
    api_key: <YOUR API KEY>
    base_url: <YOUR API BASE>
    model: gpt-4o-mini

# 定义 agents
agents:
  teacher:
    model: teacher_model
    system_prompt: |
      你是一位数学老师。请引导学生解决数学问题。
      当学生理解后，请说 "教学结束" 来表示完成。

  student:
    model: student_model
    system_prompt: |
      你是一位学生。请回答老师的问题，并展示你的思考过程。

  evaluator:
    model: evaluator_model
    system_prompt: |
      你是一位评估员。请评估学生的回答质量。
      在回答末尾输出评分："Score: XX" (0-100分)

# 使用自定义 router 的方向配置
directions:
  # 开始 -> 老师
  - START -> teacher
  
  # 老师 -> TurnLimitRouter: 限制对话最多 10 轮
  - teacher -> router:turn_limit_router(max_turns=10, end_node=END, continue_node=student)
  
  # 学生 -> 老师
  - student -> teacher
  
  # 或者使用 ScoreBasedRouter: 根据评分决定
  # - teacher -> evaluator
  # - evaluator -> router:score_based(high_threshold=80, high_node=END, low_node=student)

tasks:
  start_prompt: "请讲解这道数学题: {question}"
  mode: union
  content:
    question:
      - "1 + 1 = ?"
      - "2 * 3 = ?"

evaluation:
  judge_model: evaluator_model
  mode: tool
"""

print("\n" + "=" * 60)
print("示例配置文件内容:")
print("=" * 60)
print(CONFIG_EXAMPLE)

# 步骤 4: 使用配置运行
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("演示如何在代码中使用自定义 Router:")
    print("=" * 60)

    from elmes.config import load_config
    from elmes.model import build_model
    from elmes.agent import build_agent
    from elmes.graph import build_graph

    # 注意：实际使用时需要创建真实的 config.yaml 文件
    # 这里只是演示结构

    print("""
使用步骤:

1. 创建自定义 router 文件 (如 turn_limit_router.py)
2. 在主程序中导入: from example.custom_router.turn_limit_router import TurnLimitRouter
3. 调用 ensure_routers_registered() 注册所有 routers
4. 在 YAML 配置中使用: router:turn_limit_router(max_turns=10, end_node=END, continue_node=student)
5. 正常运行 ELMES pipeline

完整代码示例:

```python
# main.py
from example.custom_router.turn_limit_router import TurnLimitRouter
from elmes.graph.router import ensure_routers_registered
from elmes.config import load_config
from elmes.model import build_model
from elmes.agent import build_agent
from elmes.mcp import build_mcp
from elmes.graph import build_graph

# 确保 routers 已注册
ensure_routers_registered()

# 加载配置
config = load_config("config.yaml")

# 构建 models, agents...
model_dict = {name: build_model(m) for name, m in config.models.items()}
mcp_dict = {name: build_mcp(m) for name, m in config.mcps.items()}
agents = {}
for name, agent_config in config.agents.items():
    task_vars = config.tasks.content[0] if config.tasks.content else {}
    agents[name] = build_agent(agent_config, model_dict, task_vars, mcp_dict)

# 构建 graph（会自动使用配置中的自定义 router）
graph, start_node = build_graph(
    config.directions,
    agents,
    config.globals.recursion_limit,
)

# 运行 graph...
```
""")
