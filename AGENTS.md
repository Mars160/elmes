# AGENTS.md - Coding Guidelines for ELMES

## Build/Lint/Test Commands

```bash
# Install dependencies (using uv)
uv sync

# Run linting and formatting (using ruff)
uv run ruff check src/
uv run ruff format src/

# Run a single test file (when tests exist)
uv run pytest tests/test_specific.py -v

# Run a single test function
uv run pytest tests/test_specific.py::test_function_name -v

# Build the package
uv run hatch build

# Install in development mode
uv pip install -e .

# Run the CLI
uv run elmes --help
uv run elmes pipeline --config config.yaml
```

## Code Style Guidelines

### Imports
- Group imports: stdlib → third-party → local
- Use absolute imports for project modules: `from elmes.config import Model`
- Use type hint imports from `typing`: `dict[str, str]`, `list[dict]`
- Avoid `from module import *`

### Formatting
- Use **ruff** for linting and formatting
- Line length: follow default (88 chars)
- Use double quotes for strings
- Trailing commas in multi-line collections

### Types
- Use Python 3.10+ type hints: `dict[str, PydanticAIModel]`, `list[dict[str, str]]`
- Use Pydantic `BaseModel` for configuration classes
- Function return types required for public APIs
- Use `|` union syntax: `str | None` (Python 3.10+)

### Naming Conventions
- **Modules**: lowercase with underscores: `openai_provider.py`
- **Classes**: PascalCase: `Model`, `AgentConfig`
- **Functions/Variables**: snake_case: `build_model`, `model_config`
- **Constants**: UPPER_SNAKE_CASE
- **Private**: prefix with underscore: `_helper_function`

### Error Handling
- Use `ValueError` for invalid arguments/configurations
- Use `assert` for internal invariants and configuration validation
- Provide descriptive error messages (English for code, Chinese for user-facing)
- Raise exceptions early with context

### Architecture Patterns
- Configuration-driven: YAML → Pydantic models → runtime objects
- Use Pydantic `BaseModel` for all config classes
- Factory pattern for building models/agents: `build_model()`, `build_agent()`
- CLI uses Click with command groups
- MCP servers for tool integration

### Project Structure
```
src/elmes/
├── __init__.py
├── cli/           # Click CLI commands
├── config/        # Pydantic config models
├── agent/         # Agent building logic
├── model/         # Model provider implementations
├── mcp/           # MCP server handling
└── graph/         # Workflow graph definitions
```

### Dependencies
- Runtime: `pydantic-ai`, `click`, `pydantic`, `pyyaml`
- Build: `hatchling`
- Package manager: `uv`

### Notes
- Python 3.10+ required (see `.python-version`)
- Virtual environment: `.venv/`
- Lock file: `uv.lock`
