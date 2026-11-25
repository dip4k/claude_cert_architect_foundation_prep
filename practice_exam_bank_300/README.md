# CCAR-F Exam Practice Question Bank (385 Questions)
### Claude Certified Architect – Foundations (CCAR-F)
**Aligned with the Official CCAR-F 27 Task Statements, Claude 4.5 Family, and Production Agentic Architectures**

---

## 📋 Exam Blueprint & Domain Distribution

The CCAR-F exam evaluates real-world architectural decision-making, failure recovery, token economics, and governance across 60 scenario-based questions in a 120-minute testing window (passing score: **720 / 1000**).

This question bank provides **385 scenario-based practice questions** (`Q1 – Q385`) with balanced answer keys (`A/B/C/D` and `A–E` multi-response), collapsible `<details>` answer & explanation blocks, full option-by-option breakdowns, and Anti-Pattern alerts:

> **Note on File Naming vs. Official Blueprint Domain Numbers:** Sets 04–09 keep their original filenames (`set_04_domain2...` through `set_09_domain4...`) so existing study links across `scenarios/` remain intact. Use the **Official Blueprint Mapping** column below to match each set to [EXAM_BLUEPRINT.md](../EXAM_BLUEPRINT.md).

| Study Track / Set Group | Official Blueprint Domain (Weight) | Question Range | Total Questions | Focus Areas |
| :--- | :--- | :---: | :---: | :--- |
| **Sets 01 – 03** | **Domain 1:** Agentic Architecture & Orchestration (**27%**) | Q1 – Q95 | **95** | Core loop (`stop_reason`), Hub-and-Spoke vs. Mesh, subagent context isolation, extended thinking continuity, state checkpointing, circuit breakers. |
| **Sets 04 – 05** | **Domain 3:** Claude Code Configuration & Workflows (**20%**) | Q96 – Q155 | **60** | Config hierarchy (`Managed` → `.claude/` → `~/.claude/` → `CLI`), `CLAUDE.md` (<200 lines), path-scoped rules, skills with `context: fork`, Plan Mode, headless CI/CD (`-p`, `--bare`, `--output-format json`). |
| **Sets 06 – 07** | **Domain 4:** Prompt Engineering & Structured Output (**20%**) + **Domain 5** Context | Q156 – Q215 | **60** | Prompt caching prefix rules (`cache_control`), TTL resets, constrained decoding (`output_config.format` / `tool_use`), XML boundaries, Case Facts layer, `PostToolUse` trimming, token economics. |
| **Sets 08 – 09** | **Domain 2:** Tool Design & MCP Integration (**18%**) | Q216 – Q275 | **60** | JSON Schema descriptions, `tool_choice` constraints with thinking, actionable error feedback (`is_error` / `isError`), MCP primitives (`tools/*`, `resources/*`, `prompts/*`), OAuth 2.1, progressive tool discovery. |
| **Set 10** | **Domain 5:** Context Management, Reliability & Governance (**15%**) | Q276 – Q305 | **30** | Autonomy Spectrum, Approval Fatigue, DLP sanitization, Least Privilege environment isolation, audit trails, OpenTelemetry tracing. |
| **Set 11** | **Cross-Domain High-Yield CCAR-F Gaps** (**TS 1.7, 2.4–2.5, 3.1–3.5, 4.1–4.6, 5.2–5.6**) | Q306 – Q345 | **40** | Closed-loop extraction retries, fast-fail on missing facts, two-pass PR review & independent sessions, `VALID_EMPTY` vs. `UPSTREAM_FAILURE`, Simpson's Paradox & 5–10% stratified audits, nullable schemas, escalation & disambiguation, session forking, `Glob`/`Grep`/`Edit` fallback, Batch SLA math. |
| **Set 12** | **Full-Spectrum Exam Simulation: Complex Passages & Multi-Response** (**All 5 Domains · TS 1.1–5.6 · Scenarios 1–6**) | Q346 – Q385 | **40** | Long multi-paragraph scenario passages (72–157 word stems), embedded JSON/YAML/Python/CI artifacts, realistic tie-breaker distractors, and 10 **"Select two"** (`A–E`) multi-response items across all 6 scenarios and 30 task statements. |
| **TOTAL** | **All 5 Domains (TS 1.1 – 5.6)** | **Q1 – Q385** | **385** | **Full syllabus, scenario, passage, and multi-select coverage.** |

---

## 📁 Question Sets Index

Each set is saved in a dedicated markdown file with complete answers, option-by-option explanations, and Anti-Pattern alerts:

1. [Set 1: Core Agentic Loop & Stop Reasons (Q1 – Q30)](set_01_domain1_core_agentic_loop.md)
   * `stop_reason` transitions (`tool_use`, `end_turn`, `max_tokens`, `stop_sequence`)
   * Appending full assistant messages before tool results
   * Extended thinking budget constraints and temperature restrictions
   * Parallel tool executions and client validation gates

