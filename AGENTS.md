# AGENTS.md - Coding Guidelines for ELMES

Guidelines for AI agents working on the ELMES (Education Language Model Evaluation System) codebase.

## Project Overview

ELMES is a Python framework for agent orchestration and automated LLM evaluation in educational scenarios. Uses: **LangGraph** (orchestration), **Pydantic** (data modeling), **Click** (CLI), **YAML** (configuration), **UV** (package management).

## Build/Lint/Test Commands

```bash
# Package Management
uv sync                              # Install dependencies
uv sync --group dev                  # Install with dev dependencies
uv add <package>                     # Add dependency

# Build & Install
uv build                             # Build package
uv pip install -e .                  # Editable install

# Running the Application
elmes pipeline --config config.yaml  # Full pipeline (generate+export+eval)
elmes generate --config config.yaml  # Generate conversations
elmes eval --config config.yaml      # Evaluate results
elmes draw --config config.yaml      # Visualize workflow

# Testing
pytest                               # Run all tests
pytest tests/test_file.py            # Run single test file
pytest tests/test_file.py::test_name # Run single test

# Linting & Type Checking
ruff format .                        # Format code
ruff check .                         # Check linting
ruff check --fix .                   # Fix errors
pyright                              # Type checking
```

## Code Style Guidelines

### Import Ordering
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
import json
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel
from langchain.chat_models.base import BaseChatModel

from elmes.entity import AgentConfig
from elmes.config import CONFIG
```

### Type Hints
- Use type hints for all function parameters and return types
- Use `Optional[Type]` instead of `Type | None` (consistent with existing code)
- Use `Dict`, `List`, `Tuple` from `typing` module

```python
def process_data(data: Dict[str, Any]) -> Optional[str]:
    ...
```

### Naming Conventions
- **Modules/Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

```python
MAX_RETRY_COUNT = 3

class AgentConfig(BaseModel):
    model_name: str

def init_agent_map() -> Dict[str, Any]:
    return {}
```

### Error Handling
- Use specific exceptions (`ValueError`, `NotImplementedError`)
- Include descriptive error messages
- Use `tenacity` for retry logic on external API calls

```python
if not data:
    raise ValueError("Configuration data cannot be empty")

from tenacity import retry, stop_after_attempt, wait_fixed

@retry(
    stop=stop_after_attempt(CONFIG.globals.retry.attempt),
    wait=wait_fixed(CONFIG.globals.retry.interval),
)
async def api_call():
    ...
```

### Comments & Docstrings
- Use English for all code comments and docstrings
- Use docstrings for public functions and classes

```python
def evaluate_model(data: ExportFormat) -> Dict[str, Any]:
    """Evaluate a model's performance on a given task.
    
    Args:
        data: The exported conversation data to evaluate.
        
    Returns:
        A dictionary containing evaluation scores.
    """
    ...
```

### Async Patterns
- Use `async`/`await` for I/O-bound operations
- Use `asyncio.Semaphore` for concurrency control
- Use `tqdm.asyncio` for progress bars in async loops

```python
async def process_tasks(files: List[Path]):
    sem = asyncio.Semaphore(CONFIG.globals.concurrency)
    
    async def process_one(file: Path):
        async with sem:
            return await process_file(file)
    
    tasks = [process_one(f) for f in files]
    results = await tqdm.gather(*tasks)
    return results
```

### Pydantic Models
- Use `BaseModel` for all configuration and data classes
- Use `ConfigDict(arbitrary_types_allowed=True)` when needed
- Use `Final` for immutable fields
- Use `Optional` with default values

```python
from pydantic import BaseModel, ConfigDict
from typing import Final, Optional

class AgentConfig(BaseModel):
    model: str
    prompt: Final[List[Prompt]]
    memory: AgentMemoryConfig = AgentMemoryConfig(enable=True)
    
class ElmesContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    conns: List[Connection] = []
```

### CLI Commands
- Use `@click.command()` decorator
- Use type hints with `click.Path`, `click.Option`
- Use `set_debug()` for langchain debug mode
- Load config at the start of each command

```python
import click
from pathlib import Path

@click.command(help="Description of what this command does")
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to the configuration file"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def my_command(config: Path, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf
    load_conf(config)
    # Command logic
```

### File Structure
- CLI commands: `src/elmes/cli/<command>/__init__.py`
- Exporters: `src/elmes/cli/export/exporter/`
- Utilities: `src/elmes/`
- Assets: `assets/`

### Configuration
- Use YAML for user-facing configuration
- Use Pydantic models for internal config representation
- Support environment variable substitution (e.g., `${OPENAI_KEY}`)
- Store runtime data in SQLite databases

## Important Notes

- **Python Version**: Requires Python >= 3.10
- **Package Manager**: Use UV, not pip directly
- **Build Tool**: Hatchling (configured in pyproject.toml)
- **Entry Point**: `elmes` command defined in `src/elmes/cli/main.py`
- **No Pre-commit Hooks**: Currently no automated pre-commit checks configured
- **Tests**: No test directory currently present in the repo
