# The Critical Exam Traps & Anti-Patterns

When reviewing architectural alternatives on the CCAR-F exam or in technical interviews, look out for these 7 common anti-pattern traps:

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

### 6. The Temperature with Extended Thinking Trap
- **The Trap**: Passing `temperature: 0.0` or custom sampling parameters alongside Extended Thinking (`thinking={"type": "enabled", "budget_tokens": ...}`) in Claude 4.5.
- **Why It Fails**: The API rejects a custom `temperature` when thinking is enabled with an HTTP `400 Bad Request` error. Leave `top_p` and `top_k` unset too; newer models reject any non-default sampling value.
- **The Architect Solution**: Omit `temperature` entirely when thinking is enabled. Adjust reasoning depth exclusively via `budget_tokens`.

### 7. The Thinking Block Stripping Trap
- **The Trap**: Stripping assistant `thinking` blocks from conversation history before sending `tool_result` to "conserve context tokens".
- **Why It Fails**: The Anthropic API requires assistant thinking blocks (and their cryptographic signatures) to be echoed back verbatim in subsequent turns. Omitting or modifying them invalidates the conversation trail and raises an HTTP `400 Bad Request` error.
- **The Architect Solution**: Always append the full assistant response content (`model_dump()`) containing both `thinking` and `tool_use` blocks into history.

### 8. The Forced Tool Choice with Thinking Trap
- **The Trap**: Enabling Extended Thinking and also setting `tool_choice` to `any` or a named tool to guarantee structured output.
- **Why It Fails**: With thinking enabled, only `tool_choice` `auto` or `none` is accepted; the API returns HTTP `400` for the other values. This is the rule for manual extended thinking (the mode on Claude 4.5 models); adaptive thinking on newer models can accept forced tool use, except on some models.
- **The Architect Solution**: Run the forced-tool request without `thinking`. Use thinking only on `auto` turns, and return its `thinking` blocks unchanged in tool loops.
