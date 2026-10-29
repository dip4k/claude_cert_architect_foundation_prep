# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📌 Critical Constraint: Manual Execution Only

**DO NOT automate execution of scripts that make Claude API calls.** This is a learning/practice repository where scripts consume tokens and incur costs.

- ❌ Never use `/run` on `1_stop_reason/main.py`, `1_hello-sdk/agent.py`, or custom practice code that imports Claude API
- ❌ Never ask agents to execute API-calling scripts
- ✅ Safe to automate: `pytest tests/`, `black lib/ tests/`, `flake8`, `mypy` (offline tools)
- ✅ Users run API examples manually in WSL Ubuntu terminal

See [EXECUTION_POLICY.md](EXECUTION_POLICY.md) and [RUNNING_WITH_UV.md](RUNNING_WITH_UV.md) for detailed guidance.

---

## 🏗️ Architecture & Model Standards

**Language:** Python 3.10+ | **Package Manager:** uv | **Test Framework:** pytest  
**Models:** Claude 4.5 family (`claude-sonnet-4-5`, `claude-haiku-4-5`)

### Extended Thinking & Sampling Rule
- When `thinking={"type": "enabled", "budget_tokens": ...}` is enabled, **omit `temperature` entirely** (avoids HTTP 400 Bad Request error).
- In multi-turn agent loops: **never strip assistant `thinking` blocks** from conversation history; return them verbatim with signatures.

### Context Preservation & Tiering (Domain 5 & 3)
- Keep `CLAUDE.md` **under 200 lines**. Put universal constants here; tier procedural workflows into skills.
- Maintain persistent immutable "Case Facts" block outside summarized history.
- Trim raw tool outputs via `PostToolUse` before appending to conversation context.

### Core Libraries (in `lib/`)
1. **`sdk_parser_py/`** — Generic parser for Claude API/SDK responses (Zero dependencies, type-safe dataclasses).
2. **`response_logger/`** — Audit trail logging API requests/responses to JSONL for offline replay.
3. **`mock_claude/`** — Offline mock client (`MockClaudeClient`, `MockMessageResponse`) for simulated agentic loops.

### Claude Code Customizations (Domain 3 in Action)
- **Skills (`.claude/skills/`)**:
  - `architect-eval` — Code review against exam criteria (`context: fork`, restricted read tools)
  - `scaffold-exercise` — Scaffolder for new domain task statement exercises
- **Slash Commands (`.claude/commands/`)**: `/practice`, `/review`, `/audit`
- **Path Rules (`.claude/rules/`)**:
  - `domain_exercises.md` — Enforces parser, logger, loop conventions, and thinking parameters on `domain*/**`
  - `mcp_tools.md` — Enforces `isError` structured schemas on `**/tools/**`, `**/mcp*/**`
  - `python_quality.md` — Enforces typing, PEP 8, and black standards on `**/*.py`
  - `mermaid_standards.md` — Enforces October 2026 GitHub Mermaid rendering standards on `**/*.md`, `**/*.ipynb`

---

## 📊 GitHub Mermaid Architecture Standards (October 2026)

All Mermaid diagrams across documentation and notebooks must follow these rules:
- **Quoted Node Labels**: Wrap labels with punctuation, colons, or spaces in double quotes: `Node["Clean Label"]`.
- **Explicit Flow Direction**: Always declare `flowchart TD` or `flowchart LR`.
- **No Raw HTML Tags**: Never use `<b>` or `</b>` inside node labels. Use `<br>` inside double quotes for line breaks.
- **No Init Directives**: Never include `%%{init: ...}%%` blocks.

---

## 🚀 Common Commands (WSL Ubuntu Terminal)

```bash
# Setup (one-time)
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

## 🔍 Quick Answers

**Q: Can I run scripts that make Claude API calls automatically?**  
A: No. Scripts that call `client.messages.create()` must be run manually by the user in WSL Ubuntu terminal.

**Q: How do I handle temperature with Extended Thinking?**  
A: Omit `temperature` completely. The API rejects requests containing custom temperature when thinking is enabled.

**Q: Can I remove thinking blocks from conversation history?**  
A: No. Assistant thinking blocks must be preserved verbatim with signatures in subsequent turns to prevent 400 Bad Request errors.

**Q: How do I run tests?**  
A: `uv run pytest tests/` from repo root. Safe to automate.

---

**Last Updated:** October 2026 | **Line Count:** < 140 lines | **Status:** Active Learning Repository
