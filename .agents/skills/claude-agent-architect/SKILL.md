---
name: claude-agent-architect
description: Core architectural patterns for loop control (stop_reason), programmatic gates vs prompts, multi-agent topologies, and MCP error contracts.
---

# Claude Agent Architect Guide

## Core Architectural Decision Matrix

### 1. Loop Control
- **Correct**: Inspect `response.stop_reason` (`"tool_use"` -> execute tool & loop; `"end_turn"` -> complete & return).
- **Anti-patterns**: Checking for presence of assistant text, parsing keywords in response, relying on iteration counter as primary exit.

### 2. Programmatic Enforcement vs Prompt Instructions
- **Rule**: When deterministic compliance is required (e.g. identity verification, financial thresholds, irreversible actions), use **programmatic prerequisites/hooks**.
- **Rationale**: Prompt instructions have a non-zero failure rate under high ambiguity or adversarial context.

### 3. Multi-Agent Systems
- **Topology**: Hub-and-Spoke (Coordinator manages all subagent routing, aggregation, and error handling).
- **Context Isolation**: Subagents **do not** inherit coordinator conversation history. Pass all required findings and metadata explicitly in the prompt.
- **Parallel Spawning**: Emit multiple `Task` tool calls in a single coordinator response.

### 4. Tool Design & MCP
- **Routing**: Differentiated descriptions with clear boundaries, input formats, and examples.
- **Errors**: Return `isError: true` with structured categories (`transient`, `validation`, `business`, `permission`) and `isRetryable: bool`.
- **Distribution**: 4–5 tools per agent (principle of least privilege).
- **Resources vs Tools**: MCP resources for content catalogs / reading; MCP tools for actions.

### 5. Structured Output
- **Guaranteed Structure**: Use `tool_use` with strict JSON schema (eliminates JSON syntax errors).
- **Preventing Hallucination**: Use `nullable: true` (or optional) for fields that may be absent from source documents.
- **Extensibility**: Enum values + `"other"` with detail string.

### 6. Context Window Management
- **Fact Persistence**: Extract transactional facts (order ID, refund amount) into a persistent "case facts" block outside summarized history.
- **Trimming**: Trim verbose tool outputs before appending to conversation context.
- **Positioning**: Place key findings at the beginning and end to avoid the "lost in the middle" effect.
