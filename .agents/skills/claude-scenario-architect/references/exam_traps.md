# The 5 Critical Exam Traps & Anti-Patterns

When reviewing architectural alternatives on the CCAR-F exam or in technical interviews, look out for these 5 common anti-pattern traps:

### 1. The Batch API CI Trap
- **The Trap**: Proposing Anthropic's Message Batches API for pre-merge pull request gating to save 50% on cost.
- **Why It Fails**: The Message Batches API has a turnaround window of up to 24 hours and no real-time latency SLA. Using it for blocking PR checks will freeze the CI/CD pipeline and stall developer velocity.
- **The Architect Solution**: Use standard synchronous requests (with `-p` and `--output-format json`) for blocking PR gates. Reserve the Message Batches API exclusively for non-blocking, latency-tolerant workloads (e.g., overnight repository audits, weekly doc generation).

### 2. The 0-Result Search Trap
- **The Trap**: Flagging an MCP search tool execution that finds 0 records as an error (`isError: true` or raising an exception).
- **Why It Fails**: A search returning 0 hits is a successful query with an empty result set. Returning `isError: true` confuses the agentic coordinator, triggering wasteful retries and potential error cascades.
- **The Architect Solution**: Return `isError: false` with an empty collection: `{"isError": false, "records": [], "count": 0}`.

### 3. The Prompt Compliance Trap
- **The Trap**: Relying solely on system prompt rules to enforce critical security, identity verification, or monetary spending caps.
- **Why It Fails**: Prompt instructions are probabilistic. Under high ambiguity, long conversations, or adversarial inputs, prompts have a non-zero failure rate.
- **The Architect Solution**: Enforce mandatory policies using deterministic programmatic prerequisite gates in the orchestrator or Agent SDK hooks (`PostToolUse`).

### 4. The Context Inheritance Trap
- **The Trap**: Assuming spawned subagents automatically inherit the coordinator's conversation history or case facts.
- **Why It Fails**: Subagents run in completely isolated context windows with empty message histories. They cannot see parent turns.
- **The Architect Solution**: Explicitly package and pass all relevant findings, document IDs, and constraints as tool input parameters when spawning subagents.

### 5. The High Aggregate Accuracy Trap
- **The Trap**: Assuming a 98% overall extraction accuracy score means manual verification can be skipped.
- **Why It Fails**: Aggregate accuracy can conceal severe failures in low-frequency segments (e.g., 99% accuracy on common invoices, but 40% failure on rare handwritten receipts).
- **The Architect Solution**: Implement stratified random sampling (auditing 5–10% of high-confidence predictions across all document segments) to detect silent model drift and category-specific failures.