2. [Set 2: Multi-Agent Topologies & Orchestration Patterns (Q31 – Q65)](set_02_domain1_multi_agent_topologies.md)
   * Hub-and-Spoke coordinator standards vs. Peer-to-Peer mesh chaos
   * Subagent context isolation and explicit context construction
   * Context Starvation vs. Overly Narrow Decomposition
   * Parallel fan-out concurrency with rate limiters and semaphores
   * Producer-Critic / Verifier subagent patterns

3. [Set 3: Extended Thinking, State Management & Resilient Loops (Q66 – Q95)](set_03_domain1_extended_thinking_state.md)
   * Cryptographic signatures in thinking blocks and multi-turn continuity
   * Context degradation ("Lost in the Middle") mitigation
   * Handling HTTP 429 / 529 errors with exponential backoff and jitter
   * Durable checkpointing and state externalization
   * Indirect prompt injection via tool results

4. [Set 4: Configuration Hierarchy & CLAUDE.md Scoping (Q96 – Q125)](set_04_domain2_claude_code_config.md)
   * Configuration hierarchy (`Managed` → Project `.claude/` → User `~/.claude/` → `CLI`)
   * Enterprise managed immutable security floors
   * Keeping `CLAUDE.md` under 200 lines to prevent prompt saturation
   * Modular path-scoped rules in `.claude/rules/`
   * Toolchain pinning, TDD guidance, and secret protection

5. [Set 5: Skills, Subagents, Plan Mode & Headless CI/CD (Q126 – Q155)](set_05_domain2_skills_subagents_headless.md)
   * Modular Skills discovery and YAML frontmatter (`paths`, `effort`)
   * Isolated execution with `context: fork`
   * Plan Mode (`Shift+Tab`, `/plan`, `useAutoModeDuringPlan`)
   * Headless automation (`-p`, `--bare`, `--output-format json`, inline `--json-schema`)
   * Session resumption (`--resume <session_id>`) and pre-commit hooks

6. [Set 6: Prompt Caching & Token Economics (Q156 – Q185)](set_06_domain3_prompt_caching_economics.md)
   * Strict prefix rule (Tools → System → Messages)
   * Dynamic prefix invalidation (the timestamp anti-pattern)
   * Sliding TTL resets and 4-breakpoint limits
   * Token usage breakdown (`cache_creation_input_tokens`, `cache_read_input_tokens`)
   * Batch Processing API (50% discount) and high-throughput routing

7. [Set 7: Structured Outputs & Context Preservation (Q186 – Q215)](set_07_domain3_structured_outputs_prompting.md)
   * Constrained decoding via native grammar constraints (`output_config.format`)
   * Structural XML tag boundary enforcement
   * Case Facts Layer for invariant entity persistence
   * `PostToolUse` normalization hooks to strip raw data dumps
   * Golden Dataset evaluation harnesses and LLM-as-a-Judge

8. [Set 8: Tool Schemas, `tool_choice` & Error Handling (Q216 – Q245)](set_08_domain4_tool_schemas_error_handling.md)
   * High-accuracy tool and parameter descriptions in JSON Schema
   * `tool_choice` mechanics (`auto`, `any`, `tool`) and thinking incompatibilities
   * Diagnostic error recovery with `is_error: true`
   * Idempotent tool design and idempotency keys
   * Granular vs. consolidated tools and SQL argument injection defense

9. [Set 9: MCP Architecture & Specification Patterns (Q246 – Q275)](set_09_domain4_mcp_architecture_stateless.md)
   * Core primitives: Tools (`tools/*`), Resources (`resources/*`), Prompts (`prompts/*`)
   * Stateless request/response scaling, header-based routing, and cacheable lists (`ttlMs`)
   * Templated resource URIs, subscriptions (`listChanged`), and OAuth 2.1 hardening
   * Progressive tool discovery to eliminate Tool Bloat

10. [Set 10: Governance, Safety, Risk Management & Anti-Patterns (Q276 – Q305)](set_10_domain5_governance_safety_risk.md)
    * The Autonomy Spectrum: Plan → Approval Gates → Auto-Execution
    * The Approval Fatigue Trap (~93% blind approval rate) and Intent-Based Scoping
    * DLP sanitization middleware and environment isolation
    * EU AI Act Article 14 audit logging and OpenTelemetry tracing
    * The "Context Trap", "Prompt-as-a-Firewall", and "God-Mode Connection" anti-patterns

