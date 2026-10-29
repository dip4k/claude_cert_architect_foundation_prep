# Python Development Setup with uv

This guide explains how to set up and use Python development environment with `uv` for the Claude Certified Architect Foundation practice repository.

## What is uv?

`uv` is a fast Python package installer and resolver, written in Rust. It's a drop-in replacement for `pip` and `pip-tools` with significantly better performance.

**Benefits:**
- 🚀 10-100x faster than pip
- 📦 Simplified dependency management
- 🔒 Deterministic builds
- 🐍 Python version management
- 🎯 Virtual environment management

## Installation

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation
```bash
uv --version
```

## Project Setup

### 1. Clone/Navigate to Project
```bash
# From repository root:
```

### 2. Create Virtual Environment
```bash
# Create a new virtual environment
uv venv

# On Windows
uv venv .venv
.venv\Scripts\activate

# On macOS/Linux
uv venv
source .venv/bin/activate
```

### 3. Install Project with Dependencies
```bash
# Sync all dependencies for the unified workspace:
uv sync

# Or install manually with uv pip:
uv pip install -e ".[dev]"
```

### 4. Configure Environment Variables
```bash
# Copy the example environment template
cp .env.example .env

# Set your Anthropic API Key and preferences in .env:
# ANTHROPIC_API_KEY=sk-ant-...
# CLAUDE_MODEL=claude-haiku-4-5
# USE_UV=1
```

---

## 🏗️ Workspace Structure & Members

The repository uses a **unified UV workspace** declared in root `pyproject.toml`. All subprojects share the root `.venv`:

- **Root Project**: Contains core packages (`lib.sdk_parser_py`, `lib.response_logger`, `lib.mock_claude`), certification domain modules (`domain1` - `domain5`), and 6 production scenarios.
- **Workspace Member (`anthropic-api-practice/MCP/cli_project`)**: FastMCP server (`mcp_server.py`) and CLI chat client (`main.py`).

### Running MCP Practice Modules

```bash
# 1. Run MCP server with the interactive MCP Inspector UI (zero package re-downloads)
cd anthropic-api-practice/MCP/cli_project
npx @modelcontextprotocol/inspector ../../../.venv/Scripts/python.exe mcp_server.py

# 2. Run the interactive CLI chat app
uv run --no-sync main.py
```

## Common Development Tasks

### Running Examples

```bash
# Run all SDK parser examples
python lib/sdk_parser_py/examples.py

# Run specific example
python -c "from lib.sdk_parser_py.examples import basic_parsing; basic_parsing()"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lib/sdk_parser_py

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_basic_parsing

# Run tests matching pattern
pytest -k "parsing"

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Code Formatting

```bash
# Format all code
black lib/ tests/

# Format specific file
black lib/sdk_parser_py/parser.py

# Check without modifying
black --check lib/ tests/

# Sort imports
isort lib/ tests/
```

### Linting

```bash
# Lint with flake8
flake8 lib/ tests/

# Type checking with mypy
mypy lib/sdk_parser_py/

# Full lint check (black, isort, flake8, mypy)
black --check lib/ tests/
isort --check-only lib/ tests/
flake8 lib/ tests/
mypy lib/sdk_parser_py/
```

### Creating Tests

```bash
# Create tests directory if it doesn't exist
mkdir -p tests

# Create a test file
cat > tests/test_parser.py << 'TESTEOF'
from lib.sdk_parser_py import create_parser

def test_basic_parsing():
    """Test basic response parsing"""
    parser = create_parser()
    response = {
        "id": "test_123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello World"}],
        "model": "claude-sonnet-4-5",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    
    result = parser.parse(response)
    assert result.get("success")
    assert result.get("data").text == "Hello World"
    assert result.get("data").id == "test_123"

def test_tool_use_parsing():
    """Test parsing responses with tool use"""
    parser = create_parser()
    response = {
        "id": "test_456",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Calling tool..."},
            {
                "type": "tool_use",
                "id": "tool_1",
                "name": "search",
                "input": {"query": "test"},
            },
        ],
        "model": "claude-sonnet-4-5",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 50, "output_tokens": 100},
    }
    
    result = parser.parse(response)
    assert result.get("success")
    data = result.get("data")
    assert len(data.tool_uses) == 1
    assert data.tool_uses[0].name == "search"

