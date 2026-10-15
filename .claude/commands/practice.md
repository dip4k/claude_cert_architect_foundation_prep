# /practice Slash Command

Start or review an exam task statement exercise.

## Usage
`/practice <domain> <task_statement>`

Examples:
- `/practice 1 1` (Domain 1, Task Statement 1.1: Agentic loop)
- `/practice 1 4` (Domain 1, Task Statement 1.4: Multi-step workflows & programmatic prerequisite gates)
- `/practice 2 2` (Domain 2, Task Statement 2.2: MCP structured error responses)
- `/practice 4 3` (Domain 4, Task Statement 4.3: Structured output via tool_use)
- `/practice 5 2` (Domain 5, Task Statement 5.2: Escalation & ambiguity resolution)

## Instructions
1. Locate the directory `domain{domain}/ts_{domain}_{task_statement}_*`.
2. Present:
   - Exam objective and official knowledge areas.
   - Realistic exam scenario framing (e.g. Scenario 1: Customer Support, Scenario 3: Research System).
   - Architectural trade-offs to look out for.
   - Manual run command for WSL Ubuntu:
     ```bash
      uv run domain{N}/ts_{N}_{M}_<name>/main.py
     ```
   - Offline test command:
     ```bash
     uv run pytest tests/ -k "domain{N}"
     ```
