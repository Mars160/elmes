# ELMES - Education Language Model Evaluation System

ELMES (Education Language Model Evaluation System) 是一个 Python 框架，旨在为 LLM 不同场景下的各种任务提供代理编排和自动评估的功能。它采用模块化架构，基于 YAML 配置，可扩展的实体使得该框架适用于构建、配置和评估复杂的基于代理的工作流。

## 主要特点

- **模块化架构**：基于 LangGraph 构建的灵活代理编排系统
- **基于 YAML 的配置**：简单直观的任务和工作流定义，支持变量模板渲染
- **多代理协作**：支持多个 LLM 代理之间的交互和协作，并可通过路由器实现复杂流程控制
- **自动评估**：内置评估框架，支持 JSON-Schema 或工具（function calling）两种输出模式
- **记忆管理与持久化**：对话历史通过 SQLite checkpoint 持久化，长链路任务不中断
- **并发与重试机制**：内置并发执行（`concurrency`）与可配置的 Tenacity 重试策略
- **可视化流程图**：通过 `draw` 命令可视化代理交互流程，直观展示工作流设计

## 安装

```bash
pip install elmes
```

## 快速开始

1. 创建配置文件 `config.yaml`（可参考 `config.yaml.example`）
2. 运行 ELMES 命令行工具

```bash
elmes run --config config.yaml
```

## 配置示例

ELMES 使用 YAML 配置文件定义任务、代理和评估方式。以下是一个简化的配置示例：

```yaml
# 全局配置
globals:
  concurrency: 16
  recursion_limit: 50
  retry:
    attempt: 3
    interval: 3
  memory:
    path: ./logs/my_exp

# 定义模型
models:
  gpt4o:
    type: openai
    api_key: ${OPENAI_KEY}
    api_base: https://api.openai.com/v1
    model: gpt-4o-mini
    kargs:
      temperature: 0.7

# 定义代理
agents:
  teacher:
    model: gpt4o
    prompt:
      - role: system
        content: "你是数学老师，学生画像: {image}"
      - role: user
        content: "{question}"
    memory:
      enable: true
      keep_turns: 3

# 定义代理间的信息传递方向
directions:
  - START -> teacher
  - teacher -> router:any_keyword_route(keywords=["<end>", "下课"], exists_to=END, else_to="student")
  - student -> teacher

# 定义任务内容
tasks:
  mode: union
  start_prompt:
    role: user
    content: "{question}"
  content:
    image:
      - "逻辑思维突出，热爱科学"
    question:
      - "一个三位数..."
      - "师徒两人装配自行车..."

# 评估配置
evaluation:
  name: math_tutor_eval
  model: gpt4o
  format_mode: prompt
  prompt:
    - role: system
      content: "你是专业评估专家..."
  format:
    - field: accuracy
      type: float
      description: "准确性"
    - field: guidance
      type: dict
      description: "引导性"
      items:
        - field: score
          type: float
          description: "分数"
        - field: reason
          type: str
          description: "理由"
```

## 核心组件

ELMES 由以下几个核心组件构成：

1. **代理系统**：基于 LangGraph 构建的代理编排框架
2. **路由系统**：控制代理之间的信息流动和交互
3. **配置系统**：处理 YAML 配置文件并构建相应的实体
4. **评估系统**：对代理性能进行自动化评估
5. **记忆系统**：管理代理的对话历史和上下文

## 进阶使用

### 自定义路由器

ELMES 支持自定义路由逻辑，控制代理之间的交互流程：

```yaml
directions:
  - teacher -> router:any_keyword_route(keywords=["<end>", "下课"], exists_to=END, else_to="student")
```

### 评估格式化

ELMES 支持多种评估输出格式，包括结构化的 JSON 输出：

```yaml
evaluation:
  format:
    - field: accuracy
      type: float
      description: "准确性评分"
    - field: guidance
      type: dict
      description: "引导性评分"
      items:
        - field: score
          type: float
          description: "分数"
        - field: reason
          type: str
          description: "评分理由"
```

### 可视化代理流程

ELMES 提供 `draw` 命令，可以将配置文件中定义的代理交互流程绘制为可视化图表：

```bash
elmes draw --config config.yaml
```

该命令会根据配置文件中的 `directions` 部分生成一个 Mermaid 流程图，并保存为 PNG 格式（与配置文件同名）。这对于理解复杂的代理交互流程和调试路由逻辑特别有帮助。

![代理流程图示例](docs/config.png)

