"""Custom Router Example - 展示如何编写和使用自定义 Router

这个示例展示了如何：
1. 创建一个自定义 Router（基于回合数的路由器）
2. 注册并使用自定义 Router
3. 在 YAML 配置中使用自定义 Router

使用场景：
- 限制对话轮数
- 根据对话历史做决策
- 实现复杂的业务逻辑路由
"""

from elmes.graph.router import Router
from elmes.graph.state import GraphState


@Router.register()  # 使用装饰器注册 router，名称会自动转换为 turn_limit_router
class TurnLimitRouter(Router):
    """基于回合数限制的路由器

    当对话达到指定轮数时，路由到 end 节点，否则继续对话。

    配置示例：
        directions:
          - teacher -> router:turn_limit_router(max_turns=10, end_node=END, continue_node=student)

    Args:
        max_turns: 最大对话轮数
        end_node: 达到最大轮数时的目标节点（通常是 END）
        continue_node: 未达到最大轮数时的目标节点
    """

    def __init__(self, max_turns: int, end_node: str, continue_node: str):
        super().__init__("turn_limit_router")
        self.max_turns = int(max_turns)
        self.end_node = end_node
        self.continue_node = continue_node

    def route(self, state: GraphState) -> str:
        """根据当前回合数决定路由目标

        通过检查 node_trace 的长度来判断对话轮数
        """
        current_turns = len(state.node_trace)

        if current_turns >= self.max_turns:
            print(
                f"[TurnLimitRouter] Reached max turns ({self.max_turns}), routing to {self.end_node}"
            )
            return self.end_node
        else:
            print(
                f"[TurnLimitRouter] Turn {current_turns}/{self.max_turns}, routing to {self.continue_node}"
            )
            return self.continue_node

    @property
    def available_targets(self) -> set[str]:
        """返回所有可能的目标节点"""
        return {self.end_node, self.continue_node}


@Router.register("score_based")  # 使用自定义名称注册
class ScoreBasedRouter(Router):
    """基于评分的路由器

    解析 Agent 的输出，根据评分决定路由。
    适用于：质量评估、难度分级等场景。

    配置示例：
        directions:
          - evaluator -> router:score_based(high_threshold=80, high_node=END, low_node=student)

    假设 Agent 输出格式包含 "Score: XX" 的模式
    """

    def __init__(self, high_threshold: int, high_node: str, low_node: str):
        super().__init__("score_based")
        self.high_threshold = int(high_threshold)
        self.high_node = high_node
        self.low_node = low_node

    def route(self, state: GraphState) -> str:
        """解析评分并决定路由"""
        import re

        query = state.query

        # 尝试从输出中提取评分
        score_match = re.search(r"[Ss]core[:\s]*(\d+)", query)

        if score_match:
            score = int(score_match.group(1))
            print(f"[ScoreBasedRouter] Detected score: {score}")

            if score >= self.high_threshold:
                print(
                    f"[ScoreBasedRouter] Score >= {self.high_threshold}, routing to {self.high_node}"
                )
                return self.high_node

        print(f"[ScoreBasedRouter] Routing to {self.low_node}")
        return self.low_node

    @property
    def available_targets(self) -> set[str]:
        return {self.high_node, self.low_node}


# 使用示例
if __name__ == "__main__":
    from elmes.graph.router import Router, ensure_routers_registered

    # 确保内置 routers 已注册
    ensure_routers_registered()

    # 查看所有已注册的 routers
    print("Registered routers:", Router.list_routers())

    # 测试 TurnLimitRouter
    print("\n--- Testing TurnLimitRouter ---")
    router = TurnLimitRouter(max_turns=3, end_node="END", continue_node="student")

    state = GraphState()
    print(f"Initial state: {router.route(state)}")  # 应该是 student

    state.node_trace = ["teacher", "student"]
    print(f"After 2 turns: {router.route(state)}")  # 应该是 student

    state.node_trace = ["teacher", "student", "teacher", "student"]
    print(f"After 4 turns: {router.route(state)}")  # 应该是 END

    # 测试 ScoreBasedRouter
    print("\n--- Testing ScoreBasedRouter ---")
    score_router = ScoreBasedRouter(
        high_threshold=80, high_node="END", low_node="student"
    )

    state = GraphState()
    state.query = "The student answered correctly. Score: 85"
    print(f"Score 85: {score_router.route(state)}")  # 应该是 END

    state.query = "The student needs more practice. Score: 60"
    print(f"Score 60: {score_router.route(state)}")  # 应该是 student
