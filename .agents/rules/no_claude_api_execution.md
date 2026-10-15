---
trigger: always_on
description: Prohibit automated execution of live Claude API/SDK scripts. Offline WSL Ubuntu only.
---

# Policy Rule: Zero Live Claude API Execution

- **Prohibited**: Never automate scripts invoking live Anthropic/Claude APIs or Agent SDKs (`anthropic`, `claude_agent_sdk`, `client.messages.create()`, `.env` tokens, curl to `api.anthropic.com`).
- **User Execution**: All live API scripts are run manually by the user in WSL Ubuntu terminal:
  ```bash
  uv run <script_path>
  ```
- **Safe Offline Automation**: Unit tests, linting, and formatting inside WSL Ubuntu:
  ```powershell
  wsl -d Ubuntu bash -c "~/.local/bin/uv run pytest tests/"
  ```