## 贡献

欢迎提交 Pull Request 或创建 Issue 来改进 ELMES。

## 配置文件详解

以下各段落基于 `config.yaml.example` 展开，帮助你快速理解和定制自己的任务。

### 1. globals

```yaml
globals:
  concurrency: 16 # 并发协程数，控制整体吞吐
  recursion_limit: 50 # LangGraph 递归深度限制，防止死循环
  retry: # Tenacity 重试策略
    attempt: 3 # 最大重试次数
    interval: 3 # 每次重试间隔（秒）
  memory:
    path: ./logs/my_exp # 所有 SQLite checkpoint 的存储目录
```

- **并发** 与 **递归深度** 保证任务性能与安全。
- **retry** 字段映射到 Tenacity，自动为每个 LLM 调用提供重试。
- **memory.path** 决定了对话历史与评测结果的持久化位置。

### 2. models

```yaml
models:
  gpt4o:
    type: openai # 目前支持 openai / anthropic / qualsiasi future backend
    api_key: ${OPENAI_KEY}
    api_base: https://api.openai.com/v1
    model: gpt-4o-mini
    kargs: # 任何传递给 SDK 的 keyword arguments
      temperature: 0.7
```

- 一个配置块 = 一个可调用模型。
- `kargs` 将在调用 `client.chat.completions.create(**kargs)` 时透传。

### 3. agents

```yaml
agents:
  teacher:
    model: gpt4o # 关联到 `models` 的键
    prompt: # 完整 OpenAI 聊天格式 Prompt，可使用变量占位
      - role: system
        content: "你是数学老师，学生画像: {image}"
      - role: user
        content: "{question}"
    memory: # 可选，单独覆盖全局 memory 策略
      enable: true
      keep_turns: 3 # 最多携带 3 轮上下文
```

- Prompt 支持 **占位符模板**，在任务运行时由 `tasks.content` 动态填充。
- 每个代理最终被包裹为一个 LangGraph **节点**，自动注入重试与记忆逻辑。

### 4. directions

```yaml
directions:
  - START -> teacher
  - teacher -> router:any_keyword_route(keywords=["<end>", "下课"], exists_to=END, else_to="student")
  - student -> teacher
```

- 使用箭头串联节点，描述了 LangGraph 中的 **有向边**。
- 以 `router:` 前缀调用任意 Python 函数，实现条件跳转；示例中 `any_keyword_route` 根据关键词决定流程是否结束。

### 5. tasks

```yaml
tasks:
  mode: union # union=笛卡尔积组合，iter=顺序遍历
  start_prompt: # 可选，定义从 START 发出的首条消息
    role: user
    content: "{question}"
  content:
    image:
      - "逻辑思维突出，热爱科学"
    question:
      - "一个三位数..."
      - "师徒两人装配自行车..."
```

- `mode: union` 表示将 `image × question` 形成多任务并并发执行。
- 变量将被 **一对一** 替换进代理与评估 prompt 中。

### 6. evaluation（可选）

```yaml
evaluation:
  name: math_tutor_eval
  model: gpt4o # 用于打分的模型
  format_mode: prompt # prompt 或 tool 两种模式
  prompt:
    - role: system
      content: "你是专业评估专家..."
  format:
    - field: accuracy
      type: float
      description: "准确性"
    - field: guidance
      type: dict
      description: "引导性"
      items:
        - field: score
          type: float
          description: "分数"
        - field: reason
          type: str
          description: "理由"
```

- **tool 模式**：利用 OpenAI function-calling，保证输出 JSON 100% 合法。
- **prompt 模式**：通过严格的占位符和正则抽取，兼容不支持 function-calling 的模型（如 Gemini）。

> 若 `evaluation` 块被省略，ELMES 将仅执行任务，跳过评估阶段。

### 7. 命令行工具

ELMES 提供多个命令行工具，方便用户执行不同的操作：

```bash
# 生成对话
elmes generate --config config.yaml

# 导出 JSON 格式对话
elmes export-json --config config.yaml

# 评估对话结果
elmes eval --config config.yaml

# 完整流水线（生成+导出+评估，上述命令3合1）
elmes pipeline --config config.yaml

# 可视化评估结果
elmes visualize eval/

# 绘制Agent流程图
elmes draw --config config.yaml
```

---

通过以上配置，你可以 **零代码** 地组装出多 LLM 互动、自动化评测并持久化结果的完整流水线——这正是 ELMES 的核心价值所在。
