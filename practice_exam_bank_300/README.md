# CCAR-F Exam Practice Question Bank (305 Questions)
### Claude Certified Architect – Foundations (CCAR-F)
**Aligned with the June–July 2026 Exam Blueprint, Modern MCP (2026-07-28), Claude 5.5 Family, and Production Agentic Architectures**

---

## 📋 Exam Blueprint & Domain Distribution

The CCAR-F exam evaluates real-world architectural decision-making, failure recovery, token economics, and governance across 60 scenario-based questions in a 120-minute testing window (passing score: 720 / 1000).

This question bank provides **305 comprehensive scenario-based practice questions** with full option-by-option breakdowns and Anti-Pattern alerts:

| Domain | Exam Weight | Question Range | Total Questions | Focus Areas |
| :--- | :---: | :---: | :---: | :--- |
| **Domain 1: Agent Architecture & Orchestration** | **~27%** | Q1 – Q95 | **95** | Core loop (`stop_reason`), multi-agent topologies (Hub-and-Spoke vs Mesh), subagent context isolation, extended thinking continuity, state checkpointing, circuit breakers. |
| **Domain 2: Claude Code Configuration & Workflows** | **~20%** | Q96 – Q155 | **60** | Configuration hierarchy (`Managed` → `~/.claude/` → `.claude/` → `CLI`), `CLAUDE.md` conciseness (<200 lines), path-scoped rules, skills with `context: fork`, plan mode, headless CI/CD (`-p`, `--bare`, `--output-format json`). |
| **Domain 3: Prompt Engineering & Context Management** | **~20%** | Q156 – Q215 | **60** | Prompt caching prefix rules (`cache_control`), TTL sliding resets, constrained decoding (`output_config.format` with `json_schema`), XML tag boundary enforcement, Case Facts layer, token economics. |
| **Domain 4: Tool Design & Model Context Protocol (MCP)** | **~18%** | Q216 – Q275 | **60** | JSON Schema validation, `tool_choice` constraints with thinking, actionable error feedback (`is_error: true`), MCP 2026-07-28 stateless request/response spec, header routing, cacheable lists (`ttlMs`), OAuth 2.1, progressive tool discovery. |
| **Domain 5: Governance, Safety, & Risk Management** | **~15%** | Q276 – Q305 | **30** | Autonomy Spectrum, Approval Fatigue (93% blind approval trap), DLP sanitization middleware, Least Privilege environment isolation, EU AI Act Article 14 audit logging, OpenTelemetry tracing. |
| **TOTAL** | **100%** | **Q1 – Q305** | **305** | Full enterprise coverage. |

---

## 📁 Question Sets Index

Each set is saved in a dedicated markdown file with complete answers, in-depth explanations for all options, and Anti-Pattern alerts:

1. [Set 1: Domain 1 — Core Agentic Loop & Stop Reasons (Q1 – Q30)](set_01_domain1_core_agentic_loop.md)
   * `stop_reason` transitions (`tool_use`, `end_turn`, `max_tokens`, `stop_sequence`)
   * Appending full assistant messages before tool results
   * Extended thinking budget constraints and temperature restrictions
   * Parallel tool executions and client validation gates

2. [Set 2: Domain 1 — Multi-Agent Topologies & Orchestration Patterns (Q31 – Q65)](set_02_domain1_multi_agent_topologies.md)
   * Hub-and-Spoke coordinator standards vs Peer-to-Peer mesh chaos
   * Subagent context isolation and explicit context construction
   * Context Starvation vs Overly Narrow Decomposition
   * Parallel fan-out concurrency with rate limiters and semaphores
   * Producer-Critic / Verifier subagent patterns

3. [Set 3: Domain 1 — Extended Thinking, State Management & Resilient Loops (Q66 – Q95)](set_03_domain1_extended_thinking_state.md)
   * Cryptographic signatures in thinking blocks and multi-turn continuity
   * Context degradation ("Lost in the Middle") mitigation
   * Handling HTTP 429 / 529 errors with exponential backoff and jitter
   * Durable checkpointing and state externalization
   * Indirect prompt injection via tool results

4. [Set 4: Domain 2 — Configuration Hierarchy & CLAUDE.md Scoping (Q96 – Q125)](set_04_domain2_claude_code_config.md)
   * 4-tier configuration precedence hierarchy
   * Enterprise managed immutable security floors
   * Keeping `CLAUDE.md` under 200 lines to prevent prompt saturation
   * Modular path-scoped rules in `.claude/rules/`
   * Toolchain pinning, TDD enforcement, and secret protection