11. [Set 11: Official Blueprint High-Yield Scenarios & Undercovered Task Statements (Q306 – Q345)](set_11_ccar_f_high_yield_scenarios.md)
    * Closed-loop math retries, `< 0.02` rounding epsilon, and fast-failing on absent source facts (TS 4.4)
    * Two-pass PR review, independent review sessions, untrusted PR description isolation, and comment deduplication (TS 4.6)
    * `VALID_EMPTY` vs. `UPSTREAM_FAILURE`, `PARTIAL_COVERAGE` reporting, and non-crashing `asyncio.gather` wrappers (TS 5.3)
    * Simpson's Paradox, confidence routing tiers, and 5–10% stratified random auditing (TS 5.5)
    * Negative boundaries in rubrics, nullable `["string", "null"]` fields, `"other"`/`"unclear"` enums, multi-page tables, and two-pass thinking + schema extraction (TS 4.1, 4.3)
    * Immediate escalation on human demand, empathy vs. sentiment escalation, duplicate customer disambiguation, and preserving conflicting stats (TS 5.2, 5.6)
    * `--fork-session` + git branches, `STATE_SUMMARY.md` post-rebase recovery, `Glob` → `Grep` → chunked `Read`, 3-stage `Edit` fallback, `.mcp.json` `${ENV_VAR}`, `@import`/`/memory`, nested globs, Interview Pattern, and Batch SLA math (TS 1.7, 2.4, 2.5, 3.1, 3.3, 3.5, 4.5)

12. [Set 12: Full-Spectrum Exam Simulation — Complex Passages & Multi-Response ("Select Two") Items (Q346 – Q385)](set_12_ccar_f_exam_simulation_passages.md)
    * Dense, multi-paragraph production scenario passages across all 6 Scenarios and all 30 Task Statements (`TS 1.1 – 5.6`)
    * 10 **"Select two"** (`A–E`) multi-response items testing paired architectural controls (e.g., Hub-and-Spoke + isolated briefs, `PreToolUse` + `PostToolUse`, `VALID_EMPTY` + `UPSTREAM_FAILURE`, `Glob/Grep/Read` + 3-stage `Edit`, `tool_use` + nullable schemas)
    * Embedded Python loops, JSON schemas, `.claude/rules/` YAML frontmatter, and GitHub Actions CI configs with realistic tie-breaker distractors

---

## 🎯 Master Anti-Pattern Glossary Tested

This question bank tests every major architectural anti-pattern encountered in enterprise Claude deployments:

1. **Orphaned Tool Result**: Discarding intermediate assistant responses and returning bare tool results without preceding `tool_use` blocks.
2. **Thinking Block Mutilation**: Stripping `thinking` content blocks or cryptographic signatures across conversation turns, triggering HTTP 400 errors.
3. **Truncation Blindness**: Treating `stop_reason: "max_tokens"` as normal completion, passing broken code or half-formed JSON into production.
4. **Unbounded Autonomous Loop**: Writing `while True` loops without hard iteration ceilings or retry circuit breakers.
5. **Peer-to-Peer Agent Mesh**: Connecting autonomous agents in a direct cross-talk web without a central coordinator, destroying audit trails.
6. **Context Inheritance Bloat**: Automatically copying the coordinator's entire 50k-token conversation history into spawned subagents.
7. **Context Starvation**: Delegating complex tasks using cryptic one-line prompts without providing necessary environment variables or schemas.
8. **Monolithic `CLAUDE.md`**: Stuffing 2,000+ lines of general company wikis into root `CLAUDE.md`, saturating the prompt and diluting model focus.
9. **Dynamic Prefix Invalidation**: Placing timestamps, request IDs, or variable counters at the top of prompts, permanently breaking prompt caching.
10. **Cache Thrashing**: Alternating rapidly between unrelated massive corpuses before amortizing cache write premiums.
11. **Probabilistic Formatting Reliance**: Begging the model in natural language to "please return valid JSON" instead of using constrained decoding or `tool_use`.
12. **Forced Required Field Hallucination**: Marking optional or absent-prone fields as mandatory non-null strings, compelling the model to invent values.
13. **Blind Retry & Absent-Fact Retry**: Re-sending failed prompts without exact validation deltas, or retrying when a fact does not exist in the source document.
14. **Raw Tool Ingestion Bloat**: Appending unparsed megabyte JSON dumps directly into conversation history without `PostToolUse` normalization.
15. **Tool Proliferation (Bloat)**: Exposing 50+ competing tools simultaneously, causing model hesitation, latency spikes, and incorrect selections.
16. **Silent Tool Fallback**: Catching exceptions and returning dummy mock data or empty arrays with `is_error: false` / `isError: false`, masking outages.
17. **Prompt-As-Permission**: Relying on prompt promises for authorization instead of enforcing role-based access control (RBAC) and code gates at the tool layer.
18. **Author Confirmation Bias**: Asking the same session that generated code to review its own PR instead of spinning up an independent review instance.
19. **Aggregate Accuracy Fallacy (Simpson's Paradox)**: Disabling human review because overall accuracy is 98%, masking 40% error rates on niche document types.
20. **Approval Fatigue Trap**: Forcing human operators to approve every minor file read or grep query, leading to ~93% blind approval rates.
21. **The Context Trap**: Leaving agents without factual grounding, causing them to hallucinate fake endpoints, credentials, or mock state.
22. **Opaque Audit Trails**: Discarding intermediate tool arguments and system calls, leaving the enterprise unable to explain or defend AI actions.
