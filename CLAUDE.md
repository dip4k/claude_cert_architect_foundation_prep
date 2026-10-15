# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📌 Critical Constraint: Manual Execution Only

**DO NOT automate execution of scripts that make Claude API calls.** This is a learning/practice repository where scripts consume tokens and incur costs.

- ❌ Never use `/run` on `1_stop_reason/main.py`, `1_hello-sdk/agent.py`, or custom practice code that imports Claude API
- ❌ Never ask agents to execute API-calling scripts
- ✅ Safe to automate: `pytest tests/`, `black lib/ tests/`, `flake8`, `mypy` (offline tools)
- ✅ Users run API examples manually in WSL Ubuntu terminal

**Why:** Scripts can make multiple API calls per execution. Unmonitored automated runs exhaust token budgets quickly.

See [EXECUTION_POLICY.md](EXECUTION_POLICY.md) and [RUNNING_WITH_UV.md](RUNNING_WITH_UV.md) for detailed guidance.

---

## 🏗️ Architecture Overview

**Language:** Python 3.10+ | **Package Manager:** uv | **Test Framework:** pytest

### Core Libraries (in `lib/`)

1. **`sdk_parser_py/`** — Generic parser for Claude API/SDK responses
   - Zero dependencies, production-ready
   - Type-safe with Python dataclasses
   - Extract text, tool calls, token usage from responses
   - See: [lib/sdk_parser_py/USAGE.md](lib/sdk_parser_py/USAGE.md)

2. **`response_logger/`** — Audit trail for agentic loops
   - Log API requests/responses to JSONL for offline replay
   - Track latency, tool calls, session lifecycle
   - No API calls needed for replay
   - See: [lib/response_logger/README.md](lib/response_logger/README.md)

### Examples & Practice

- **`1_stop_reason/main.py`** — Agent with Pokemon lookup + fortune tools (makes API calls)
- **`1_hello-sdk/agent.py`** — Basic SDK usage example (makes API calls)
- **`lib/sdk_parser_py/examples.py`** — SDK parser examples with simulated data (no API calls)
- **`hello-world/`** — Tool use tutorial examples

### Certification Practice (`domainN/`)

Hands-on exercises for the **Claude Certified Architect – Foundations** exam
(`Claude_Certified_Architect_-_Foundations_-_Exam_Guide.pdf`), organized by exam content domain
and task statement:

```
domain{N}/ts_{N}_{M}_<short-name>/main.py
```

- `N` = domain number (1–5), `M` = task statement number within that domain
- Example: `domain1/ts_1_1_multi_tool_agent_loop/main.py` → Domain 1, Task Statement 1.1

Exam domains:
1. **Agentic Architecture & Orchestration** (27%) — agentic loops, subagents, hooks, task decomposition, session state
2. **Tool Design & MCP Integration** (18%) — tool interfaces, MCP error handling, tool distribution, built-in tools
3. **Claude Code Configuration & Workflows** (20%) — CLAUDE.md hierarchy, slash commands/skills, plan mode, CI/CD
4. **Prompt Engineering & Structured Output** (20%) — precision prompting, few-shot, JSON schemas, batch processing
5. **Context Management & Reliability** (15%) — context preservation, escalation patterns, error propagation, provenance

Every practice script:
- Uses `lib/sdk_parser_py` to parse Claude responses (`create_parser().parse(response.model_dump())`)
- Uses `lib/response_logger` (`ResponseTrail`, `get_agent_trail_path`, `replay_trail`) for a full JSONL audit trail of each run
- Makes live API calls → **subject to the Manual Execution Only constraint above**

### Tests, Offline Simulation & Quality

- **`tests/`** — 100% offline pytest unit tests for parsers, loggers, and domain exercises (zero API tokens used)
- **`lib/mock_claude/`** — Offline mock client (`MockClaudeClient`, `MockMessageResponse`) for simulated agentic loops
- **pyproject.toml** — Dependencies: `anthropic`, `python-dotenv` (plus dev tools)
- **`.python-version`** — Python 3.11 (minimum 3.10)

### Claude Code Customizations (Domain 3 in Action)

- **Skills (`.claude/skills/`)**:
  - `architect-eval` — Code review against exam criteria (`context: fork`, restricted read tools)
  - `scaffold-exercise` — Scaffolder for new domain task statement exercises