5. [Set 5: Domain 2 — Skills, Subagents, Plan Mode & Headless CI/CD (Q126 – Q155)](set_05_domain2_skills_subagents_headless.md)
   * Modular Skills discovery and YAML frontmatter (`paths`, `effort`)
   * Isolated execution with `context: fork`
   * Plan Mode (`Shift+Tab`, `/plan`, `useAutoModeDuringPlan`)
   * Headless automation (`-p`, `--bare`, `--output-format json`, `--json-schema`)
   * Session resumption (`--resume <session_id>`) and pre-commit hooks

6. [Set 6: Domain 3 — Prompt Caching & Token Economics (Q156 – Q185)](set_06_domain3_prompt_caching_economics.md)
   * Strict prefix rule (Tools → System → Messages)
   * Dynamic prefix invalidation (the timestamp anti-pattern)
   * Sliding TTL resets and 4-breakpoint limits
   * Token usage breakdown (`cache_creation_input_tokens`, `cache_read_input_tokens`)
   * Batch Processing API (50% discount) and high-throughput routing

7. [Set 7: Domain 3 — Structured Outputs & Context Preservation (Q186 – Q215)](set_07_domain3_structured_outputs_prompting.md)
   * Constrained decoding via native grammar constraints (`output_config.format`)
   * Structural XML tag boundary enforcement
   * Case Facts Layer for invariant entity persistence
   * PostToolUse normalization hooks to strip raw data dumps
   * Golden Dataset evaluation harnesses and LLM-as-a-Judge

8. [Set 8: Domain 4 — Tool Schemas, tool_choice & Error Handling (Q216 – Q245)](set_08_domain4_tool_schemas_error_handling.md)
   * High-accuracy tool and parameter descriptions in JSON Schema
   * `tool_choice` mechanics (`auto`, `any`, `tool`) and thinking incompatibilities
   * Diagnostic error recovery with `is_error: true`
   * Idempotent tool design and idempotency keys
   * Granular vs consolidated tools and SQL argument injection defense

9. [Set 9: Domain 4 — MCP Architecture & 2026 Specification (Q246 – Q275)](set_09_domain4_mcp_architecture_stateless.md)
   * Core primitives: Tools (`tools/*`), Resources (`resources/*`), Prompts (`prompts/*`)
   * The July 28, 2026 Stateless Request/Response specification
   * Header-based routing (`Mcp-Method`, `Mcp-Name`) and cacheable lists (`ttlMs`)
   * Templated resources, subscriptions (`listChanged`), and OAuth 2.1 hardening
   * Progressive tool discovery to eliminate Tool Bloat

10. [Set 10: Domain 5 — Governance, Safety, Risk Management & Anti-Patterns (Q276 – Q305)](set_10_domain5_governance_safety_risk.md)
    * The Autonomy Spectrum: Plan → Approval Gates → Auto-Execution
    * The Approval Fatigue Trap (93% blind approval rate) and Intent-Based Scoping
    * DLP sanitization middleware and air-gapped environment isolation
    * EU AI Act Article 14 audit logging and OpenTelemetry tracing
    * The "Context Trap", "Prompt-as-a-Firewall", and "God-Mode Connection" anti-patterns

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
8. **Monolithic CLAUDE.md**: Stuffing 2,000+ lines of general company wikis into root `CLAUDE.md`, saturating the prompt and diluting model focus.
9. **Dynamic Prefix Invalidation**: Placing timestamps, request IDs, or variable counters at the top of prompts, permanently breaking prompt caching.
10. **Cache Thrashing**: Alternating rapidly between unrelated massive corpuses before amortizing cache write premiums.
11. **Probabilistic Formatting Reliance**: Begging the model in natural language to "please return valid JSON" instead of using constrained decoding.
12. **Raw Tool Ingestion Bloat**: Appending unparsed megabyte JSON dumps directly into conversation history without normalization.
13. **Tool Proliferation (Bloat)**: Exposing 50+ competing tools simultaneously, causing model hesitation, latency spikes, and incorrect selections.
14. **Silent Tool Fallback**: Catching exceptions and returning dummy mock data with `is_error: false`, blinding the agent to operational failures.
15. **Prompt-As-Permission**: Relying on prompt promises for authorization instead of enforcing role-based access control (RBAC) at the tool layer.
16. **Approval Fatigue Trap**: Forcing human operators to approve every minor file read or grep query, leading to ~93% blind approval rates.
17. **The Context Trap**: Leaving agents without factual grounding, causing them to hallucinate fake endpoints, credentials, or mock state.
18. **Opaque Audit Trails**: Discarding intermediate tool arguments and system calls, leaving the enterprise unable to explain or defend AI actions.

