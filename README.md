# elmes - 教育场景评测系统

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)


**E**ducation **L**anguage **M**odel **E**valuation **S**ystem (elmes) 是一个 Python 框架，旨在为LLM不同场景下的各种任务提供代理编排和自动评估的功能。它采用模块化架构，基于 YAML 配置，可扩展的实体使得该框架适用于构建、配置和评估复杂的基于代理的工作流。系统采用现代 Python 编程实践。

---

## 目录

- [概述](#概述)
- [安装](#🔧 安装与配置)
- [命令行接口](#命令行接口)
- [核心组件](#核心组件)
  - [配置管理](#配置管理)
  - [实体定义](#实体定义)
  - [评估框架](#评估框架)
- [扩展 elmes](#扩展-elmes)
---

## 概述

elmes 使用户能够通过灵活的 YAML 配置系统配置、管理和评估 AI 代理和工作流。应用的核心功能包括：

- **可配置组件**：描述代理、模型、任务、评估和工作流方向。
- **动态评估与工具**：允许将结果导出并通过工具和数据库进行操作。
- **模块化、可扩展的实体**：便于快速原型设计和新评估策略的实验。
---

## 🔧 安装与配置

### 环境要求

- Python 3.10+
- 支持OpenAI、Anthropic等主流AI模型
- uv 包管理器（推荐）或 pip

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd elmes
```

2. **安装依赖**
```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

3. **配置教育场景**
```bash
cp config.yaml.example config.yaml
```

4. **设置AI模型**

编辑 `config.yaml` 文件，配置您的AI模型：

```yaml
models:
  math_teacher:
    type: openai
    api_key: your_openai_api_key
    api_base: https://api.openai.com/v1
    model: gpt-4o-mini
    kargs:
      temperature: 0.7
```


---

## 命令行接口

elmes 提供了一个方便的 CLI 工具，定义在 `pyproject.toml` 中：
```toml
[project.scripts]
elmes = "elmes.cli:main"
```

CLI 功能包括：

- `generate(config: str, debug: bool)`：根据 YAML 配置文件初始化并运行工作流。
- `export_json(input_dir: str, debug: bool)`：导出生成结果为 JSON 格式。
- `eval(config: str, debug: bool)`：评估生成结果。导出JSON及CSV
- `pipeline(config: str, debug: bool)`：执行上述所有步骤。

例如使用方式：
```bash
elmes generate --config config.yaml --debug
elmes export_json --input_dir input_dir --debug
elmes eval --config config.yaml --debug 
elmes pipeline --config config.yaml --debug 
```

---

## 核心组件

### 实体定义

实体（`src/elmes/entity.py`）为系统的主要概念提供了强类型和模块化支持。关键实体包括：

- **ElmesConfig**：根配置，封装所有工作流、任务、代理、模型和评估配置。

    ```python
    class ElmesConfig(BaseModel):
        globals: GlobalConfig
        models: Dict[str, ModelConfig]
        agents: Dict[str, AgentConfig]
        directions: List[str]
        tasks: TaskConfig
        evaluation: Optional[EvalConfig] = None
        context: ElmesContext = ElmesContext(conns=[])
    ```

- **EvalConfig**：描述如何执行评估，支持动态模式生成和多种评估方式。

    ```python
    class EvalConfig(BaseModel):
        model: str
        prompt: List[Prompt]
        format: List[FormatField]
        format_mode: Literal["tool", "prompt"] = "tool"
        def format_to_json_schema(self) -> str: ...
        def get_prompts(self) -> Tuple[str, List[Prompt]]: ...
        def format_to_pydantic(self) -> BaseModel: ...
    ```

### 评估框架

评估工具包封装在 `src/elmes/evaluation.py` 中。核心功能 `generate_evaluation_tool` 动态构建用于处理和存储评估结果的工具。

- **动态工具生成**：使用当前评估配置，在运行时定义工具模式，支持可扩展的评估格式。
- **持久化支持**：设计为序列化评估结果（作为 Pydantic 模型），并将其保存到数据库或存储后端（默认逻辑可以扩展以支持其他后端）。

评估工具示例：

```python
def generate_evaluation_tool() -> BaseTool:
    ...
    @tool(
        name_or_callable="save_result_to_database",
        description="Save the evaluation results to a database.",
        return_direct=True,
        args_schema=CONFIG.evaluation.format_to_pydantic(),
    )
    def save_to_db(**kwargs):
        ...
        return kwargs

    return save_to_db
```

---

## 扩展 elmes

- **添加新代理或模型类型**：通过扩展实体类并更新 YAML 配置。
- **集成新评估格式**：通过 `EvalConfig` 模式和工具生成实用程序。
- **自定义工作流**：编辑配置文件，并根据需要组合代理和工作流。

