---
name: architect-eval
description: Evaluates an agent or tool implementation against the Claude Certified Architect Foundations exam criteria
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
argument-hint: "<domain_or_filepath>"
---

# Claude Architect Implementation Evaluator

Evaluate the specified file or domain exercise against the 5 Exam Domains of the Claude Certified Architect – Foundations Certification and October 2026 standards.

## Evaluation Checklist

### 1. Loop Control & Stop Reason (Domain 1: TS 1.1)
- [ ] Uses `response.stop_reason` as the sole signal (`"tool_use"` vs `"end_turn"`).
- [ ] Avoids anti-patterns: parsing assistant text to detect completion, relying solely on iteration caps.
- [ ] Correctly appends `tool_result` content blocks to conversation history.
- [ ] **Thinking Continuity**: Preserves and echoes assistant `thinking` blocks verbatim with their signature in multi-turn history (never strips thinking).

### 2. Multi-Agent & Orchestration (Domain 1: TS 1.2, 1.3)
- [ ] Coordinator delegates to subagents with isolated context.
- [ ] Subagents do not assume automatic context inheritance.
- [ ] Context passing preserves source attribution and metadata.
- [ ] Parallel subagent spawning emits multiple `Task` tool calls in a single response.

### 3. Workflow Enforcement & Hooks (Domain 1: TS 1.4, 1.5)
- [ ] Uses deterministic programmatic prerequisites (hooks or gates) for critical compliance rather than prompt instructions alone.
- [ ] Normalizes heterogeneous tool outputs before model processing.

### 4. Tool & MCP Design (Domain 2: TS 2.1, 2.2, 2.3)
- [ ] Differentiates similar tools with input formats, edge cases, and boundary explanations.
- [ ] Employs structured error responses (`isError: true`, `errorCategory`, `isRetryable`).
- [ ] Distinguishes protocol errors from tool execution errors.
- [ ] Follows principle of least privilege: subagents restricted to 4–5 focused tools.

### 5. Claude 4.5 & Extended Thinking Standards
- [ ] Uses Claude 4.5 model strings (`claude-sonnet-4-5`, `claude-haiku-4-5`).
- [ ] When Extended Thinking is enabled (`thinking={"type": "enabled", "budget_tokens": ...}`):
  - **Omit `temperature` entirely** (avoids HTTP 400 Bad Request error).
  - Ensures `max_tokens > budget_tokens`.

### 6. Structured Output & Reliability (Domain 4 & 5: TS 4.3, 5.1, 5.2)
- [ ] Guaranteed schema enforcement via `tool_use`.
- [ ] Nullable fields for absent data (avoids hallucinations).
- [ ] Explicit escalation criteria and preservation of transactional facts in a dedicated "Case Facts" block outside summarized history.
- [ ] Trims bloated tool payloads via `PostToolUse`.

### 7. Mermaid Rendering Standards (October 2026)
- [ ] All diagrams wrap node labels in double quotes: `Node["Clean Label"]`.
- [ ] No raw HTML tags like `<b>` or `</b>` inside node labels.
- [ ] No fragile `%%{init: ...}%%` directives.
- [ ] Explicit flow directions (`flowchart TD` or `flowchart LR`).

## Output Format
Deliver a structured score (1-5) per relevant domain and actionable recommendations for exam-aligned architectural refactoring.
