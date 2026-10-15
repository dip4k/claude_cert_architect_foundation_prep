---
paths:
  - "domain*/**"
---

# Domain Exercise Implementation Standards

When working on certification practice exercises inside `domain{N}/`:

1. **Response Parser & Logger Integration**:
   - Always use `lib.sdk_parser_py.create_parser()` to parse responses:
     ```python
     parser = create_parser()
     parsed = parser.parse(response.model_dump())
     ```
   - Always initialize `ResponseTrail` from `lib.response_logger` with `get_agent_trail_path(__file__)` to record all turns and tool calls for offline audit and replay.

2. **Deterministic Control Flow**:
   - Never parse natural language strings or text content to determine loop completion.
   - Use `response.stop_reason` as the sole signal: `"tool_use"` to execute tools and continue, `"end_turn"` to terminate.
   - Set safety caps (`MAX_ITERATIONS`) solely as defensive fallbacks, never as the primary loop stopping condition.

3. **Offline Test Pairing**:
   - Every domain exercise script should have a corresponding offline unit test in `tests/` using `lib.mock_claude`.
   - Automated test verification must run offline without making live Claude API calls.

4. **Strict Manual Execution**:
   - Mark all main scripts with clear docstrings warning that live execution is for manual user runs only.
