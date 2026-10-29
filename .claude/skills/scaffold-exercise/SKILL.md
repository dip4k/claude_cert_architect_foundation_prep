---
name: scaffold-exercise
description: Scaffolds a new Claude Certified Architect task statement practice exercise with offline test pairing
context: fork
allowed-tools:
  - Read
  - Write
  - Glob
argument-hint: "<domain_num> <task_statement_num> <exercise_short_name>"
---

# Claude Architect Exercise Scaffolder

Scaffolds a new practice exercise in `domain{domain_num}/ts_{domain_num}_{task_statement_num}_{exercise_short_name}/`.

## Standard Components to Generate:
1. `main.py`:
   - Detailed header documenting exam domain, task statement, and key architectural concepts.
   - Claude 4.5 API model (`claude-sonnet-4-5` or `claude-haiku-4-5`).
   - Extended Thinking parameters (`thinking={"type": "enabled", "budget_tokens": 1024}`); **temperature omitted**.
   - Core tools and agentic loop using `lib.sdk_parser_py` and `lib.response_logger`.
   - In multi-turn history: preserve assistant thinking blocks verbatim with signatures.
   - Clear manual execution instructions in WSL Ubuntu.
2. `README.md`:
   - Task statement exam objectives and official competencies.
   - Mermaid diagram complying with October 2026 standards (quoted labels, no raw HTML, no init directives).
   - Exam distractor traps and decision matrix.
3. `tests/test_domain_{domain_num}_ts_{task_statement_num}.py`:
   - Offline unit test using `lib.mock_claude.MockClaudeClient` and `MockMessageResponse`.
   - Comprehensive test assertions for tool schemas, deterministic stopping, and error scenarios.
4. Update `PROGRESS.md` to reflect the newly scaffolded task statement.
