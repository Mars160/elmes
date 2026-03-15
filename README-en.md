[简体中文](./README.md) | [English](./README-en.md)

[Paper](https://arxiv.org/abs/2507.22947)

<p align="center">
  <img src="./docs/assets/icons/elmes-logo.svg" alt="ELMES Logo" width="120" height="120">
</p>

<h1 align="center">ELMES - Evaluating Large Language Models in Educational Scenarios</h1>

ELMES (Evaluating Large Language Models in Educational Scenarios) is a Python framework designed to provide agent orchestration and automatic evaluation capabilities for LLMs across various scenarios and tasks. It adopts a modular architecture based on YAML configuration, with extensible entities making the framework suitable for building, configuring, and evaluating complex agent-based workflows.

## Core Features

- **Modular Architecture**: Built with pydantic-ai and pydantic-graph, supporting flexible agent orchestration
- **YAML Configuration-Driven**: Define multi-turn dialogue scenarios, models, agents, and workflows through simple YAML files
- **Multi-Turn Dialogue Support**: Supports complex multi-agent interaction scenarios, including routers and conditional jumps
- **Automatic Evaluation**: LLM-as-Judge based automatic evaluation system with multi-dimensional scoring
- **MCP Integration**: Supports Model Context Protocol (MCP) servers to extend agent capabilities
- **Visualization Analysis**: Built-in radar chart and stacked bar chart generation for intuitive evaluation results display
- **Workflow Visualization**: Automatically generates Mermaid flowcharts to display agent interaction flows

## Tech Stack

- **Python 3.10+**
- **pydantic-ai**: For building and managing AI agents
- **pydantic-graph**: For defining and executing graph workflows
- **pydantic-evals**: For LLM-as-Judge evaluation
- **Click**: For building CLI tools
- **Matplotlib**: For data visualization
- **FastMCP**: For MCP server integration

## Installation

```bash
# Install dependencies using uv
uv sync

# Or using pip
pip install -e .
```

Optional OpenAI support:

```bash
uv add --dev openai
```

## Quick Start

### 1. Configuration

Create a configuration file `config.yaml`, refer to `config.yaml.example`:

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
    system_prompt: "You are a patient teacher..."

directions:
  - START -> teacher
  - teacher -> END

tasks:
  start_prompt: "Teaching topic: {topic}"
  mode: union
  content:
    topic:
      - "Mathematics"
      - "Physics"

evaluation:
  name: teaching_quality
  judge_model: teacher_model
  target: gpt-4o
  fields:
    - name: clarity
      rubric: Whether the teaching content is clear and easy to understand
      reason: true
```

### 2. Generate Conversations

```bash
elmes generate --config config.yaml
```

### 3. Evaluate Results

```bash
elmes eval --config config.yaml
```

### 4. Visualize Results

```bash
elmes visualize ./generated
```

## CLI Commands

### `generate` - Generate Conversations

Generate multi-turn dialogue data based on configuration.

```bash
elmes generate --config config.yaml --output ./results --debug
```

**Options:**

- `--config`: Configuration file path (default: config.yaml)
- `--output`: Output directory (defaults to globals.output_dir)
- `--debug`: Enable debug mode

### `eval` - Evaluate Conversations

Evaluate generated conversation quality using LLM-as-Judge.

```bash
elmes eval --config config.yaml --input ./generated --output ./eval_results
```

**Options:**

- `--config`: Configuration file path (required)
- `--input`: Generation result directory (auto-inferred by default)
- `--output`: Evaluation result output directory
- `--avg/--no-avg`: Whether to calculate average score (default: enabled)
- `--include-reasons/--no-include-reasons`: Whether to include scoring reasons (default: enabled)
- `--debug`: Enable debug mode

### `export` - Export Data

Export conversation data in different formats.

```bash
# Export as JSON
elmes export json --input ./generated --output ./exported.json

# Export as Label Studio format
elmes export label-studio --input ./generated --output ./label_studio.json
```

### `visualize` - Visualize Evaluation Results

Generate stacked bar charts and radar charts from CSV files.

```bash
elmes visualize ./generated --x-rotation 30
```

**Arguments:**

- `input_dir`: Directory containing CSV files
- `--x-rotation`: X-axis label rotation angle (default: 30)

### `draw` - Draw Workflow Diagram

Generate agent workflow diagram based on configuration.

```bash
elmes draw --config config.yaml --output workflow.png
```

**Options:**

- `--config`: Configuration file path
- `--output`: Output file path (supports .png or .mmd)
- `--print`: Print Mermaid code to console
- `--direction`: Diagram direction (TB/LR/RL/BT, default: LR)

### `hash` - Calculate Config Hash

Calculate MD5 hash of the configuration file, used to determine result subdirectory name.

```bash
elmes hash --config config.yaml
```

## Configuration Guide

### Global Configuration (globals)

```yaml
globals:
  concurrency: 16           # Number of concurrent tasks
  recursion_limit: 3        # Maximum recursion call limit
  output_dir: "./generated" # Result output directory
```

### Model Configuration (models)

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

### Agent Configuration (agents)

```yaml
agents:
  agent_name:
    model: model_alias
    system_prompt: "Prompt content"
    memory:
      enable: true
      keep_turns: 3
    tools:
      - calculator  # MCP tool name
```

### Routing Configuration (directions)

```yaml
directions:
  - START -> teacher
  - teacher -> router:any_keyword_router(keywords=["<end>"], exists_to=END, else_to="student")
  - student -> teacher
```

Supported routers:

- `any_keyword_router`: Keyword matching router

### Task Configuration (tasks)

```yaml
tasks:
  start_prompt: "Initial prompt {variable}"
  mode: union  # or iter
  content:
    variable:
      - "value1"
      - "value2"
```

- `union` mode: Generate tasks by combining all fields
- `iter` mode: Iterate through content items

### Evaluation Configuration (evaluation)

```yaml
evaluation:
  name: eval_name
  judge_model: model_alias
  target: target_name
  fields:
    - name: dimension_name
      rubric: Scoring rubric description
      reason: true  # Whether to generate scoring reasons
```

### MCP Configuration (mcps)

```yaml
mcps:
  tool_name:
    type: stdio  # stdio / http-with-sse / streamable-http
    command: "python"
    args: ["script.py"]
    timeout: 30
    env:
      KEY: "value"
```

## Project Structure

```
elmes/
├── src/elmes/
│   ├── cli/           # CLI command implementations
│   │   ├── generate/  # Generate conversations
│   │   ├── eval/      # Evaluate conversations
│   │   ├── export/    # Export data
│   │   ├── visualize/ # Visualization
│   │   ├── draw/      # Draw workflow
│   │   └── hash_/     # Calculate hash
│   ├── config/        # Configuration models (Pydantic)
│   ├── graph/         # Graph workflow implementation
│   ├── agent/         # Agent builders
│   ├── model/         # Model providers
│   └── mcp/           # MCP server integration
├── example/           # Example configurations
├── tests/             # Test files
└── docs/              # Documentation and assets
```

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Citation

If you use ELMES in your research, please cite:

```bibtex
@article{elmes2025,
  title={ELMES: Evaluating Large Language Models in Educational Scenarios},
  author={...},
  journal={arXiv preprint},
  year={2025}
}
```
