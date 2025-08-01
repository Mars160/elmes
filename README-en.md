[简体中文](./README.md) | [English](./README-en.md)

[Paper][https://arxiv.org/abs/2507.22947]

# ELMES - Evaluating Large Language Models in Educational Scenarios

ELMES (Evaluating Large Language Models in Educational Scenarios) is a Python framework designed to provide agent orchestration and automated evaluation for various tasks in different LLM scenarios. It features a modular architecture, YAML-based configuration, and extensible entities, making it suitable for building, configuring, and evaluating complex agent-based workflows.

## Main Features

- **Modular Architecture**: A flexible agent orchestration system built on LangGraph.
- **YAML-based Configuration**: Simple and intuitive task and workflow definitions with support for variable template rendering.
- **Multi-Agent Collaboration**: Supports interaction and collaboration between multiple LLM agents, with complex flow control achievable through routers.
- **Automated Evaluation**: Built-in evaluation framework supporting both JSON Schema and tool (function calling) output modes.
- **Memory Management and Persistence**: Conversation history is persisted via SQLite checkpoints, ensuring long-running tasks are not interrupted.
- **Concurrency and Retry Mechanisms**: Built-in concurrent execution (`concurrency`) and configurable Tenacity retry strategies.
- **Visualized Flowcharts**: Visualize agent interaction flows with the `draw` command for an intuitive representation of workflow design.

## Installation

```bash
pip install elmes
```

## Quick Start

1. Create a configuration file `config.yaml` (you can refer to `config.yaml.example`).
2. Run the ELMES command-line tool.

```bash
elmes pipeline --config config.yaml
```

## Configuration Example

ELMES uses YAML configuration files to define tasks, agents, and evaluation methods. Below is a simplified configuration example:

```yaml
# Global configuration
globals:
  concurrency: 16
  recursion_limit: 50
  retry:
    attempt: 3
    interval: 3
  memory:
    path: ./logs/my_exp

# Define models
models:
  gpt4o:
    type: openai
    api_key: ${OPENAI_KEY}
    api_base: https://api.openai.com/v1
    model: gpt-4o-mini
    kargs:
      temperature: 0.7

# Define agents
agents:
  teacher:
    model: gpt4o
    prompt:
      - role: system
        content: "You are a math teacher, student profile: {image}"
      - role: user
        content: "{question}"
    memory:
      enable: true
      keep_turns: 3

# Define information flow between agents
directions:
  - START -> teacher
  - teacher -> router:any_keyword_route(keywords=["<end>", "class dismissed"], exists_to=END, else_to="student")
  - student -> teacher

# Define task content
tasks:
  mode: union
  start_prompt:
    role: user
    content: "{question}"
  content:
    image:
      - "Strong logical thinking, loves science"
    question:
      - "A three-digit number..."
      - "A master and apprentice assemble a bicycle..."

# Evaluation configuration
evaluation:
  name: math_tutor_eval
  model: gpt4o
  format_mode: prompt
  prompt:
    - role: system
      content: "You are a professional evaluation expert..."
  format:
    - field: accuracy
      type: float
      description: "Accuracy"
    - field: guidance
      type: dict
      description: "Guidance"
      items:
        - field: score
          type: float
          description: "Score"
        - field: reason
          type: str
          description: "Reason"
```

## Core Components

ELMES consists of the following core components:

1.  **Agent System**: An agent orchestration framework built on LangGraph.
2.  **Routing System**: Controls the flow of information and interaction between agents.
3.  **Configuration System**: Processes YAML configuration files and builds the corresponding entities.
4.  **Evaluation System**: Automatically evaluates agent performance.
5.  **Memory System**: Manages agent conversation history and context.

## Advanced Usage

### Custom Routers

ELMES supports custom routing logic to control the interaction flow between agents:

```yaml
directions:
  - teacher -> router:any_keyword_route(keywords=["<end>", "class dismissed"], exists_to=END, else_to="student")
```

### Evaluation Formatting

ELMES supports multiple evaluation output formats, including structured JSON output:

```yaml
evaluation:
  format:
    - field: accuracy
      type: float
      description: "Accuracy score"
    - field: guidance
      type: dict
      description: "Guidance score"
      items:
        - field: score
          type: float
          description: "Score"
        - field: reason
          type: str
          description: "Reason for the score"
```

### Visualizing Agent Flows

ELMES provides a `draw` command that can render the agent interaction flow defined in the configuration file into a visual chart:

```bash
elmes draw --config config.yaml
```

This command generates a Mermaid flowchart based on the `directions` section in the configuration file and saves it as a PNG file (with the same name as the configuration file). This is particularly helpful for understanding complex agent interaction flows and debugging routing logic.

![Agent Flowchart Example](docs/assets/imgs/config.png)

## Contributing

Pull requests and issues are welcome to improve ELMES.

## Configuration File Explained

The following sections are based on `config.yaml.example` to help you quickly understand and customize your own tasks.

### 1. globals

```yaml
globals:
  concurrency: 16 # Number of concurrent coroutines, controlling overall throughput
  recursion_limit: 50 # LangGraph recursion depth limit to prevent infinite loops
  retry: # Tenacity retry strategy
    attempt: 3 # Maximum number of retries
    interval: 3 # Interval between each retry (seconds)
  memory:
    path: ./logs/my_exp # Storage directory for all SQLite checkpoints
```

- **Concurrency** and **recursion depth** ensure task performance and safety.
- The **retry** field maps to Tenacity, automatically providing retries for each LLM call.
- **memory.path** determines the persistence location for conversation history and evaluation results.

### 2. models

```yaml
models:
  gpt4o:
    type: openai # Currently supports openai / anthropic / any future backend
    api_key: ${OPENAI_KEY}
    api_base: https://api.openai.com/v1
    model: gpt-4o-mini
    kargs: # Any keyword arguments to be passed to the SDK
      temperature: 0.7
```

- One configuration block = one callable model.
- `kargs` will be passed through when calling `client.chat.completions.create(**kargs)`.

### 3. agents

```yaml
agents:
  teacher:
    model: gpt4o # Links to a key in `models`
    prompt: # Full OpenAI chat format prompt, supports variable placeholders
      - role: system
        content: "You are a math teacher, student profile: {image}"
      - role: user
        content: "{question}"
    memory: # Optional, overrides the global memory strategy individually
      enable: true
      keep_turns: 3 # Carries a maximum of 3 turns of context
```

- The prompt supports **placeholder templates**, which are dynamically filled by `tasks.content` at runtime.
- Each agent is ultimately wrapped into a LangGraph **node**, with retry and memory logic automatically injected.

### 4. directions

```yaml
directions:
  - START -> teacher
  - teacher -> router:any_keyword_route(keywords=["<end>", "class dismissed"], exists_to=END, else_to="student")
  - student -> teacher
```

- Arrows are used to chain nodes, describing the **directed edges** in the LangGraph.
- Use the `router:` prefix to call any Python function for conditional branching; in the example, `any_keyword_route` determines whether the flow ends based on keywords.

### 5. tasks

```yaml
tasks:
  mode: union # union=Cartesian product combination, iter=sequential iteration
  start_prompt: # Optional, defines the first message sent from START
    role: user
    content: "{question}"
  content:
    image:
      - "Strong logical thinking, loves science"
    question:
      - "A three-digit number..."
      - "A master and apprentice assemble a bicycle..."
```

- `mode: union` means that `image × question` will form multiple tasks and be executed concurrently.
- Variables will be replaced **one-to-one** into the agent and evaluation prompts.

### 6. evaluation (optional)

```yaml
evaluation:
  name: math_tutor_eval
  model: gpt4o # Model used for scoring
  format_mode: prompt # prompt or tool modes
  prompt:
    - role: system
      content: "You are a professional evaluation expert..."
  format:
    - field: accuracy
      type: float
      description: "Accuracy"
    - field: guidance
      type: dict
      description: "Guidance"
      items:
        - field: score
          type: float
          description: "Score"
        - field: reason
          type: str
          description: "Reason"
```

- **tool mode**: Utilizes OpenAI function-calling to ensure the output JSON is 100% valid.
- **prompt mode**: Compatible with models or providers that do not support function-calling, through strict placeholders and regular expression extraction.

> If the `evaluation` block is omitted, ELMES will only execute the tasks and skip the evaluation phase.

### 7. Command-Line Tools

ELMES provides several command-line tools for users to perform different operations:

```bash
# Generate conversations
elmes generate --config config.yaml

# Export conversations to JSON
elmes export json --config config.yaml

# Export Label Studio data
elmes export label-studio --config config.yaml

# Evaluate conversation results
elmes eval --config config.yaml

# Full pipeline (generate + export JSON + evaluate, a 3-in-1 command)
elmes pipeline --config config.yaml

# Visualize evaluation results
elmes visualize eval/

# Draw Agent flowchart
elmes draw --config config.yaml
```

---

You can find our documentation for the four teaching scenarios [here](docs/scenes/en/).
