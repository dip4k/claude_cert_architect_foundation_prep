# Workspace Guide: Claude Architect & Interview Prep

## 🛡️ Policy & Execution Safety
Strictly follow [no_claude_api_execution.md](file:///.agents/rules/no_claude_api_execution.md).
- **Prohibited**: Automated execution of live Claude/Anthropic API or Agent SDK scripts.
- **User Execution**: Manual in WSL Ubuntu-26.04 (`uv run <script_path>`).
- **Offline Automation**: Unit tests, linting, formatting (`pytest`, `black`, `flake8`, `mypy`) in WSL Ubuntu-26.04:
  ```powershell
  wsl -d Ubuntu-26.04 bash -c "~/.local/bin/uv run pytest tests/"
  ```

## 🎯 Architecture & Interview Preparation
This workspace prepares candidates for senior AI Systems Architect interviews and the **CCAR-F** certification.

### 📚 Foundational References
- **10 Golden Architectural Rules**: See [EXAM_REFRESHER.md](EXAM_REFRESHER.md) for core principles and anti-patterns.
- **Domains & Task Statements**: See [EXAM_BLUEPRINT.md](EXAM_BLUEPRINT.md) for the 5-domain matrix (TS 1.1–5.6).
- **6 Production Scenarios**: See [scenarios/README.md](scenarios/README.md) for lab guides and simulations.

### 🧭 Active Interview Skills
Activate on-demand skills from `.agents/skills/`:
- `claude-interview-coach`: Interactive mock exams, technical grilling, flashcards, and scenario roleplays.
- `claude-scenario-architect`: Blueprint matrix, SLAs, and decision trees for the 6 production scenarios.
- `claude-agent-architect`: Core loop patterns (`stop_reason`), hooks, and multi-agent topologies.
- `claude-cert-navigator`: Domain weightings (1-5) and syllabus navigation.
- `claude-code-workflows`: CLAUDE.md hierarchy, path rules, plan mode, and CI/CD.
- `claude-offline-tester`: Zero-cost offline mocking with `lib.mock_claude`.
