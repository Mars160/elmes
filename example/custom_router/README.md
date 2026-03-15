# 自定义 Router 开发指南

## 什么是 Router？

Router 用于在 Agent 节点之间进行条件路由，根据当前状态决定下一个要执行的节点。例如：

- 根据关键词判断对话是否结束
- 根据对话轮数限制循环次数
- 根据 Agent 输出的评分决定下一步

## 编写自定义 Router

### 1. 继承 Router 基类

```python
from elmes.graph.router import Router
from elmes.graph.state import GraphState

@Router.register()  # 自动注册 router
class MyRouter(Router):
    def __init__(self, param1: str, param2: int):
        super().__init__("my_router")  # router 名称
        self.param1 = param1
        self.param2 = param2
    
    def route(self, state: GraphState) -> str:
        """
        根据当前状态返回下一个节点的名称
        
        Args:
            state: 当前图状态，包含 query, messages, node_trace 等
            
        Returns:
            下一个节点的名称（如 "END", "student"）
        """
        # 你的路由逻辑
        if some_condition:
            return "END"
        return "next_agent"
    
    @property
    def available_targets(self) -> set[str]:
        """返回所有可能的目标节点集合，用于验证"""
        return {"END", "next_agent"}
```

### 2. 使用装饰器注册

**自动命名**（CamelCase 转 snake_case）：
```python
@Router.register()
class TurnLimitRouter(Router):
    ...
# 注册为: turn_limit_router
```

**自定义名称**：
```python
@Router.register("custom_name")
class MyRouter(Router):
    ...
# 注册为: custom_name
```

### 3. GraphState 可用字段

```python
@dataclass
class GraphState:
    query: str                    # 当前查询内容（通常是上一个 Agent 的输出）
    query_from: str              # 上一个节点的名称
    messages: dict[str, list]    # 每个 Agent 的消息历史
    node_trace: list[str]        # 节点执行轨迹（用于计算轮数等）
```

### 4. 在 YAML 配置中使用

```yaml
directions:
  # 基础用法
  - teacher -> router:turn_limit_router(max_turns=5, end_node=END, continue_node=student)
  
  # 支持多种参数类型
  - student -> router:score_based(high_threshold=80, high_node=END, low_node=teacher)
```

**支持的参数类型**：
- 字符串: `target="student"` 或 `target='student'` 或 `target=student`
- 列表: `keywords=["end", "stop", "finish"]`
- 数字: `threshold=80`, `max_turns=10`
- 布尔: `strict=True`

## 完整示例

### TurnLimitRouter（回合数限制）

```python
from elmes.graph.router import Router
from elmes.graph.state import GraphState

@Router.register()
class TurnLimitRouter(Router):
    """当对话达到指定轮数时结束"""
    
    def __init__(self, max_turns: int, end_node: str, continue_node: str):
        super().__init__("turn_limit_router")
        self.max_turns = int(max_turns)
        self.end_node = end_node
        self.continue_node = continue_node
    
    def route(self, state: GraphState) -> str:
        if len(state.node_trace) >= self.max_turns:
            return self.end_node
        return self.continue_node
    
    @property
    def available_targets(self) -> set[str]:
        return {self.end_node, self.continue_node}
```

YAML 配置：
```yaml
directions:
  - START -> teacher
  - teacher -> router:turn_limit_router(max_turns=10, end_node=END, continue_node=student)
  - student -> teacher
```

### ScoreBasedRouter（评分路由）

```python
import re
from elmes.graph.router import Router
from elmes.graph.state import GraphState

@Router.register("score_based")
class ScoreBasedRouter(Router):
    """根据 Agent 输出的评分决定路由"""
    
    def __init__(self, high_threshold: int, high_node: str, low_node: str):
        super().__init__("score_based")
        self.high_threshold = int(high_threshold)
        self.high_node = high_node
        self.low_node = low_node
    
    def route(self, state: GraphState) -> str:
        # 从输出中提取评分
        match = re.search(r'Score:\s*(\d+)', state.query)
        if match:
            score = int(match.group(1))
            if score >= self.high_threshold:
                return self.high_node
        return self.low_node
    
    @property
    def available_targets(self) -> set[str]:
        return {self.high_node, self.low_node}
```

YAML 配置：
```yaml
directions:
  - teacher -> evaluator
  - evaluator -> router:score_based(high_threshold=80, high_node=END, low_node=student)
```

## 内置 Routers

### AnyKeywordRouter

检查输出中是否包含任意关键词：

```yaml
directions:
  - teacher -> router:any_keyword_router(keywords=["<end>", "下课"], exists_to=END, else_to=student)
```

参数：
- `keywords`: 要搜索的关键词列表
- `exists_to`: 找到关键词时的目标节点
- `else_to`: 未找到关键词时的目标节点

## 调试技巧

1. **查看已注册的 routers**：
```python
from elmes.graph.router import Router, ensure_routers_registered
ensure_routers_registered()
print(Router.list_routers())
```

2. **测试 router**：
```python
router = TurnLimitRouter(max_turns=5, end_node="END", continue_node="student")
state = GraphState(query="test", node_trace=["teacher", "student"])
result = router.route(state)
print(f"Routed to: {result}")
```

3. **打印调试信息**：
```python
def route(self, state: GraphState) -> str:
    print(f"[Router Debug] Query: {state.query[:100]}...")
    print(f"[Router Debug] Node trace: {state.node_trace}")
    # ... 路由逻辑
```

## 最佳实践

1. **命名规范**：使用描述性的类名，CamelCase 会自动转换为 snake_case
2. **参数验证**：在 `__init__` 中验证参数有效性
3. **错误处理**：处理边界情况（如 query 为空）
4. **文档**：为 router 添加 docstring 说明用途和参数
5. **测试**：编写单元测试验证路由逻辑

## 文件位置

- 自定义 router 文件可放在项目任意位置（如 `routers/` 目录）
- 确保在使用前导入（可在主程序或 `__init__.py` 中导入）
- 内置 routers 位于: `elmes/graph/router/`