- **Slash Commands (`.claude/commands/`)**:
  - `/practice <domain> <ts>` — Launch scenario practice
  - `/review [path]` — Architecture & code review
  - `/audit` — Run offline pytest, formatters, and type checkers
- **Path Rules (`.claude/rules/`)**:
  - `domain_exercises.md` — Enforces parser, logger, and deterministic loop conventions on `domain*/**`
  - `mcp_tools.md` — Enforces `isError` structured schemas on `**/tools/**`, `**/mcp*/**`
  - `python_quality.md` — Enforces typing, PEP 8, and black standards on `**/*.py`
- **MCP Server Config**: `.mcp.json` with environment variable expansion (`${ANTHROPIC_API_KEY}`)
- **Master Blueprint**: `EXAM_BLUEPRINT.md` and `PROGRESS.md`


---

## 🚀 Common Commands (WSL Ubuntu Terminal)

```bash
# Setup (one-time)
# From repository root:
cp .env.example .env          # Edit with your ANTHROPIC_API_KEY
uv sync                       # Install dependencies

# Development (safe to automate)
uv run pytest tests/                      # Run all tests
uv run pytest tests/test_response_logger.py -v  # Run specific test
uv run black lib/ tests/                  # Format code
uv run flake8 lib/ tests/                 # Lint
uv run mypy lib/sdk_parser_py/            # Type checking

# Running examples (MANUAL ONLY in WSL Ubuntu terminal)
uv run lib/sdk_parser_py/examples.py      # Simulated data, no API calls
uv run 1_stop_reason/main.py              # Makes API calls - manual run only!
uv run 1_hello-sdk/agent.py               # Makes API calls - manual run only!
```

---

## 📝 Development Workflow

### Add a New Test
```bash
# Create test in tests/test_*.py
# Use pytest patterns, import from lib.sdk_parser_py or lib.response_logger
# Run: uv run pytest tests/test_yourname.py -v
```

### Create a Practice Project
```bash
mkdir practice/my-project
cat > practice/my-project/main.py << 'EOF'
from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail

def main():
    # Your code here
    pass

if __name__ == "__main__":
    main()
EOF

# Run manually if it makes API calls
# Run via agents if it doesn't
```

### Import SDK Parser
```python
from lib.sdk_parser_py import create_parser, format_token_usage
from lib.response_logger import ResponseTrail, replay_trail
```

---

## 📚 Key Documentation

**For detailed setup:** [PYTHON_SETUP.md](PYTHON_SETUP.md)  
**For execution policy:** [EXECUTION_POLICY.md](EXECUTION_POLICY.md)  
**For import/path issues:** [RUNNING_WITH_UV.md](RUNNING_WITH_UV.md)  
**SDK Parser deep dive:** [lib/sdk_parser_py/README.md](lib/sdk_parser_py/README.md)  
**Response Logger guide:** [lib/response_logger/README.md](lib/response_logger/README.md)

---

## ✅ Code Standards

- **Style:** Black (100 char lines), PEP 8
- **Types:** Full type hints on all functions (mypy checks)
- **Docs:** Module & function docstrings
- **Imports:** Module exports via `__init__.py` (use `/select:Read,Edit,Grep` for imports)
- **Tests:** pytest in `tests/` directory
- **Deps:** Zero external deps for core parsers

---

## 🔍 Quick Answers

**Q: Where is the SDK parser?**  
A: `lib/sdk_parser_py/` — use `from lib.sdk_parser_py import create_parser`

**Q: How do I log API calls for offline replay?**  
A: `from lib.response_logger import ResponseTrail` — see [lib/response_logger/README.md](lib/response_logger/README.md)

**Q: Can I run stop_reason/main.py automatically?**  
A: No. It makes API calls. User must run manually in WSL Ubuntu terminal. See [EXECUTION_POLICY.md](EXECUTION_POLICY.md).

**Q: How do I run tests?**  
A: `uv run pytest tests/` from repo root. Safe to automate.

**Q: What's in 1_stop_reason/ vs stop_reason/?**  
A: `1_stop_reason/` is the current version. Old `stop_reason/` was deleted but still referenced in git history.

---

**Last Updated:** September 2026  
**Status:** Active Learning Repository
