# Domain 2 Cheatsheet: Tool Design & MCP Integration (18%)

One-page revision. **Not a copy of [KEY_CONCEPTS.md](KEY_CONCEPTS.md)**: that file explains each task statement and lists the anti-patterns. This sheet adds question wording to answer, look-alike pairs, exact values, and elimination filters. Worked traps with code are in each study guide (links at the bottom).

---

## 1. Question wording → answer

| If the question says... | Choose | Reject | TS |
|---|---|---|---|
| Agent picks the wrong one of two similar tools, descriptions are short | Rewrite descriptions: returns, formats, when and when not | Few-shot, routing layer, merging into one tool | 2.1 |
| Two tools overlap (`analyze_content` / `analyze_document`) | Rename or split by purpose | Keep both plus a prompt rule | 2.1 |
| Descriptions are good but one tool is still over-used | Check system prompt for keyword wording | Only tune descriptions | 2.1 |
| Tool fails and agent cannot decide what to do | `isError` plus category, `isRetryable`, message | "Operation failed" | 2.2 |
| Policy block (refund over limit) | `business`, not retryable | Mark as transient | 2.2 |
| Query worked but found nothing | `isError: false`, `count: 0` | Error "not found" | 2.2 |
| Subagent gets a timeout | Retry locally, propagate only if unresolved, with context | Escalate every error | 2.2 |
| Agent has about 18 tools and misselects | 4 to 5 scoped tools per role | More prompt text | 2.3 |
| Open tool such as `fetch_url` is risky | Constrained tool (`load_document`) | Prompt says "only our docs" | 2.3 |
| A tool must run first | Forced `tool_choice` on turn 1, then back to `auto` | `auto` plus "please call it first" | 2.3 |
| Forced tool together with extended thinking | `auto` with thinking, or force without thinking | `any` or forced with thinking (HTTP 400) | 2.3 |
| Whole team needs a server | `.mcp.json` in the repo | `~/.claude.json` per laptop | 2.4 |
| Server needs a token | `${ENV_VAR}` expansion | Token in the file | 2.4 |
| Agent prefers `Grep` over the MCP tool | Richer MCP tool description | Remove `Grep` | 2.4 |
| Large catalog the agent must browse | MCP resource | Many search-tool calls | 2.4 |
| Find text in files / find files by name | `Grep` / `Glob` | Swapped | 2.5 |
| `Edit` fails, text not unique | Longer anchor, or `Read` + `Write` | Repeat the same `Edit` | 2.5 |

---

## 2. Look-alike pairs

| Pair | Difference |
|---|---|
| `tool_choice` `auto` / `any` / `tool` / `none` | Model decides (may answer in text) / must call some tool / must call this tool / no tools |
| `.mcp.json` vs `~/.claude.json` | Project, shared via git vs personal |
| MCP tool vs MCP resource | Action or query with arguments vs browsable read-only catalog |
| Access failure vs valid empty | `isError: true` (could not check) vs `isError: false` with zero results |
| `transient` / `validation` / `business` / `permission` | Retry / fix input / explain or escalate / stop |
| `isError` (MCP) vs `is_error` (Messages API) | camelCase vs snake_case |
| `--allowedTools` vs `--tools` (Claude Code CLI) | Runs without asking permission vs restricts which built-in tools exist |
| `Read` + `Write` vs `Edit` | Whole file in and out vs targeted unique replacement |

---

## 3. Exact values and names

- Tool name pattern: `^[a-zA-Z0-9_-]{1,128}$`. Prefix names with the service when tools span services (`github_list_prs`).
- Description guidance (Anthropic docs): what it does, when to use it and when not to, what each parameter means, caveats. Aim for at least 3 to 4 sentences. Optional `input_examples` (must be valid against the schema) for complex inputs.
- Tool responses: return only the high-signal fields, with stable identifiers.
- Nuance: the docs also suggest grouping related actions of one resource into one tool with an `action` parameter. The exam trap is merging tools with **different purposes** (`get_customer` + `lookup_order`) to fix misselection.
- `tool_choice` `any` or `tool` prefill the assistant turn, so no text appears before the `tool_use`. A forced tool call skips thinking. Changing `tool_choice` invalidates cached message blocks.
- Manual extended thinking (Claude 4.5): `any` and `tool` give an error. Some newer models reject forced tool use entirely, then use `auto` with `strict: true` tools.
- `strict: true` guarantees schema-valid inputs (needs `additionalProperties: false`).
- `disable_parallel_tool_use: true` inside `tool_choice` gives one tool call per turn, for dependent steps.
- MCP tool names in Claude Code appear as `mcp__<server>__<action>`.
- Server config: `{"mcpServers": {"name": {"command": ..., "args": [...], "env": {"TOKEN": "${TOKEN}"}}}}`.

---

## 4. Elimination filters (reject on sight)

1. Any option that adds a layer (router, classifier, few-shot) before fixing the tool description.
2. Any option with one generic error string.
3. Any option that marks a business rule or zero results as a retryable error.
4. Any option that gives every agent every tool.
5. Any option that puts a credential in a committed file.
6. Any option that combines `any` or a forced tool with manual extended thinking.

---

## Where the detail is

[2.1](ts_2_1_tool_interface_design/README.md) · [2.2](ts_2_2_mcp_structured_errors/README.md) · [2.3](ts_2_3_tool_distribution_and_choice/README.md) · [2.4](ts_2_4_mcp_server_integration/README.md) · [2.5](ts_2_5_builtin_tools_usage/README.md)
