---
trigger: always_on
description: Enforce Extended Thinking parameters, context preservation, and GitHub Mermaid rendering rules.
---

# Rule: Context Management, Thinking Parameters & Mermaid Standards

## 1. Extended Thinking & Sampling Rule (Claude 4.5)
- **Model Standard**: Use `claude-sonnet-4-5` or `claude-haiku-4-5`.
- **Temperature Omission**: When `thinking` is enabled (`thinking={"type": "enabled", "budget_tokens": ...}`), **do not provide `temperature`** (rejected with HTTP `400`). Safest: also leave `top_k` and `top_p` unset (newer models reject any non-default sampling value). With manual extended thinking use only `tool_choice` `auto` or `none`.
- **Thinking Continuity**: In multi-turn loops, assistant reasoning blocks (`type: "thinking"`) must be returned **unmodified** with their cryptographic `signature` in subsequent turns. Stripping thinking blocks causes an API `400 Bad Request` error.

## 2. Context Window Preservation (Domain 5)
- **Case Facts Layer**: Store transactional entities (order IDs, customer details, timestamps) in a dedicated block outside summarized history.
- **Tool Trimming**: Use `PostToolUse` normalization hooks to strip irrelevant fields from raw tool payloads before appending to conversation context.
- **Exploration Scratchpads**: Use scratchpads and `/compact` during large codebase investigations to avoid context degradation.

## 3. GitHub Mermaid Standards (October 2026)
- **Quoted Labels**: Wrap all labels with punctuation, colons, or spaces in double quotes: `Node["Clean Text"]`.
- **No Raw HTML**: Never use `<b>` or `</b>` inside node labels. Use `<br>` inside double quotes for line breaks.
- **No Init Directives**: Never include `%%{init: ...}%%` blocks.
- **Explicit Layout**: Always declare `flowchart TD` or `flowchart LR`.
- **Safe Edges**: Use `-->|"Text"|` or `-- "Text" -->`.
