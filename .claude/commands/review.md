# /review Slash Command

Execute the team's standard Claude Certified Architect code review checklist.

## Usage
`/review [path/to/code]`

## Review Focus
1. **Compliance with Execution Policy**:
   - Verify no live API calls are run automatically.
2. **Architectural Patterns**:
   - Deterministic stop_reason checks (`tool_use` vs `end_turn`).
   - Programmatic hooks vs prompt guidance for business logic.
   - Differentiated tool descriptions and structured error responses (`isError`, `errorCategory`, `isRetryable`).
   - Least privilege tool distribution.
   - Schema enforcement via `tool_use`.
3. **Audit & Replay**:
   - `ResponseTrail` logging for JSONL audit trails.
   - `lib.sdk_parser_py` response parsing.
4. **Code Quality**:
   - Full typing, docstrings, and offline unit test coverage.
