# Claude Certified Architect – Foundations Practice Repository

[![Tests](https://img.shields.io/badge/pytest-29%20passed%20offline-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Package Manager](https://img.shields.io/badge/uv-fast%20sync-purple)](https://astral.sh/uv)
[![Exam](https://img.shields.io/badge/Claude%20Certified%20Architect-Foundations-orange)](EXAM_BLUEPRINT.md)

Comprehensive hands-on practice repository for the **Claude Certified Architect – Foundations Certification** (passing score 720/1000).

---

## ⚠️ Critical Policy: Manual Execution Only in WSL Ubuntu

To protect API budgets and prevent unintended costs:
- ❌ **Automated agents MUST NEVER execute scripts making live Anthropic API calls.**
- ✅ **Offline testing is 100% automated & zero-token:** All unit tests (`pytest tests/`) run with offline mock responses (`lib.mock_claude`).
- ✅ **Live API practice is executed manually by the user** in their WSL Ubuntu terminal:
  ```bash
  # From repository root:
  uv run domain1/ts_1_1_multi_tool_agent_loop/main.py
  ```

---

## 🏛️ Exam Syllabus & Architecture

This repository is organized directly around the official Exam Content Domains and 6 Realistic Scenarios:

```
Claude_cert/
├── domain1/          # Agentic Architecture & Orchestration (27%)
│   ├── ts_1_1_multi_tool_agent_loop/
│   ├── ts_1_4_prerequisite_enforcement/
│   └── README.md
├── domain2/          # Tool Design & MCP Integration (18%)
│   ├── ts_2_2_mcp_structured_errors/
│   └── README.md
├── domain3/          # Claude Code Configuration & Workflows (20%)
│   └── README.md
├── domain4/          # Prompt Engineering & Structured Output (20%)
│   ├── ts_4_3_structured_output_tool_use/
│   └── README.md
├── domain5/          # Context Management & Reliability (15%)
│   ├── ts_5_1_context_preservation/
│   └── README.md
├── scenarios/        # The 6 Exam Scenarios Reference & Architectural Guide
│   └── README.md
├── lib/
│   ├── sdk_parser_py/   # Response extraction & validation
│   ├── response_logger/ # JSONL trail recording & offline replay
│   └── mock_claude/     # Offline mock client for zero-cost testing
├── tests/            # Pytest suite running offline (29+ tests)
├── .claude/          # Claude Code native configuration (Domain 3)
│   ├── rules/        # Path-specific conditional rules (TS 3.3)
│   ├── skills/       # Forked, tool-restricted skills (TS 3.2)
│   └── commands/     # Project-scoped slash commands (TS 3.2)
├── .agents/          # Antigravity agents and skills
│   ├── skills/       # Navigator, architect, offline-tester, workflows
│   └── ...           # Exam mentor, code reviewer, exercise scaffolder
├── .mcp.json         # Project-scoped MCP server config (TS 2.4)
├── EXAM_BLUEPRINT.md # Master exam syllabus, weighting, and scenario guide
└── PROGRESS.md       # Interactive 27-task statement progress checklist
```

---

## 🤖 Agents & Skills Included

### 1. Antigravity & Workspace Skills (`.agents/skills/`)
- [`claude-cert-navigator`](.agents/skills/claude-cert-navigator/SKILL.md): Comprehensive exam guide, scoring requirements, 5 domains, and 6 scenarios.
- [`claude-agent-architect`](.agents/skills/claude-agent-architect/SKILL.md): Architectural decision matrix: loop control, programmatic gates, tool distribution, and context preservation.
- [`claude-offline-tester`](.agents/skills/claude-offline-tester/SKILL.md): Offline test design with zero API tokens using `lib.mock_claude`.
- [`claude-code-workflows`](.agents/skills/claude-code-workflows/SKILL.md): Domain 3 configuration: CLAUDE.md hierarchy, path-scoped rules, plan mode, and CI/CD.

### 2. Specialized Agents (`.agents/`)
- [`claude-exam-mentor`](.agents/claude-exam-mentor.md): Scenario coach and quiz master testing candidates with 4-choice questions and trade-off analysis.
- [`offline-code-reviewer`](.agents/offline-code-reviewer.md): Automated static checker running tests, formatting, and verifying no-live-API policies.
- [`claude-cert-scaffolder`](.agents/claude-cert-scaffolder.md): Automated exercise scaffolder for new task statements.

### 3. Claude Code Native Skills & Commands (`.claude/`)
- **Skills**:
  - [`.claude/skills/architect-eval/`](.claude/skills/architect-eval/SKILL.md): Architectural review (`context: fork`, restricted read tools).
  - [`.claude/skills/scaffold-exercise/`](.claude/skills/scaffold-exercise/SKILL.md): Scaffolds new task statement practice (`context: fork`).
- **Commands**:
  - `/practice <domain> <ts>`: Launch practice framing and requirements.
  - `/review [path]`: Multi-pass architectural code review.
  - `/audit`: Run offline tests, formatting, and linting.
- **Path-Specific Rules** (`.claude/rules/`):
  - `domain_exercises.md`: Enforces `sdk_parser_py`, `response_logger`, and `stop_reason` standards for `domain*/**`.
  - `mcp_tools.md`: Enforces `isError` structured schemas for MCP tools.
  - `python_quality.md`: Enforces type hints, docstrings, and formatting for `**/*.py`.

---

## ⚡ Quick Start

```bash
# In WSL Ubuntu Terminal:
# From repository root:

# 1. Install dependencies
uv sync

# 2. Run all offline unit tests (zero tokens, safe to automate)
uv run pytest tests/ -v

# 3. Format and lint checks
uv run black --check lib/ tests/
uv run flake8 lib/ tests/
uv run mypy lib/sdk_parser_py/

# 4. Run hands-on live exercise manually:
cp .env.example .env # Set your ANTHROPIC_API_KEY
uv run domain1/ts_1_1_multi_tool_agent_loop/main.py
```

---

## 📚 Study Resources
- [Master Exam Blueprint](EXAM_BLUEPRINT.md)
- [Interactive Progress Tracker](PROGRESS.md)
- [Official Exam Scenarios Guide](scenarios/README.md)
- [Response Parser Documentation](lib/sdk_parser_py/USAGE.md)
- [Response Trail Logger Guide](lib/response_logger/README.md)
