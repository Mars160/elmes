# AGENTS.md - Coding Guidelines for ELMES

## Project Overview
ELMES (Education Language Model Evaluation System) - A Python CLI tool for evaluating language models in educational contexts using pydantic-ai and graph-based workflows.

## Build/Lint/Test Commands

### Package Management (uv)
```bash
# Install dependencies
uv sync

# Add dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Run commands in venv
uv run <command>
```

### Code Quality (ruff)
```bash
# Format all files
uv run ruff format .

# Check linting
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix

# Check specific file
uv run ruff check src/elmes/cli/main.py
```

### Testing (pytest)
```bash
# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_config.py

# Run single test function
uv run pytest tests/test_config.py::test_load_config

# Run with verbose output
uv run pytest -v

# Run specific test class
uv run pytest tests/test_graph.py::TestGraphNodes
```

### CLI Commands
```bash
# Run CLI
uv run elmes --help

# Generate conversations
uv run elmes generate --config config.yaml

# Evaluate results
uv run elmes eval --config config.yaml

# Export data
uv run elmes export --format json
```

## Code Style Guidelines

### Python Version
- Python 3.12+
- Use modern syntax (union types with `|`, pattern matching, etc.)

### Imports
- Group imports: stdlib → third-party → local
- Use absolute imports for local modules: `from elmes.config import Model`
- Avoid relative imports (e.g., `from .config import Model`)
- Import typing modules: `from __future__ import annotations` (optional for 3.12+)

### Formatting
- Line length: 88 characters (Black-compatible)
- Use double quotes for strings
- Trailing commas in multi-line structures
- 4 spaces indentation

### Type Hints
- Use type hints for function parameters and return types
- Use `| None` instead of `Optional[T]`
- Use `dict[str, T]` instead of `Dict[str, T]`
- Complex types: `list[str]`, `dict[str, Any]`, `type[BaseNode]`

### Naming Conventions
- Classes: PascalCase (e.g., `GraphState`, `AgentNode`)
- Functions/variables: snake_case (e.g., `load_config`, `task_idx`)
- Constants: UPPER_SNAKE_CASE (module-level)
- Private: _leading_underscore (e.g., `_build_run_dir`)
- Type variables: PascalCase with descriptive names

### Documentation
- Use triple-quoted docstrings for modules, classes, functions
- Follow Google/NumPy style (concise descriptions)
- Include type info in docstrings for complex params

### Error Handling
- Use assertions for internal logic validation
- Raise `ValueError` for invalid configurations
- Log errors with `click.echo(..., err=True)` in CLI context
- Catch exceptions at task level to prevent total failure

### Pydantic Models
- Use `BaseModel` for configuration classes
- Use `Field(..., description="...")` for documentation
- Use `default_factory=dict` for mutable defaults

### Async Patterns
- Use `asyncio.run()` at entry points
- Use `async/await` consistently
- Handle concurrent execution with `asyncio.gather()` or `tqdm.gather()`

### CLI Development
- Use Click for CLI commands
- Use `@click.command()` and `@click.option()` decorators
- Group related commands using `click.group()`

## Project Structure
```
src/elmes/
├── cli/           # Click CLI commands
├── config/        # Pydantic configuration models
├── graph/         # Pydantic-graph nodes and state
├── agent/         # Agent builders
├── model/         # LLM provider builders
└── mcp/           # MCP server integration
```
