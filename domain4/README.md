# Domain 4: Prompt Engineering & Structured Output (20% of Exam)

Domain 4 represents 20% of the **Claude Certified Architect – Foundations (CCAR-F)** exam. It focuses on designing prompts with explicit categorical criteria, few-shot prompting for structural generalization, guaranteed valid structured output via `tool_use`, validation-retry feedback loops, high-throughput asynchronous Message Batches API pipelines, and multi-pass review architectures.

> 📖 **Deep Dive Master Guide**: For exhaustive technical explanations, architecture diagrams, sequence flows, gotchas, to-remember points, and practical scenario questions & answers, see [KEY_CONCEPTS.md](KEY_CONCEPTS.md).

---

## 📋 Task Statements & Core Architectural Principles

### [TS 4.1: Design Prompts with Explicit Criteria to Improve Precision and Reduce False Positives](ts_4_1_explicit_criteria_classification/main.py)
- **Categorical Criteria vs Vague Guidance**: Explicit criteria with code examples drastically outperform subjective directives like "be conservative and careful".
- **Negative Boundaries**: Explicitly state what NOT to report (e.g. ignore missing types in test helper functions) to prevent over-eager classification.
- **Managing False Positives**: Temporarily disable noisy categories entirely while refining criteria, rather than filtering by unreliable model confidence scores.
- **Concrete Severity Tiers**: Define Critical, High, Medium, Low with unambiguous technical criteria.
- **Reference Exercise**: [ts_4_1_explicit_criteria_classification/](ts_4_1_explicit_criteria_classification/)

### [TS 4.2: Apply Few-Shot Prompting to Improve Output Consistency and Quality](ts_4_2_few_shot_and_multi_instance/main.py)
- **Targeted Examples**: 2–4 high-impact few-shot examples illustrating complex reasoning, boundary edge cases, and expected output formatting.
- **Generalization**: Teach underlying principles and reasoning rather than string matching.
- **Structural Diversity**: Include diverse layout examples (tables, key-value blocks, unstructured text) to eliminate null extraction errors on varied enterprise documents.
- **Reference Exercise**: [ts_4_2_few_shot_and_multi_instance/](ts_4_2_few_shot_and_multi_instance/)

### [TS 4.3: Enforce Structured Output Using Tool Use and JSON Schemas](ts_4_3_structured_output_tool_use/main.py)
- **Guaranteed Valid Syntax**: Enforcing schemas via `tool_use` with forced `tool_choice` guarantees 100% syntactically valid JSON, eliminating markdown parsing errors.
- **Preventing Hallucinations via Nullable Fields**: Mark missing-prone fields as `type: ["string", "null"]` so Claude outputs `null` instead of fabricating data.
- **Extensible Taxonomy**: Use enum categories with `"OTHER"` plus a companion string field `other_description`.
- **Reference Exercise**: [ts_4_3_structured_output_tool_use/](ts_4_3_structured_output_tool_use/)

### [TS 4.4: Implement Validation, Retry, and Feedback Loops for Extraction Quality](ts_4_4_validation_retry_feedback/main.py)
- **Targeted Error Feedback**: Feed specific Pydantic / JSON schema validator errors (field, observed value, expected format) back to Claude for self-correction.
- **Recoverable vs Unrecoverable Errors**: Retries fix formatting and math errors; retries fail when data is fundamentally absent from source documents. Stop retries and escalate unrecoverable errors to human queues.
- **Semantic Cross-Checking**: Compare independent fields (e.g. `sum(line_items)` vs `stated_total`) to catch calculation mismatches.
- **Reference Exercise**: [ts_4_4_validation_retry_feedback/](ts_4_4_validation_retry_feedback/)

### [TS 4.5: Design Efficient Batch Processing Strategies](ts_4_5_message_batches_api/main.py)
- **Message Batches API**: 50% discount on API costs with up to 24-hour turnaround window (no latency SLA).
- **Workload Qualification**: Ideal for non-blocking overnight audits, large-scale extraction, and test generation; never use for blocking pre-merge CI checks.
- **Correlation & Partial Recovery**: Assign deterministic `custom_id`s to correlate results and resubmit only failed requests.
- **Reference Exercise**: [ts_4_5_message_batches_api/](ts_4_5_message_batches_api/)

### [TS 4.6: Design Multi-Instance and Multi-Pass Review Architectures](ts_4_6_multi_pass_review/main.py)
- **Mitigating Self-Review Bias**: Independent Claude review instances (with clean context) catch subtle defects that the authoring instance overlooks.
- **Multi-Pass Review Pipeline**: Split large PR reviews into Pass 1 (isolated per-file checks) + Pass 2 (cross-file integration pass) to prevent attention dilution.
- **Reference Exercise**: [ts_4_6_multi_pass_review/](ts_4_6_multi_pass_review/)

---

## 🛠️ Hands-on Exercises in this Domain
- `ts_4_1_explicit_criteria_classification/`: Precision classification with explicit negative boundaries and severity tiers.
- `ts_4_2_few_shot_and_multi_instance/`: Diverse few-shot prompting across varied invoice structures.
- `ts_4_3_structured_output_tool_use/`: Guaranteed schema extraction via `tool_use` with nullable fields.
- `ts_4_4_validation_retry_feedback/`: Programmatic validation-retry loops and unrecoverable missing data handling.
- `ts_4_5_message_batches_api/`: Batch submission, `custom_id` correlation, and partial failure resubmission.
- `ts_4_6_multi_pass_review/`: Two-pass code review architecture (local per-file pass + cross-file integration pass).
