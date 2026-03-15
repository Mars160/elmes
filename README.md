[简体中文](./README.md) | [English](./README-en.md)

[论文](https://arxiv.org/abs/2507.22947)

<p align="center">
  <img src="./docs/assets/icons/elmes-logo.svg" alt="ELMES Logo" width="120" height="120">
</p>

<h1 align="center">ELMES - Evaluating Large Language Models in Educational Scenarios</h1>

ELMES (Evaluating Large Language Models in Educational Scenarios) 是一个 Python 框架，旨在为 LLM 不同场景下的各种任务提供代理编排和自动评估的功能。它采用模块化架构，基于 YAML 配置，可扩展的实体使得该框架适用于构建、配置和评估复杂的基于代理的工作流。

## 核心特性

- **模块化架构**：采用 pydantic-ai 和 pydantic-graph 构建，支持灵活的代理编排
- **YAML 配置驱动**：通过简单的 YAML 文件定义多轮对话场景、模型、代理和工作流
- **多轮对话支持**：支持复杂的多智能体交互场景，包括路由器和条件跳转
- **自动评估**：基于 LLM-as-Judge 的自动评估系统，支持多维度评分
- **MCP 集成**：支持 Model Context Protocol (MCP) 服务器，扩展代理能力
- **可视化分析**：内置雷达图和堆叠柱状图生成，直观展示评估结果
- **工作流可视化**：自动生成 Mermaid 流程图，展示代理交互流程

## 技术栈

- **Python 3.10+**
- **pydantic-ai**：用于构建和管理 AI 代理
- **pydantic-graph**：用于定义和执行图工作流
- **pydantic-evals**：用于 LLM-as-Judge 评估
- **Click**：用于构建 CLI 工具
- **Matplotlib**：用于数据可视化
- **FastMCP**：用于 MCP 服务器集成

## 安装

```bash
# 使用 uv 安装依赖
uv sync

# 或者使用 pip
pip install -e .
```

可选的 OpenAI 支持：

```bash
uv add --dev openai
```

## 快速开始

### 1. 配置环境

创建配置文件 `config.yaml`，参考 `config.yaml.example`：

```yaml
globals:
  concurrency: 16
  recursion_limit: 3
  output_dir: "./generated"

models:
  teacher_model:
    type: openai
    api_key: <YOUR_API_KEY>
    base_url: <YOUR_BASE_URL>
    model: gpt-4o

agents:
  teacher:
    model: teacher_model
    system_prompt: "你是一位耐心的老师..."

directions:
  - START -> teacher
  - teacher -> END

tasks:
  start_prompt: "教学主题: {topic}"
  mode: union
  content:
    topic:
      - "数学"
      - "物理"

evaluation:
  name: teaching_quality
  judge_model: teacher_model
  target: gpt-4o
  fields:
    - name: clarity
      rubric: 教学内容是否清晰易懂
      reason: true
```

### 2. 生成对话

```bash
elmes generate --config config.yaml
```

### 3. 评估结果

```bash
elmes eval --config config.yaml
```

### 4. 可视化结果

```bash
elmes visualize ./generated
```

## CLI 命令

### `generate` - 生成对话

生成基于配置的多轮对话数据。

```bash
elmes generate --config config.yaml --output ./results --debug
```

**选项：**

- `--config`：配置文件路径（默认：config.yaml）
- `--output`：输出目录（默认使用 globals.output_dir）
- `--debug`：启用调试模式

### `eval` - 评估对话

使用 LLM-as-Judge 评估生成的对话质量。

```bash
elmes eval --config config.yaml --input ./generated --output ./eval_results
```

**选项：**

- `--config`：配置文件路径（必需）
- `--input`：生成结果目录（默认自动推断）
- `--output`：评估结果输出目录
- `--avg/--no-avg`：是否计算平均分（默认：启用）
- `--include-reasons/--no-include-reasons`：是否包含评分理由（默认：启用）
- `--debug`：启用调试模式

### `export` - 导出数据

将对话数据导出为不同格式。

```bash
# 导出为 JSON
elmes export json --input ./generated --output ./exported.json

# 导出为 Label Studio 格式
elmes export label-studio --input ./generated --output ./label_studio.json
```

### `visualize` - 可视化评估结果

从 CSV 文件生成堆叠柱状图和雷达图。

```bash
elmes visualize ./generated --x-rotation 30
```

**参数：**

- `input_dir`：包含 CSV 文件的目录
- `--x-rotation`：X 轴标签旋转角度（默认：30）

### `draw` - 绘制工作流图

根据配置生成代理工作流图。

```bash
elmes draw --config config.yaml --output workflow.png
```

**选项：**

- `--config`：配置文件路径
- `--output`：输出文件路径（支持 .png 或 .mmd）
- `--print`：在控制台打印 Mermaid 代码
- `--direction`：图表方向（TB/LR/RL/BT，默认：LR）

### `hash` - 计算配置哈希

计算配置文件的 MD5 哈希值，用于确定结果子目录名称。

```bash
elmes hash --config config.yaml
```

## 配置说明

### 全局配置 (globals)

```yaml
globals:
  concurrency: 16 # 并发任务数
  recursion_limit: 3 # 最大递归调用次数
  output_dir: "./generated" # 结果输出目录
```

### 模型配置 (models)

```yaml
models:
  model_alias:
    type: openai
    api_key: <API_KEY>
    base_url: <BASE_URL>
    model: gpt-4o
    kargs:
      temperature: 0.7
```

### 代理配置 (agents)

```yaml
agents:
  agent_name:
    model: model_alias
    system_prompt: "提示词内容"
    memory:
      enable: true
      keep_turns: 3
    tools:
      - calculator # MCP 工具名称
```

### 路由配置 (directions)

```yaml
directions:
  - START -> teacher
  - teacher -> router:any_keyword_router(keywords=["<end>"], exists_to=END, else_to="student")
  - student -> teacher
```

支持的路由器：

- `any_keyword_router`：关键词匹配路由

### 任务配置 (tasks)

```yaml
tasks:
  start_prompt: "初始提示词 {variable}"
  mode: union # 或 iter
  content:
    variable:
      - "值1"
      - "值2"
```

- `union` 模式：所有字段排列组合生成任务
- `iter` 模式：逐条遍历内容

### 评估配置 (evaluation)

```yaml
evaluation:
  name: eval_name
  judge_model: model_alias
  target: target_name
  fields:
    - name: dimension_name
      rubric: 评分细则描述
      reason: true # 是否生成评分理由
```

### MCP 配置 (mcps)

```yaml
mcps:
  tool_name:
    type: stdio # stdio / http-with-sse / streamable-http
    command: "python"
    args: ["script.py"]
    timeout: 30
    env:
      KEY: "value"
```

## 项目结构

```
elmes/
├── src/elmes/
│   ├── cli/           # CLI 命令实现
│   │   ├── generate/  # 生成对话
│   │   ├── eval/      # 评估对话
│   │   ├── export/    # 导出数据
│   │   ├── visualize/ # 可视化
│   │   ├── draw/      # 绘制工作流
│   │   └── hash_/     # 计算哈希
│   ├── config/        # 配置模型（Pydantic）
│   ├── graph/         # 图工作流实现
│   ├── agent/         # 代理构建器
│   ├── model/         # 模型提供商
│   └── mcp/           # MCP 服务器集成
├── example/           # 示例配置
├── tests/             # 测试文件
└── docs/              # 文档和资产
```
