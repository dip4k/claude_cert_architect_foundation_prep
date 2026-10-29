# Architect Candidate Evaluation Rubric

Evaluate candidate responses across core dimensions (1–10 points each):

| Dimension | Novice (1–4) | Competent (5–7) | Senior Architect (8–10) |
|---|---|---|---|
| **1. Determinism vs. Probabilism** | Relies entirely on system prompt warnings for critical security/financial gates. | Combines prompts with regex text parsing to detect intent. | Enforces strict programmatic gates, prerequisite verification, or SDK hooks (`PostToolUse`) before executing sensitive tools. |
| **2. Context Window Efficiency** | Dumps full API responses and entire codebase files into conversational context. | Summarizes conversation history but loses critical identifiers (order IDs, dates). | Implements persistent immutable "Case Facts" layer outside summaries, trims tool output fields, uses progressive discovery (Grep -> chunked Read), keeps `CLAUDE.md` <200 lines. |
| **3. Tool Design & MCP** | Exposes 15+ overlapping tools to a single agent; throws raw string exceptions on failure. | Limits tools but allows ambiguous descriptions; uses generic error codes. | Strictly enforces least privilege (4–5 tools per agent); provides input examples and boundaries; returns structured error contracts (`isError`, categories, `isRetryable`). |
| **4. Cost & Latency Strategy** | Suggests Message Batches API for interactive/blocking CI checks, or runs subagents sequentially. | Uses parallel calls but forgets custom_id correlation or error retry bounds. | Correctly pairs Batches API with non-blocking 24h jobs (50% savings); parallelizes subagents in single turn; handles rate limits gracefully. |
| **5. Reliability & Provenance** | Averages conflicting figures or ignores data discrepancies; audits only high-error cohorts. | Flags conflicts but lacks structured citations; conducts random sampling without segmentation. | Preserves conflicting data with explicit timestamps and citations; implements stratified random sampling (5–10% of high-confidence results) to detect silent drift. |
| **6. API Parameters & Thinking Continuity** | Passes temperature with Extended Thinking (causing 400 error); strips thinking blocks from conversation history. | Removes temperature but relies on default thinking without budgeting; inconsistent block echoing. | Omits temperature completely when thinking is active; calibrates `budget_tokens`; preserves assistant thinking blocks verbatim with signatures in multi-turn history. |

## Scoring Scale:
- **50–60**: Principal / Lead Architect (Ready to pass CCAR-F with 900+ score).
- **42–49**: Senior AI Engineer / Architect (Passing range $\ge 720/1000$).
- **30–41**: Mid-Level Developer (Needs focused remediation on Domain 1 & 5).
- **< 30**: Fundamental review required (Focus on 15 Golden Rules).
