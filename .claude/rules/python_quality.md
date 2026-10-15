---
paths:
  - "**/*.py"
---

# Python Code Quality Standards

1. **Typing & Documentation**:
   - Every function and method must have complete type annotations (`typing` module / Python 3.10+ syntax).
   - Module and function docstrings must explain intent, architectural reasoning, inputs, and outputs.

2. **Formatting & Linting**:
   - Strict 100 character maximum line length.
   - Code must pass `black --check`, `flake8`, and `mypy` without errors.

3. **Dependency & Environment Hygiene**:
   - Zero dependencies for core parsing logic in `lib/sdk_parser_py`.
   - Never use global `pip install`; run tools via `uv run` inside WSL Ubuntu.
