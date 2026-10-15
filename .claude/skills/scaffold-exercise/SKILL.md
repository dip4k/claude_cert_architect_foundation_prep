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
   - Core tools and agentic loop using `lib.sdk_parser_py` and `lib.response_logger`.
   - Clear manual execution instructions in WSL Ubuntu.
2. `tests/test_domain_{domain_num}_ts_{task_statement_num}.py`:
   - Offline unit test using `lib.mock_claude.AsyncMockClaudeClient` and `MockMessageResponse`.
   - Comprehensive test assertions for tool schemas, deterministic stopping, and error scenarios.
3. Update `PROGRESS.md` to reflect the newly scaffolded task statement.
