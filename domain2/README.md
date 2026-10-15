# Domain 2: Tool Design & MCP Integration (18% of Exam)

Domain 2 accounts for 18% of the **Claude Certified Architect – Foundations (CCAR-F)** exam. It covers designing robust tool interfaces, implementing structured error responses for Model Context Protocol (MCP), distributing tools according to least privilege, integrating project vs. user MCP servers, and effectively selecting built-in tools.

> 📖 **Deep Dive Master Guide**: For exhaustive technical explanations, architecture diagrams, sequence flows, gotchas, to-remember points, and practical scenario questions & answers, see [KEY_CONCEPTS.md](KEY_CONCEPTS.md).

---

## 📋 Task Statements & Core Architectural Principles

### [TS 2.1: Design Effective Tool Interfaces with Clear Descriptions and Boundaries](ts_2_1_tool_interface_design/main.py)
- **Primary Routing Mechanism**: LLMs select tools based on descriptions and schemas. Vague descriptions cause a 50%+ misrouting rate.
- **4 Components of Production Descriptions**: Specific capability contract, input constraints & regex formats, explicit boundary statements (when to use vs adjacent tools), and 2–3 authentic user query examples.
- **Tool Refactoring**: Split monolithic "Swiss Army Knife" tools into focused, single-responsibility interfaces.
- **Reference Exercise**: [ts_2_1_tool_interface_design/](ts_2_1_tool_interface_design/)

### [TS 2.2: Implement Structured Error Responses for MCP Tools](ts_2_2_mcp_structured_errors/main.py)
- **The `isError` Flag**: Must be set to `true` on execution failure inside `CallToolResult`.
- **Structured Error Taxonomy**:
  - `transient`: Network timeouts, rate limits (`isRetryable: true`).
  - `validation`: Malformed or missing arguments (`isRetryable: false`).
  - `business`: Policy violations, insufficient balance (`isRetryable: false`, with user explanation).
  - `permission`: Authorization failures (`isRetryable: false`).
- **The Empty Match vs Error Rule**: A successful query returning 0 records is a **VALID EMPTY RESULT** (`isError: false`, `count: 0`), NOT an error. Treating it as an error triggers wasteful retries.
- **Reference Exercise**: [ts_2_2_mcp_structured_errors/](ts_2_2_mcp_structured_errors/)

### [TS 2.3: Distribute Tools Appropriately Across Agents and Configure Tool Choice](ts_2_3_tool_distribution_and_choice/main.py)
- **Principle of Least Privilege**: Limit agents to **4–5 specialized tools** rather than 15–20 broad tools to avoid tool selection degradation.
- **`tool_choice` Modes**:
  - `{"type": "auto"}`: Model decides whether to call a tool or reply with text (exploratory tasks).
  - `{"type": "any"}`: Model is forced to call at least one tool, selecting which one.
  - `{"type": "tool", "name": "..."}`: Forces an exact tool call (mandatory first step).
  - `{"type": "none"}`: Prevents all tool calls.
  - `disable_parallel_tool_use: True`: Forces strictly sequential execution when downstream tools depend on upstream outputs.
- **Reference Exercise**: [ts_2_3_tool_distribution_and_choice/](ts_2_3_tool_distribution_and_choice/)

### [TS 2.4: Integrate MCP Servers into Claude Code and Agent Workflows](ts_2_4_mcp_server_integration/main.py)
- **Configuration Scoping**: Project-level (`.mcp.json` in git) for team tools vs User-level (`~/.claude.json`) for local developer tools.
- **Secure Credentials**: Never commit secrets to git; use `${ENV_VAR}` expansion in `.mcp.json`.
- **The 3 MCP Primitives**: **Tools** (active functions with side effects), **Resources** (passive read-only data blobs/schemas via URIs), and **Prompts** (pre-parameterized slash-command templates).
- **Transports**: `stdio` (local subprocesses) vs `sse` (Server-Sent Events over HTTP).
- **Reference Exercise**: [ts_2_4_mcp_server_integration/](ts_2_4_mcp_server_integration/)

### [TS 2.5: Select and Apply Built-in Tools Effectively](ts_2_5_builtin_tools_usage/main.py)
- **Selection Matrix**: `Grep` (content search), `Glob` (path matching), `Read` (view content), `Write` (full file write), `Edit` (surgical replacement via anchor).
- **Edit Fallback Pattern**: When `Edit` fails due to ambiguous or non-unique anchor text, invoke `Read` to retrieve exact offsets and fall back to `Write` with the reconciled content.
- **Reference Exercise**: [ts_2_5_builtin_tools_usage/](ts_2_5_builtin_tools_usage/)

---

## 🛠️ Hands-on Exercises in this Domain
- `ts_2_1_tool_interface_design/`: Boundary-differentiated tool descriptions and query routing.
- `ts_2_2_mcp_structured_errors/`: MCP error classification taxonomy and valid empty result handling.
- `ts_2_3_tool_distribution_and_choice/`: Least privilege tool distribution and `tool_choice` configuration.
- `ts_2_4_mcp_server_integration/`: Project `.mcp.json` configuration, env var expansion, and MCP Resources.
- `ts_2_5_builtin_tools_usage/`: Built-in tool selection engine and surgical `Edit` fallback workflow.
