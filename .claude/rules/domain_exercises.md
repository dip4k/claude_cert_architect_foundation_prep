---
paths:
  - "domain*/**"
---

# Domain Exercise Implementation Standards

When working on certification practice exercises inside `domain{N}/`:

1. **Model Standards & Extended Thinking**:
   - Use the **Claude 4.5 family** (`claude-sonnet-4-5` for orchestrators/reasoning, `claude-haiku-4-5` for workers/subagents).
   - When Extended Thinking is enabled (`thinking={"type": "enabled", "budget_tokens": ...}`):
     - **Remove / omit `temperature`** (rejected with HTTP `400` when thinking is on). Safest: also leave `top_p` and `top_k` unset; newer models reject any non-default `temperature`, `top_p` or `top_k`.
     - With manual extended thinking (`type: enabled`, the only thinking mode on Claude 4.5 models), use only `tool_choice` `auto` or `none`; `any` or a forced named tool returns HTTP `400`. Force a tool on a request that has no `thinking`. Adaptive thinking on newer models can accept forced tool use (not on every model).
     - Models newer than 4.5 use `thinking: {type: adaptive}` with `output_config.effort`; Claude 4.7 and later reject `budget_tokens`.
     - Set `budget_tokens` as a positive integer (minimum 1024, strictly less than `max_tokens`).
   - In multi-turn agent loops: assistant `thinking` blocks must be preserved and echoed back **unmodified** (including their cryptographic `signature`) in subsequent turns; stripping them causes an API `400 Bad Request` error.

2. **Deterministic Control Flow (TS 1.1)**:
   - Never parse natural language strings or text content to determine loop completion.
   - Use `response.stop_reason` as the sole signal: `"tool_use"` to execute tools and continue, `"end_turn"` to terminate.
   - Set safety caps (`MAX_ITERATIONS`) solely as defensive fallbacks, never as the primary loop stopping condition.

3. **Context Window Preservation (Domain 5)**:
   - Maintain an immutable "Case Facts" block outside summarized conversational history for transactional entities (order IDs, customer IDs, prices).
   - Use `PostToolUse` normalization hooks to trim bloated tool outputs before appending to conversation context.

4. **Response Parser & Logger Integration**:
   - Use `lib.sdk_parser_py.create_parser()` to parse responses:
     ```python
     parser = create_parser()
     parsed = parser.parse(response.model_dump())
     ```
   - Initialize `ResponseTrail` from `lib.response_logger` with `get_agent_trail_path(__file__)` to record turns for offline replay.

5. **GitHub Mermaid Guidelines (October 2026 Standards)**:
   - All architecture diagrams in markdown/notebooks must use clean GitHub-compliant Mermaid:
     - Wrap all node labels with punctuation, colons, or spaces in double quotes: `Node["Clean Label"]`.
     - Explicit flow direction (`flowchart TD` or `flowchart LR`).
     - No raw HTML tags like `<b>` or `</b>` inside node labels.
     - No fragile `%%{init: ...}%%` directives.

6. **Offline Test Pairing & Safety**:
   - Every domain exercise script should have a corresponding offline unit test in `tests/` using `lib.mock_claude`.
   - Never execute live API calls during automated runs. Live execution is for manual user runs only.
