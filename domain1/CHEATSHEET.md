# Domain 1 Cheatsheet: Agentic Architecture & Orchestration (27%)

One-page revision. **Not a copy of [KEY_CONCEPTS.md](KEY_CONCEPTS.md)**: that file explains the concepts, the golden rules and the anti-pattern teardown. This sheet only adds four things for last-minute review: question wording to answer, look-alike pairs, exact values, and elimination filters. Worked traps with code are in each study guide (links at the bottom).

---

## 1. Question wording → answer

| If the question says... | Choose | Reject | TS |
|---|---|---|---|
| Loop ends too early, hangs, or ends on a phrase like "done" | Branch on `stop_reason` | Text or regex check, `range(N)` as the exit | 1.1 |
| Response cut off, last `tool_use` looks incomplete | Do not run it. Raise `max_tokens` or stop with an error | Treat as `end_turn`, run partial input | 1.1 |
| Agent sometimes skips a required step ("always", "compliance", "identity first") | Code gate on session state | Stronger prompt, few-shot, routing classifier | 1.4 |
| A limit must hold (amount, destructive action) | `PreToolUse` hook that denies with a reason | Prompt rule, "undo afterwards" | 1.5 |
| Tool results are messy, mixed formats, 40+ fields | `PostToolUse` hook normalises and trims | Ask Claude to convert or ignore fields | 1.5 |
| Report misses a whole topic, but each subagent's output is correct | Fix the coordinator's decomposition | Improve search or synthesis subagent | 1.2 |
| Several independent subagents, results slow | Several `Task` calls in one response | One `Task` per turn | 1.3 |
| Subagents defined but never used | Add `"Task"` to coordinator `allowedTools` | More agent definitions | 1.3 |
| Subagent lacks facts or invents context | Put facts in its prompt | Assume inherited history | 1.2, 1.3 |
| Uneven review of a large PR | Per-file passes plus an integration pass | Smaller PRs, bigger model, 3-run consensus | 1.6 |
| "Add tests to an unfamiliar legacy codebase" | Map, prioritise, adapt (dynamic) | Fixed script written up front | 1.6 |
| Customer asks for a human | Escalate now with a structured summary | Ask why, or escalate on sentiment | 1.4 |
| Resuming after files changed | Resume and name them, or fresh session plus summary | Resume and say nothing | 1.7 |
| Compare two designs | Fork | Both in one thread | 1.7 |

---

## 2. Look-alike pairs

| Pair | Difference |
|---|---|
| `tool_use` / `end_turn` / `pause_turn` / `max_tokens` / `refusal` | Run tools and continue / finished / resume with assistant turn unchanged / truncated, not success / surface it |
| Safety cap vs completion signal | Cap (`MAX_ITERATIONS`, or `--max-turns` in print mode, which exits with an error) catches bugs. `stop_reason` is the only normal exit |
| Code gate vs `PreToolUse` hook | Both deterministic. Gate = your own check on workflow state in the tool layer. Hook = SDK interception point before the tool runs |
| `PreToolUse` vs `PostToolUse` | Before the tool: block or rewrite input. After the tool, before context: normalise, trim, redact. `PostToolUse` cannot undo the action |
| Prompt chaining vs adaptive decomposition | Steps known up front vs steps discovered while working |
| Resume vs fork vs fresh | Same valid history / branch from a baseline / history is stale, carry a summary |
| `is_error` vs `isError` | Messages API `tool_result` (snake_case) vs MCP result (camelCase) |
| Hub-and-spoke vs mesh | All traffic via coordinator vs agents talk to each other |
| Pass 1 vs Pass 2 | Per-file local issues vs cross-file contracts using compact finding cards |

---

## 3. Exact values and names

- Thinking: `budget_tokens` at least 1024 and below `max_tokens`. Thinking tokens count against `max_tokens`. No `temperature`. `tool_choice` only `auto` or `none` with manual thinking.
- Echo `thinking` blocks with their `signature` unchanged, or HTTP 400.
- Hooks (Agent SDK docs): events are case-sensitive (`PreToolUse`). Matchers match tool names only, not file paths (check `tool_input` inside the hook). Matching hooks run in parallel. Decision priority when they disagree: `deny` over `defer` over `ask` over `allow`. A `PreToolUse` hook that times out blocks the call (fail closed).
- `PreToolUse` output: `permissionDecision` (`allow`, `deny`, `ask`, `defer`), `permissionDecisionReason`, `updatedInput`. `PostToolUse` output: `additionalContext`, `updatedToolOutput`.
- Sessions: `claude --resume <id or name>`, `-n` to name, `--fork-session` to branch. SDK: `resume=` and `fork_session=True`.
- Models in this repo: `claude-sonnet-4-5` (coordinator, reasoning), `claude-haiku-4-5` (workers).
- Subagent topology: flat. Leaf subagents do not spawn further subagents.

---

## 4. Elimination filters (reject on sight)

1. Any option that reads Claude's text to decide the loop is finished.
2. Any option that enforces a hard rule with wording only (prompt, few-shot, "be careful").
3. Any option that lets subagents talk to each other or inherit history.
4. Any option whose fix is "bigger model", "bigger window", "vote three times", or "smaller PR" for a structure problem.
5. Any option that acts first and corrects later (refund, then reverse).
6. Any option that treats a safety cap as the normal exit.

---

## Where the detail is

[1.1](ts_1_1_multi_tool_agent_loop/README.md) · [1.2](ts_1_2_coordinator_subagents/README.md) · [1.3](ts_1_3_subagent_invocation_spawning/README.md) · [1.4](ts_1_4_prerequisite_enforcement/README.md) · [1.5](ts_1_5_sdk_hooks/README.md) · [1.6](ts_1_6_task_decomposition/README.md) · [1.7](ts_1_7_session_management/README.md)
