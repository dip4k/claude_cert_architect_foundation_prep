---
paths:
  - "**/tools/**"
  - "**/mcp*/**"
  - ".mcp.json"
---

# MCP Tool & Server Design Rules

When implementing or editing MCP tools and configurations:

1. **Structured Error Protocol (TS 2.2)**:
   - Always return errors with the `isError: true` flag in MCP responses.
   - Include structured error metadata:
     - `errorCategory`: `"transient"` | `"validation"` | `"business"` | `"permission"`
     - `isRetryable`: `true` for timeouts/transient network failures; `false` for invalid inputs and policy violations.
     - `message`: Clear, human-readable message for the agent or user.

2. **Differentiated Tool Descriptions (TS 2.1)**:
   - Tool descriptions are the primary routing mechanism for LLMs.
   - Every tool description must state:
     - Specific purpose and capabilities.
     - Input parameter formats and constraints.
     - Clear boundary definitions distinguishing it from similar tools (e.g. `lookup_order` vs `get_customer`).

3. **Least Privilege Distribution (TS 2.3)**:
   - Restrict agents and subagents to 4–5 focused tools aligned with their specialization.
   - For mandatory first steps, use forced `tool_choice: {"type": "tool", "name": "..."}`.

4. **Configuration Scoping & Credentials (TS 2.4)**:
   - Project-scoped servers belong in `.mcp.json`.
   - Never hardcode secrets in `.mcp.json`; use `${ENV_VAR}` expansion.
