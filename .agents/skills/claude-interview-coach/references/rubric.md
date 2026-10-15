# Architect Candidate Evaluation Rubric

Evaluate candidate responses across 5 core dimensions (1–10 points each, 50 points total):

| Dimension | Novice (1–4) | Competent (5–7) | Senior Architect (8–10) |
|---|---|---|---|
| **1. Determinism vs. Probabilism** | Relies entirely on system prompt warnings for critical security/financial gates. | Combines prompts with regex text parsing to detect intent. | Enforces strict programmatic gates, prerequisite verification, or SDK hooks (`PostToolUse`) before executing sensitive tools. |
| **2. Context Window Efficiency** | Dumps full API responses and entire codebase files into conversational context. | Summarizes conversation history but loses critical identifiers (order IDs, dates). | Implements persistent immutable "Case Facts" layer outside summaries, trims tool output fields, uses progressive discovery (Grep -> chunked Read). |
| **3. Tool Design & MCP** | Exposes 15+ overlapping tools to a single agent; throws raw string exceptions on failure. | Limits tools but allows ambiguous descriptions; uses generic error codes. | Strictly enforces least privilege (4–5 tools per agent); provides input examples and boundaries; returns structured error contracts (`isError`, categories, `isRetryable`). |
| **4. Cost & Latency Strategy** | Suggests Message Batches API for interactive/blocking CI checks, or runs subagents sequentially. | Uses parallel calls but forgets custom_id correlation or error retry bounds. | Correctly pairs Batches API with non-blocking 24h jobs (50% savings); parallelizes subagents in single turn; handles rate limits gracefully. |
| **5. Reliability & Provenance** | Averages conflicting figures or ignores data discrepancies; audits only high-error cohorts. | Flags conflicts but lacks structured citations; conducts random sampling without segmentation. | Preserves conflicting data with explicit timestamps and citations; implements stratified random sampling (5–10% of high-confidence results) to detect silent drift. |

## Scoring Scale:
- **45–50**: Principal / Lead Architect (Ready to pass CCAR-F with 900+ score).
- **36–44**: Senior AI Engineer / Architect (Passing range $\ge 720/1000$).
- **25–35**: Mid-Level Developer (Needs focused remediation on Domain 1 & 5).
- **< 25**: Fundamental review required (Focus on 10 Golden Principles).
