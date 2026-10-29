---
name: claude-agent-architect
description: Core loop patterns (stop_reason), thinking block continuity, programmatic gates, multi-agent topologies, MCP error contracts, and Mermaid standards.
---

# Claude Agent Architect Guide

## Core Architectural Decision Matrix

### 1. Loop Control (TS 1.1)
- **Correct**: Inspect `response.stop_reason` (`"tool_use"` -> execute tool & loop; `"end_turn"` -> complete & return).
- **Anti-patterns**: Checking for presence of assistant text, parsing keywords in response, relying on iteration counter as primary exit.
- **Thinking Block Continuity**: When Extended Thinking is enabled, assistant reasoning blocks (`type: "thinking"`) must be returned **unmodified with their signature** in subsequent assistant history. Stripping them throws an HTTP `400 Bad Request` error.

### 2. Extended Thinking & Sampling (Claude 4.5 Standard)
- **Model Standard**: Default to `claude-sonnet-4-5` or `claude-haiku-4-5`.
- **Temperature Rule**: When `thinking={"type": "enabled", "budget_tokens": ...}` is enabled, **omit `temperature` entirely**. Passing custom temperature causes an API 400 error.
- **Budget Calibration**: Set `budget_tokens >= 1024` and strictly less than `max_tokens`.

### 3. Programmatic Enforcement vs Prompt Instructions (TS 1.4)
- **Rule**: When deterministic compliance is required (e.g. identity verification, financial thresholds, irreversible actions), use **programmatic prerequisites/hooks**.
- **Rationale**: Prompt instructions have a non-zero failure rate under high ambiguity or adversarial context.

### 4. Multi-Agent Systems (TS 1.2, 1.3)
- **Topology**: Hub-and-Spoke (Coordinator manages all subagent routing, aggregation, and error handling).
- **Context Isolation**: Subagents **do not** inherit coordinator conversation history. Pass all required findings and metadata explicitly in the prompt.
- **Parallel Spawning**: Emit multiple `Task` tool calls in a single coordinator response.

### 5. Tool Design & MCP (TS 2.1, 2.2, 2.3, 2.4)
- **Routing**: Differentiated descriptions with clear boundaries, input formats, and examples.
- **Two Error Channels**: Protocol errors (JSON-RPC) vs tool execution errors (`isError: true`).
- **Structured Errors**: Return `isError: true` with `errorCategory` (`transient`, `validation`, `business`, `permission`) and `isRetryable: bool`.
- **Distribution**: 4–5 tools per agent (principle of least privilege).
- **Resources vs Tools**: MCP resources for content catalogs / reading; MCP tools for actions.

### 6. Structured Output (TS 4.3, 4.4)
- **Guaranteed Structure**: Use `tool_use` with strict JSON schema (eliminates JSON syntax errors).
- **Preventing Hallucination**: Use `nullable: true` (or optional) for fields that may be absent from source documents.
- **Extensibility**: Enum values + `"other"` with detail string.

### 7. Context Window Management (TS 5.1, 5.2, 5.4)
- **Fact Persistence**: Extract transactional facts (order ID, refund amount) into a persistent "case facts" block outside summarized history.
- **Trimming**: Trim verbose tool outputs via `PostToolUse` before appending to conversation context.
- **Positioning**: Place key findings at the beginning and end to avoid the "lost in the middle" effect.

### 8. GitHub Mermaid Architecture Standards (October 2026)
- Wrap all node labels with punctuation, colons, or spaces in double quotes: `Node["Clean Label"]`.
- Explicit flow direction: `flowchart TD` or `flowchart LR`.
- No raw HTML tags like `<b>` or `</b>` inside node labels. Use `<br>` inside double quotes for line breaks.
- No fragile `%%{init: ...}%%` directives.
