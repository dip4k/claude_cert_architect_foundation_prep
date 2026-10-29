# Workspace Guide: Claude Architect & Interview Prep

## 🛡️ Policy & Execution Safety
Strictly follow [no_claude_api_execution.md](.agents/rules/no_claude_api_execution.md).
- **Prohibited**: Automated execution of live Claude/Anthropic API or Agent SDK scripts.
- **User Execution**: Manual in WSL Ubuntu-26.04 (`uv run <script_path>`).
- **Offline Automation**: Unit tests, linting, formatting (`pytest`, `black`, `flake8`, `mypy`) in WSL Ubuntu-26.04:
  ```powershell
  wsl -d Ubuntu-26.04 bash -c "~/.local/bin/uv run pytest tests/"
  ```

## 🎯 Architecture, Context & Mermaid Standards
- **Extended Thinking**: Follow [.agents/rules/context_and_mermaid.md](.agents/rules/context_and_mermaid.md). Use Claude 4.5; omit `temperature` when `thinking` is active (`budget_tokens`); preserve thinking blocks in multi-turn history.
- **Context Preservation**: Persistent "Case Facts" block outside summaries, `PostToolUse` tool trimming, `CLAUDE.md` under 200 lines, and on-demand skills with `context: fork`.
- **October 2026 Mermaid Standards**: Quoted labels (`Node["..."]`), explicit flow direction, no raw HTML tags (`<b>`), and no `%%{init}%%` blocks.

## 📚 Foundational References
- **15 Golden Architectural Rules**: See [EXAM_REFRESHER.md](EXAM_REFRESHER.md) for core principles and anti-patterns.
- **Domains & Task Statements**: See [EXAM_BLUEPRINT.md](EXAM_BLUEPRINT.md) for the 5-domain matrix (TS 1.1–5.6).
- **6 Production Scenarios**: See [scenarios/README.md](scenarios/README.md) for lab guides and simulations.

## 🧭 Active Interview Skills
Activate on-demand skills from `.agents/skills/`:
- `claude-interview-coach`: Interactive mock exams, technical grilling, flashcards, and scenario roleplays.
- `claude-scenario-architect`: Blueprint matrix, SLAs, and decision trees for the 6 production scenarios.
- `claude-agent-architect`: Core loop patterns (`stop_reason`), thinking continuity, and multi-agent topologies.
- `claude-cert-navigator`: Domain weightings (1-5) and syllabus navigation.
- `claude-code-workflows`: CLAUDE.md hierarchy (<200 lines), path rules, plan mode, and CI/CD.
- `claude-offline-tester`: Zero-cost offline mocking with `lib.mock_claude`.
