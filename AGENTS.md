# AGENTS.md - Coding Guidelines for ELMES

## Build/Lint/Test Commands

```bash
# Install dependencies (using uv)
uv sync

# Run linting and formatting (using ruff)
uv run ruff check src/
uv run ruff format src/

# Run linting with auto-fix
uv run ruff check src/ --fix

# Run a single test file (when tests exist)
uv run pytest tests/test_specific.py -v

# Run a single test function
uv run pytest tests/test_specific.py::test_function_name -v

# Run all tests
uv run pytest tests/ -v

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
- Add `from __future__ import annotations` for forward references

### Formatting
- Use **ruff** for linting and formatting
- Line length: follow default (88 chars)
- Use double quotes for strings
- Trailing commas in multi-line collections
- Two blank lines between top-level definitions
- One blank line between method definitions in a class

### Types
- Use Python 3.10+ type hints: `dict[str, PydanticAIModel]`, `list[dict[str, str]]`
- Use Pydantic `BaseModel` for configuration classes
- Function return types required for public APIs
- Use `|` union syntax: `str | None` (Python 3.10+)
- Use `Any` sparingly, prefer specific types
- Type all function parameters and return values

### Naming Conventions
- **Modules**: lowercase with underscores: `openai_provider.py`
- **Classes**: PascalCase: `Model`, `AgentConfig`
- **Functions/Variables**: snake_case: `build_model`, `model_config`
- **Constants**: UPPER_SNAKE_CASE
- **Private**: prefix with underscore: `_helper_function`
- **Type Variables**: PascalCase with suffix: `T`, `ModelT`

### Error Handling
- Use `ValueError` for invalid arguments/configurations
- Use `assert` for internal invariants and configuration validation
- Provide descriptive error messages (English for code, Chinese for user-facing)
- Raise exceptions early with context
- Use specific exception types, avoid bare `except:`
- Document exceptions in docstrings

### Documentation
- Use triple quotes for docstrings
- First line should be a brief description
- Include type information in docstrings for complex functions
- Use Chinese for user-facing documentation
- Use English for code comments and internal docs

### Testing
- Write tests for all new features
- Use pytest for testing
- Test file naming: `test_<module>.py`
- Test function naming: `test_<function_name>_<scenario>`
- Use fixtures for common setup
- Mock external dependencies

## Architecture Patterns

### Configuration-Driven Design
- YAML → Pydantic models → runtime objects
- Use Pydantic `BaseModel` for all config classes
- Support variable template rendering in config
- Validate configurations at load time

### Factory Pattern
- Factory pattern for building models/agents: `build_model()`, `build_agent()`
- Factory functions should accept config objects and return runtime instances
- Keep factory logic separate from business logic

### Graph-Based Workflows
- Use pydantic-graph for workflow orchestration
- Nodes should be stateless and reusable
- State management through GraphState
- Support router patterns for conditional flows

### CLI Design
- CLI uses Click with command groups
- Each command group in separate module
- Use decorators for common options
- Provide helpful help text

### MCP Servers
- MCP servers for tool integration
- Support multiple MCP server types
- Lazy initialization of MCP connections

## Project Structure

```
src/elmes/
├── __init__.py
├── cli/           # Click CLI commands
│   ├── main.py    # Entry point with command groups
│   ├── generate/  # Generation commands
│   ├── eval/      # Evaluation commands
│   ├── visualize/ # Visualization commands
│   ├── draw/      # Drawing commands
│   ├── export/    # Export commands
│   └── hash_/     # Hash utilities
├── config/        # Pydantic config models
│   ├── __init__.py
│   ├── models.py  # Model configurations
│   ├── agents.py  # Agent configurations
│   ├── tasks.py   # Task configurations
│   ├── mcps.py    # MCP configurations
│   ├── eval.py    # Evaluation configurations
│   ├── directions.py  # Direction configurations
│   └── globals.py # Global configurations
├── agent/         # Agent building logic
│   └── __init__.py
├── model/         # Model provider implementations
│   └── openai_provider.py
├── mcp/           # MCP server handling
│   └── __init__.py
└── graph/         # Workflow graph definitions
    ├── __init__.py
    ├── builder.py # Graph construction
    ├── nodes.py   # Node definitions
    ├── state.py   # Graph state
    └── router/    # Routing logic
```

## Dependencies

### Runtime Dependencies
- `pydantic-ai-slim[mcp]` - AI agent framework with MCP support
- `pydantic-graph` - Graph-based workflow orchestration
- `pydantic-evals` - Evaluation framework
- `click` - CLI framework
- `pydantic` - Data validation
- `pyyaml` - YAML parsing
- `pandas` - Data manipulation
- `matplotlib` - Visualization
- `diskcache` - Caching
- `tenacity` - Retry logic
- `polyfactory` - Test data generation

### Optional Dependencies
- `openai` - OpenAI API support (via `pip install elmes[openai]`)

### Development Dependencies
- `hatch` - Build tool
- `fastmcp` - MCP development

### Package Management
- Package manager: `uv`
- Virtual environment: `.venv/`
- Lock file: `uv.lock`

## Python Version
- Python 3.12 required (see `.python-version`)
- Use Python 3.10+ features (union types with `|`, match statements)
- Avoid deprecated features from older Python versions

## Git Workflow
- Use conventional commits
- Branch naming: `feature/`, `fix/`, `docs/`, `refactor/`
- Keep commits focused and atomic
- Write descriptive commit messages
- Review code before merging

## Best Practices
- Keep functions small and focused (under 50 lines)
- Avoid deep nesting (max 3 levels)
- Use early returns to reduce nesting
- Prefer composition over inheritance
- Keep modules focused on single responsibility
- Use dependency injection for testability
- Cache expensive operations appropriately
- Handle async/await properly in graph nodes
- Validate inputs at boundaries
- Log important operations for debugging
