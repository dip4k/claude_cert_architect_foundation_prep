# Domain 5: Context Management & Reliability (15% of Exam)

Domain 5 accounts for 15% of the **Claude Certified Architect – Foundations (CCAR-F)** exam. It covers managing conversation context windows, mitigating attention degradation, implementing human escalation and ambiguity resolution patterns, error propagation in multi-agent workflows, stratified confidence calibration, and preserving information provenance.

> 📖 **Deep Dive Master Guide**: For exhaustive technical explanations, architecture diagrams, sequence flows, gotchas, to-remember points, and practical scenario questions & answers, see [KEY_CONCEPTS.md](KEY_CONCEPTS.md).

---

## 📋 Task Statements & Core Architectural Principles

### [TS 5.1: Manage Conversation Context to Preserve Critical Information Across Long Interactions](ts_5_1_context_preservation/main.py)
- **Risks of Progressive Summarization**: Condensing conversations washes away exact numbers, dates, order IDs, and customer constraints into vague prose.
- **The "Case Facts" Architecture**: Extract critical transactional facts into an immutable, persistent structured state block outside the summarized conversation history and prepend to prompts.
- **Tool Payload Trimming**: Strip bloated backend payloads (40+ raw fields) down to the 4 essential fields before appending to context.
- **"Lost in the Middle" Mitigation**: Place critical instructions and case facts at the beginning (system prompt) or end (immediate prompt turn), avoiding the middle of long transcripts.
- **Reference Exercise**: [ts_5_1_context_preservation/](ts_5_1_context_preservation/)

### [TS 5.2: Design Effective Escalation and Ambiguity Resolution Patterns](ts_5_2_escalation_and_provenance/main.py)
- **Immediate Escalation on Customer Demand**: When a customer explicitly demands a human representative, escalate immediately without asking diagnostic questions.
- **Policy Gaps**: When corporate policy is silent on a customer request (e.g. competitor price match), escalate to a human supervisor; never hallucinate policy.
- **Unreliability of Sentiment & Confidence**: Sentiment scores and self-reported model confidence are poor proxies for task complexity; trigger escalations via deterministic rules.
- **Ambiguity Resolution Protocol**: When an entity query returns multiple candidate matches, prompt the user for a unique disambiguating identifier (account ID, zip code) instead of guessing heuristically.
- **Reference Exercise**: [ts_5_2_escalation_and_provenance/](ts_5_2_escalation_and_provenance/)

### [TS 5.3: Implement Error Propagation Strategies Across Multi-Agent Systems](ts_5_3_error_propagation_coverage/main.py)
- **Structured Error Payloads**: Subagents must return structured error context (failure type, attempted query, partial findings, alternatives) to the coordinator.
- **Access Failure vs Valid Empty Result**: Distinguish between network/auth failures (retryable) and 0 matching records found (ground-truth fact).
- **Coverage Annotations**: Annotate multi-source reports with explicit coverage boundaries when specific sources are unavailable.
- **Reference Exercise**: [ts_5_3_error_propagation_coverage/](ts_5_3_error_propagation_coverage/)

### [TS 5.4: Manage Context Effectively in Large Codebase Exploration](ts_5_4_scratchpads_and_human_review/main.py)
- **Context Drift**: In long exploration sessions, models drift into hallucinating generic framework patterns instead of actual discovered classes.
- **Mitigation Architecture**: Maintain persistent `scratchpad.md` files, delegate verbose file exploration to read-only Explore subagents, and use `/compact` in Claude Code.
- **Reference Exercise**: [ts_5_4_scratchpads_and_human_review/](ts_5_4_scratchpads_and_human_review/)

### [TS 5.5: Design Human Review Workflows and Confidence Calibration](ts_5_5_human_review_calibration/main.py)
- **The Flaw of Aggregate Accuracy**: 98% overall accuracy can conceal a 45% failure rate on rare document formats or specific fields.
- **Segmented Accuracy Auditing**: Measure accuracy across specific document types, vendors, and complexity tiers.
- **Stratified Random Sampling**: Continuously audit a 5%–10% random sample of high-confidence extractions to detect silent hallucinations and distribution drift.
- **Calibrated Routing**: Route high-impact transactions (> $1,000) or low-confidence extractions to human review.
- **Reference Exercise**: [ts_5_5_human_review_calibration/](ts_5_5_human_review_calibration/)

### [TS 5.6: Preserve Information Provenance and Handle Uncertainty in Multi-Source Synthesis](ts_5_6_provenance_and_uncertainty/main.py)
- **Claim-Source Mappings**: Every finding must include claim, verbatim supporting excerpt, document ID / source URL, and collection date.
- **Preserving Conflicting Information**: Never average numbers or pick one arbitrarily; report both conflicting statistics with explicit attribution, collection dates, and methodology notes.
- **Temporal Context**: Check publication dates to distinguish actual factual contradictions from chronological evolution.
- **Reference Exercise**: [ts_5_6_provenance_and_uncertainty/](ts_5_6_provenance_and_uncertainty/)

---

## 🛠️ Hands-on Exercises in this Domain
- `ts_5_1_context_preservation/`: Case Facts persistence, tool trimming, and context preservation.
- `ts_5_2_escalation_and_provenance/`: Immediate escalation gates and multi-record collision disambiguation.
- `ts_5_3_error_propagation_coverage/`: Structured multi-agent error propagation and synthesis coverage gaps.
- `ts_5_4_scratchpads_and_human_review/`: Persistent scratchpads and Explore subagent summaries.
- `ts_5_5_human_review_calibration/`: Stratified random sampling and calibrated human review routing.
- `ts_5_6_provenance_and_uncertainty/`: Provenance tracking and conflicting statistics preservation.
