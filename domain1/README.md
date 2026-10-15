# Domain 1: Agentic Architecture & Orchestration (27% of Exam)

Domain 1 represents the highest-weighted domain on the **Claude Certified Architect – Foundations (CCAR-F)** exam (27%). It covers designing and implementing autonomous agentic systems using Claude and the Claude Agent SDK.

> 📖 **Deep Dive Master Guide**: For exhaustive technical explanations, architecture diagrams, sequence flows, gotchas, to-remember points, and practical scenario questions & answers, see [KEY_CONCEPTS.md](KEY_CONCEPTS.md).

---

## 📋 Task Statements & Core Architectural Principles

### [TS 1.1: Design and Implement Agentic Loops for Autonomous Task Execution](ts_1_1_multi_tool_agent_loop/main.py)
- **Loop Lifecycle**: `client.messages.create()` -> inspect `response.stop_reason` -> if `"tool_use"`, append assistant message, execute tools, append user message with `tool_result` blocks -> repeat until `"end_turn"`.
- **Sole Deterministic Signal**: `response.stop_reason == "end_turn"` is the only reliable signal of task completion.
- **Anti-Patterns**: Parsing assistant text for keywords ("Done", "Complete"), relying on regex, or using loop turn limits as completion triggers.
- **Reference Exercise**: [ts_1_1_multi_tool_agent_loop/](ts_1_1_multi_tool_agent_loop/)

### [TS 1.2: Orchestrate Multi-Agent Systems with Coordinator-Subagent Patterns](ts_1_2_coordinator_subagents/main.py)
- **Hub-and-Spoke Topology**: All communication, state management, audit logging, and routing flows through the coordinator.
- **Context Isolation Contract**: Subagents **do not** inherit coordinator history, memory, or permissions. Subagents start with empty context.
- **Dynamic Routing**: Coordinator dynamically routes by query complexity (direct resolution vs specialized subagent delegation).
- **Iterative Synthesis**: Coordinator evaluates subagent outputs against requirements and re-delegates if gaps exist.
- **Reference Exercise**: [ts_1_2_coordinator_subagents/](ts_1_2_coordinator_subagents/)

### [TS 1.3: Configure Subagent Invocation, Context Passing, and Spawning](ts_1_3_subagent_invocation_spawning/main.py)
- **Spawning Mechanism**: The `Task` tool (must be explicitly whitelisted in `allowedTools` or `tools`).
- **Parallel Spawning**: Emitting multiple `Task` tool use blocks in a single coordinator response/turn enables concurrent subagent execution, reducing latency by 40%–60%.
- **Structured Context**: Separate content/findings from metadata (source URLs, page numbers, timestamps) to preserve provenance.
- **Goal-Oriented Prompts**: Specify clear goals, constraints, and schemas rather than rigid procedural steps.
- **Reference Exercise**: [ts_1_3_subagent_invocation_spawning/](ts_1_3_subagent_invocation_spawning/)

### [TS 1.4: Implement Multi-Step Workflows with Enforcement and Handoff Patterns](ts_1_4_prerequisite_enforcement/main.py)
- **Programmatic Prerequisite Gates**: State machine / code checks (e.g., blocking `process_refund` until `get_customer` verifies ID) provide 100% deterministic compliance guarantees that prompts cannot ensure.
- **Structured Handoff Manifests**: Compile comprehensive case manifests (customer ID, verified identity, issue summary, actions attempted, root cause, recommended action) for human agents.
- **Escalation Triggers**: Immediate escalation on explicit customer demand, unhandled policy gaps, or technical barriers.
- **Reference Exercise**: [ts_1_4_prerequisite_enforcement/](ts_1_4_prerequisite_enforcement/)

### [TS 1.5: Apply Agent SDK Hooks for Tool Call Interception and Data Normalization](ts_1_5_sdk_hooks/main.py)
- **Hook Lifecycle**: `PreToolUse` (interception / gating) and `PostToolUse` (normalization).
- **Interception Hooks**: Enforce hard regulatory, security, and financial boundaries (e.g. blocking transactions > $500).
- **PostToolUse Normalization**: Normalize heterogeneous data (Unix timestamps -> ISO 8601, status codes -> uniform enums, PII redaction) before returning to Claude.
- **Reference Exercise**: [ts_1_5_sdk_hooks/](ts_1_5_sdk_hooks/)

### [TS 1.6: Design Task Decomposition Strategies for Complex Workflows](ts_1_6_task_decomposition/main.py)
- **Attention Dilution**: Large multi-file changes (10+ files) degrade model focus if evaluated in a single prompt.
- **Two-Pass Prompt Chaining**: Pass 1 (isolated per-file analysis for local bugs) + Pass 2 (cross-file integration pass for contracts, shared state, and end-to-end security).
- **Adaptive Decomposition**: Dynamic generation of subtasks based on intermediate discoveries during open-ended troubleshooting.
- **Reference Exercise**: [ts_1_6_task_decomposition/](ts_1_6_task_decomposition/)

### [TS 1.7: Manage Session State, Resumption, and Forking](ts_1_7_session_management/main.py)
- **Session Continuation**: `--resume <session-id>` reloads historical message trails for continuous work.
- **Session Forking**: `fork_session` branches from a shared baseline checkpoint into isolated threads for divergent exploration.
- **Stale Context Trap**: Resuming long sessions after source code changes leads to hallucinations over cached outputs. Remedy: Discard stale session, inject a structured summary into a fresh session.
- **Reference Exercise**: [ts_1_7_session_management/](ts_1_7_session_management/)

---

## 🛠️ Hands-on Exercises in this Domain
- `ts_1_1_multi_tool_agent_loop/`: Standard agentic loop with `stop_reason` control and response logging.
- `ts_1_2_coordinator_subagents/`: Hub-and-spoke research coordinator with isolated subagents and iterative synthesis.
- `ts_1_3_subagent_invocation_spawning/`: Spawning parallel subagents via multiple `Task` tool calls in a single turn.
- `ts_1_4_prerequisite_enforcement/`: Deterministic prerequisite gates and structured human handoff summaries.
- `ts_1_5_sdk_hooks/`: Tool call interception compliance hooks and `PostToolUse` normalization.
- `ts_1_6_task_decomposition/`: Multi-pass prompt chaining (local per-file pass + cross-file integration pass).
- `ts_1_7_session_management/`: Named session resumption (`--resume`), `fork_session`, and injected summaries.
