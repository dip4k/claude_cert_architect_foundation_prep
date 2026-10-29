# Running Scripts with UV - Workspace & Execution Guide

> **Execution Policy Reminder**: Do not automate live Anthropic API calls. All interactive/API scripts must be run manually in your terminal. Offline unit tests (`pytest tests/ scenarios/`) are 100% safe to automate.

---

## 🏗️ Unified UV Workspace Architecture

This repository uses a **unified UV workspace** centered around a single, shared virtual environment located at the repository root (`.venv`).

```
Claude_cert/
├── .venv/                         # Shared virtual environment for the entire repository
│   └── Lib/site-packages/_root.pth # Adds repo root to sys.path automatically
├── .env                           # Single source of truth for API keys & model settings
├── .env.example                   # Sanitized template
├── pyproject.toml                 # Workspace root with shared dependencies & tools
├── lib/                           # Core shared libraries (sdk_parser_py, response_logger, mock_claude)
├── domain1/ ... domain5/          # Certification Task Statements (TS 1.1 - 5.6)
├── scenarios/                     # 6 Production Scenarios
└── anthropic-api-practice/        # Anthropic API & MCP Practice
    └── MCP/
        └── cli_project/           # Workspace member: FastMCP server & CLI chat
            ├── pyproject.toml     # [tool.uv] package = false
            ├── mcp_server.py      # FastMCP tools, resources & prompts
            └── main.py            # CLI chat application
```

---

## ⚡ Quick Reference: Running Scripts

### 1. From Repository Root (Standard Practice Exercises)
When working on Task Statements (Domains 1–5) or Production Scenarios:

```bash
# Windows PowerShell:
.\.venv\Scripts\activate
python domain1/ts_1_1_multi_tool_agent_loop/main.py

# Or using uv run:
uv run domain1/ts_1_1_multi_tool_agent_loop/main.py

# Linux / WSL Ubuntu:
source .venv/bin/activate
python domain1/ts_1_1_multi_tool_agent_loop/main.py
```

### 2. From Subdirectories (e.g. MCP Practice)
The root `.venv` includes a `_root.pth` path configuration file and workspace definition, so you can execute scripts from subdirectories without `ModuleNotFoundError`:

```powershell
# Navigate into the subproject
cd anthropic-api-practice\MCP\cli_project

# Option A: UV run (pointing to root workspace venv)
uv run --no-sync main.py

# Option B: Directly invoke the root virtual environment
..\..\..\.venv\Scripts\python main.py
```

---

## 🔌 Running MCP Servers & MCP Inspector

The `anthropic-api-practice/MCP/cli_project` directory contains a complete **FastMCP** server (`mcp_server.py`) exposing tools, resources, and prompts.

### Option A: Interactive MCP Inspector Web Dashboard (Zero Re-installs)
The official `mcp dev` command creates an ephemeral environment and re-downloads packages on every launch. To avoid re-installations, pass your existing root Python directly to the inspector:

```powershell
cd anthropic-api-practice\MCP\cli_project

# Launch Inspector with root venv Python (instant startup):
npx @modelcontextprotocol/inspector ..\..\..\.venv\Scripts\python.exe mcp_server.py
```

This launches the web UI at `http://localhost:5173` where you can interactively test:
- **Tools**: `read_doc_contents`, `edit_document`
- **Resources**: `docs://documents` (list IDs), `docs://documents/{doc_id}` (read content)
- **Prompts**: `/summarize <doc_id>`, `/rewrite_markdown <doc_id>`

### Option B: Running the MCP Server Standalone
FastMCP servers run over standard input/output (`stdio`):

```powershell
cd anthropic-api-practice\MCP\cli_project
uv run --no-sync python mcp_server.py
```

---

## 🔑 Environment Configuration (`.env`)

You only need **one** `.env` file at the repository root:
- `python-dotenv` automatically walks up parent directories until it finds the root `.env`.
- Subprojects inherit `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, and `USE_UV=1` automatically without duplicating secrets.

```bash
# .env at repository root:
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5
USE_UV=1
DEBUG=false
```

---

## 🧪 Safe Offline Testing

All unit tests across domains and scenarios are designed to run with **zero API tokens** using deterministic mocks (`lib.mock_claude`):

```bash
# Run all unit tests
uv run pytest

# Run tests with short traceback
uv run pytest tests/ scenarios/ -v --tb=short
```

---

## 🛠️ Troubleshooting Common UV Issues

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'lib'` | Python doesn't have the repo root in its path | Run from repo root, or verify `.venv/Lib/site-packages/_root.pth` exists. |
| `TypeError: Field.__init__() got unexpected keyword argument 'description'` | Imported `Field` from standard `dataclasses` instead of Pydantic | Change `from dataclasses import Field` to `from pydantic import Field`. |
| `mcp dev` keeps downloading packages | Hardcoded `--with mcp` in CLI creates a temporary environment | Run `npx @modelcontextprotocol/inspector <path_to_venv_python> mcp_server.py` directly. |
| Lockfile out-of-sync error offline | `uv run` attempts to sync missing packages when network is disabled | Add `--no-sync` flag: `uv run --no-sync <script>`. |
