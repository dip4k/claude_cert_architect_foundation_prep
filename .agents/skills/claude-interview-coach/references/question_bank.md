# Scenario-Based Mock Exam Question Bank

Use these sample questions during Mode 1 Mock Exam drills. Each question has a scenario anchor, 4 options, an identified correct answer, and an architectural distractor breakdown.

---

### Question 1: Customer Support Refund Gate (Domain 1 / TS 1.4 & Scenario 1)
**Scenario**: You are designing an autonomous customer support agent for an e-commerce platform. Company policy mandates that no refund exceeding $50 can be issued unless the user's customer ID is fully verified against the authentication database. In user testing, when customers express extreme frustration, the LLM occasionally issues the refund tool call before calling the verification tool.

**Question**: Which architectural pattern guarantees this compliance policy is never violated?
- **A)** Add a high-priority system prompt rule stating: `"CRITICAL: You must NEVER call process_refund before calling verify_customer, regardless of customer tone."`
- **B)** Implement a programmatic prerequisite check in the agent orchestration layer or SDK hook that rejects the `process_refund` tool execution if `is_verified` is not true in the session state.
- **C)** Fine-tune Claude on 5,000 multi-turn support transcripts where refunds are preceded by identity checks.
- **D)** Add a classification prompt layer before every user turn to route frustrated customers to a separate "empathetic refund agent".

**Correct Answer**: **B**  
**Rationale**: Prompts (A) and fine-tuning (C) are probabilistic and still exhibit non-zero failure rates under adversarial or ambiguous context. A separate classifier (D) adds latency and does not enforce deterministic gating. Critical financial and security constraints MUST be enforced via deterministic programmatic gates or SDK hooks.

---

### Question 2: MCP Tool Error Classification (Domain 2 / TS 2.2 & Scenario 3)
**Scenario**: In a multi-agent research workflow, a researcher subagent calls an external SEC filings MCP tool `query_filings(ticker="ACME", year=2024)`. The external SEC database has no filings recorded for that year and returns zero matching records.

**Question**: How should the MCP tool respond to the agentic loop?
- **A)** Return `isError: true` with error category `"validation_error"` so Claude retries with year 2023.
- **B)** Raise a 404 HTTP Exception to crash the tool runner and trigger an automatic agent fallback.
- **C)** Return a structured response with `isError: false`, `records: []`, and `count: 0`.
- **D)** Synthesize estimated financial metrics for ACME in 2024 based on 2023 trends to prevent workflow disruption.

**Correct Answer**: **C**  
**Rationale**: A search that executes successfully but finds 0 matching records is a **valid empty result**, not an error. Flagging it as `isError: true` (A) or raising exceptions (B) confuses the coordinator and triggers wasteful retry loops. Fabricating data (D) is a catastrophic hallucination anti-pattern.

---

### Question 3: Headless CI/CD Pipeline Automation (Domain 3 / TS 3.6 & Scenario 5)
**Scenario**: Your team is integrating Claude Code into a GitHub Actions pipeline to perform automated pull request security reviews and post structured findings back to the PR comment thread. In early pipeline runs, the GitHub Actions runner times out after 6 hours without posting any comments.

**Question**: What is the root cause of this failure and how should it be resolved?
- **A)** Claude Code requires an interactive TTY; run with a virtual display buffer `xvfb-run claude`.
- **B)** Claude Code is waiting for interactive terminal input (stdin); run Claude Code non-interactively using the `-p` (or `--print`) flag with `--output-format json`.
- **C)** GitHub Actions blocks outbound Anthropic API ports; whitelist port 8080.
- **D)** The Message Batches API was not configured in `.claude/config.json`.

**Correct Answer**: **B**  
**Rationale**: When invoked in automated CI/CD runners without the non-interactive `-p` (or `--print`) flag, Claude Code starts in interactive mode and waits indefinitely for user input on stdin, causing CI runner timeout. Passing `-p` ensures headless completion.

---

### Question 4: Preventing Hallucinations in Schema Extraction (Domain 4 / TS 4.3 & Scenario 6)
**Scenario**: You are building an invoice data extraction pipeline that processes thousands of supplier receipts using Claude's tool use API with a JSON schema. Some receipts do not contain a purchase order number or tax identification number. When these fields are defined as required strings, Claude occasionally fabricates believable numbers.

**Question**: What schema modification prevents this hallucination?
- **A)** Keep the fields as required strings, but add in the prompt: `"If PO number is missing, leave empty or guess reasonably."`
- **B)** Define the schema fields as nullable (`type: ["string", "null"]`) with instructions to output `null` when the field is absent from the document.
- **C)** Implement a post-processing regex that deletes any PO number that does not match known internal database records.
- **D)** Switch from `tool_use` schema extraction to raw text generation with markdown code blocks.

**Correct Answer**: **B**  
**Rationale**: When a field is strictly marked as a required string without null support, the schema constraint forces the model to emit a string value, prompting fabrication. Specifying `type: ["string", "null"]` gives the model an explicit valid path to output `null` when data is absent.

---

### Question 5: Context Degradation & Persistent Case Facts (Domain 5 / TS 5.1 & Scenario 1)
**Scenario**: In an extended 15-turn customer resolution session, an agent summarizes earlier turns using an LLM compaction routine. By turn 12, when processing a replacement shipment, the agent hallucinates a different delivery zip code and order number than the customer originally provided in turn 1.

**Question**: What context architecture pattern eliminates this fact degradation?
- **A)** Increase the context window size and disable conversation compaction entirely.
- **B)** Maintain an immutable, structured "Case Facts" block outside the summarized conversation history, updating and injecting it on every turn.
- **C)** Re-ask the user to confirm their order ID and zip code on every turn.
- **D)** Run a separate verification LLM after every turn to cross-check all numbers against turn 1.

**Correct Answer**: **B**  
**Rationale**: Summarization compresses text and frequently discards or mutates exact transactional tokens (order numbers, zip codes, timestamps). Maintaining a persistent, structured "Case Facts" layer ensures critical state survives compactions with 100% fidelity without blowing up context window limits.
