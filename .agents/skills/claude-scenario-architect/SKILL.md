---
name: claude-scenario-architect
description: Architectural blueprints, SLA requirements, decision trees, Claude 4.5 thinking standards, and trade-off rationales for the 6 production scenarios.
---

# The 6 Production Scenarios Architecture Guide

On the CCAR-F exam and in senior AI architect interviews, system design questions are anchored in these 6 production scenarios. Use this guide to quickly evaluate architectural trade-offs, SLAs, and anti-patterns.

---

## 🧭 Scenario Decision Matrix

| Scenario | Core SLA | Key Task Statements | Golden Architectural Pattern | Anti-Patterns to Reject |
|---|---|---|---|---|
| **1. Customer Support** | $\ge 80\%$ First Contact Resolution (FCR) | TS 1.4, 2.1, 2.2, 5.1, 5.2 | Programmatic gates before refunds; immediate escalation on customer demand; trim tool outputs (45 $\rightarrow$ 4 fields); persistent "Case Facts" block. | Relying on prompts to block refunds; refusing escalation; dumping raw DB responses into history; setting temperature with thinking. |
| **2. Code Generation** | Zero-assumption engineering across multi-tier repos | TS 3.1, 3.2, 3.3, 3.4, 3.5 | Path-scoped rules in `.claude/rules/`; Plan Mode for multi-file/architectural refactors; Direct Execution for localized 1-file fixes; Interview Pattern on ambiguity. | Using Plan Mode for 1-line typo fixes; editing files without reading them; guessing user intent without clarifying; bloated `CLAUDE.md` (>200 lines). |
| **3. Multi-Agent Research** | Verifiable market report with cited source provenance | TS 1.2, 1.3, 2.4, 5.3, 5.6 | Hub-and-Spoke coordinator; parallel `Task` spawning in single turn; distinguish `VALID_EMPTY` (0 hits) vs `UPSTREAM_FAILURE`; preserve conflicting stats with dates. | Passing full history to subagents; sequential subagent turns; averaging conflicting numbers; stripping thinking blocks from history. |
| **4. Dev Productivity** | Safe exploration of large legacy codebases | TS 1.7, 2.3, 2.4, 2.5 | Progressive discovery: `Glob` $\rightarrow$ `Grep` $\rightarrow$ chunked `Read`; Edit Fallback: expand anchor text or fallback to `Read + Write`; expose catalogs as MCP Resources. | Reading entire repository upfront; repeating failed `Edit` tool calls indefinitely; creating tools for read-only static docs. |
| **5. CI/CD Code Review** | Non-blocking PR gatekeeper and review bot | TS 3.6, 4.1, 4.5, 4.6 | Headless `-p` flag + `--output-format json`; Two-pass review (file-level correctness + cross-file integration); independent review instance (no author bias). | Omitting `-p` (causes CI runner hang); using Message Batches API for blocking PR checks (24h latency); Claude self-reviewing own PR. |
| **6. Data Extraction** | Zero-hallucination entity extraction from receipts | TS 4.3, 4.4, 4.5, 5.5 | `tool_use` schema enforcement; `nullable: true` for missing-prone fields; validation-retry loops; 10% stratified random audit across all confidence bands. | Required non-nullable fields on optional data; retrying when source data is fundamentally absent; auditing only low-confidence outputs. |

---

## ⚡ API Standards & Extended Thinking Rules
- **Model Standard**: Use `claude-sonnet-4-5` for orchestrators/complex reasoning; `claude-haiku-4-5` for subagents and extraction.
- **The Temperature Trap**: When Extended Thinking (`thinking={"type": "enabled", "budget_tokens": ...}`) is active, `temperature` **must be omitted**. Passing temperature raises an HTTP `400 Bad Request` error.
- **Thinking Continuity**: Never strip assistant `thinking` blocks from multi-turn history; echo them verbatim with their signature.

---

## 📊 October 2026 Mermaid Architecture Standards
All architectural diagrams must follow modern GitHub Mermaid standards:
- Wrap all labels with punctuation, colons, or spaces in double quotes: `Node["Clean Label"]`.
- Explicit flow direction (`flowchart TD` or `flowchart LR`).
- No raw HTML tags like `<b>` or `</b>` inside node labels. Use `<br>` inside double quotes for line breaks.
- No fragile `%%{init: ...}%%` directives.

---

## 🎯 Production Scenario Labs (Deep Dive)
- **Scenario 1**: [`scenarios/scenario_1_customer_support/SCENARIO_GUIDE.md`](scenarios/scenario_1_customer_support/SCENARIO_GUIDE.md)
- **Scenario 2**: [`scenarios/scenario_2_code_generation/SCENARIO_GUIDE.md`](scenarios/scenario_2_code_generation/SCENARIO_GUIDE.md)
- **Scenario 3**: [`scenarios/scenario_3_multi_agent_research/SCENARIO_GUIDE.md`](scenarios/scenario_3_multi_agent_research/SCENARIO_GUIDE.md)
- **Scenario 4**: [`scenarios/scenario_4_developer_productivity/SCENARIO_GUIDE.md`](scenarios/scenario_4_developer_productivity/SCENARIO_GUIDE.md)
- **Scenario 5**: [`scenarios/scenario_5_continuous_integration/SCENARIO_GUIDE.md`](scenarios/scenario_5_continuous_integration/SCENARIO_GUIDE.md)
- **Scenario 6**: [`scenarios/scenario_6_structured_data_extraction/SCENARIO_GUIDE.md`](scenarios/scenario_6_structured_data_extraction/SCENARIO_GUIDE.md)

---

## ⚡ Critical Anti-Patterns & Traps
Detailed teardowns of common exam distractors and failure modes are documented in [The Critical Exam Traps](./references/exam_traps.md).
