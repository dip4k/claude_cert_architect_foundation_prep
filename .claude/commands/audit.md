# /audit Slash Command

Run an offline safety, static analysis, and unit test audit of the practice repository.

## Commands Executed (Offline in WSL Ubuntu)
```bash
# 1. Run offline unit tests
uv run pytest tests/ -v

# 2. Format checking
uv run black --check lib/ tests/

# 3. Linting
uv run flake8 lib/ tests/

# 4. Type checking
uv run mypy lib/sdk_parser_py/
```