def test_error_handling():
    """Test error handling for invalid responses"""
    parser = create_parser()
    invalid_response = {"id": "test"}  # Missing required fields
    
    result = parser.parse(invalid_response)
    assert not result.get("success")
    assert result.get("error") is not None
    assert result.get("error").code == "INVALID_RESPONSE"

if __name__ == "__main__":
    test_basic_parsing()
    test_tool_use_parsing()
    test_error_handling()
    print("✓ All tests passed!")
TESTEOF

# Run the test
pytest tests/test_parser.py
```

## UV Commands Reference

### Virtual Environment
```bash
uv venv [PATH]              # Create virtual environment
uv venv --python 3.11       # Create with specific Python version
uv venv --seed              # Include seed packages
uv venv --upgrade           # Upgrade existing venv
```

### Package Management
```bash
uv pip install PACKAGE      # Install package
uv pip install -e .         # Install current project
uv pip install -e ".[dev]"  # Install with optional dependencies
uv pip install -r requirements.txt  # Install from requirements
uv pip list                  # List installed packages
uv pip show PACKAGE         # Show package info
uv pip uninstall PACKAGE    # Uninstall package
uv pip freeze               # Show installed packages
uv pip compile requirements.in  # Compile requirements
```

### Python Versions
```bash
uv python list              # List available Python versions
uv python pin 3.11          # Pin project to Python 3.11
uv python install 3.11      # Download and install Python 3.11
```

## Project Configuration

The project is configured in `pyproject.toml`:

```toml
[project]
name = "claude-cert-sdk-parser"
requires-python = ">=3.8"

[project.optional-dependencies]
dev = ["pytest", "black", "flake8", "mypy"]
test = ["pytest", "pytest-cov"]
lint = ["black", "flake8", "mypy", "isort"]
```

Install specific dependency groups:
```bash
uv pip install -e ".[dev]"   # Development tools
uv pip install -e ".[test]"  # Testing tools
uv pip install -e ".[lint]"  # Linting tools
```

## Development Workflow

### 1. Start Development Session
```bash
cd /path/to/Claude_cert
source .venv/bin/activate  # Activate venv (if not already)
```

### 2. Make Code Changes
```bash
# Edit your code
# Example: lib/sdk_parser_py/parser.py
```

### 3. Test Your Changes
```bash
# Run relevant tests
pytest tests/test_parser.py

# Check code quality
black --check lib/
flake8 lib/
mypy lib/sdk_parser_py/
```

### 4. Format and Fix
```bash
# Auto-format code
black lib/
isort lib/

# Re-run tests
pytest tests/
```

### 5. Commit Changes
```bash
git add .
git commit -m "Add feature: description"
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate venv
rm -rf .venv
uv venv

# Activate again
source .venv/bin/activate
```

### Package Installation Issues
```bash
# Clear cache
uv pip cache purge

# Reinstall everything
uv pip install --force-reinstall -e ".[dev]"

# Check for conflicts
uv pip check
```

### Python Version Issues
```bash
# Check current Python
python --version

# Use specific Python from venv
.venv/bin/python --version

# Reinstall with specific version
uv venv --python 3.11
```

## Performance Tips

1. **Cache:** uv caches packages, making subsequent installs faster
2. **Lock file:** Use `uv pip compile` for deterministic installs
3. **Dependencies:** Keep dependency list minimal
4. **Parallel:** uv installs in parallel by default

## Integration with IDEs

### VS Code
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

### PyCharm
1. Settings → Project → Python Interpreter
2. Select "Existing environment"
3. Choose `.venv/bin/python`

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [mypy Documentation](https://mypy.readthedocs.io/)

## Quick Commands Cheat Sheet

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Development
python lib/sdk_parser_py/examples.py
pytest tests/ -v
black lib/ tests/
flake8 lib/ tests/

# Cleanup
deactivate
rm -rf .venv .pytest_cache __pycache__
```

---

**Happy coding! 🚀**
