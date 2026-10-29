# Domain 4 Cheatsheet: Prompt Engineering & Structured Output (20%)

One-page revision. **Not a copy of [KEY_CONCEPTS.md](KEY_CONCEPTS.md)**: that file already holds the golden rules, the distractor teardown and a decision matrix. This sheet adds question wording to answer, look-alike pairs, exact batch and API values, and elimination filters. Worked traps are in each study guide (links at the bottom).

---

## 1. Question wording → answer

| If the question says... | Choose | Reject | TS |
|---|---|---|---|
| Too many false positives | Explicit report/skip criteria with negative boundaries | "Be conservative", confidence threshold | 4.1 |
| Severity differs between runs | One rule plus one code example per level | Level names only | 4.1 |
| One category is mostly dismissed | Disable it, rewrite criteria, re-enable | Keep it on while tuning | 4.1 |
| Ambiguous cases inconsistently labelled | 2 to 4 examples with reasons | More rules | 4.2 |
| Fails on a new document layout | Examples with varied layouts | More examples of the same layout | 4.2 |
| Model invents values for absent fields | Nullable fields plus an example returning `null` | Everything `required` | 4.2, 4.3 |
| JSON sometimes fails to parse | Tool with `input_schema` | "Return JSON" in the prompt | 4.3 |
| Totals do not add up although JSON is valid | Recompute in code, `conflict_detected` | "The schema guarantees it" | 4.3 |
| New or unknown category appears | Enum plus `other` + detail, and `unclear` | Closed enum | 4.3 |
| Unknown document type, several extraction tools | `tool_choice: any` | Forcing one tool | 4.3 |
| Format error after extraction | Retry with document, failed output, specific error | "Invalid, try again" | 4.4 |
| Value is simply not in the source | No retry. `null` or human review | Retry three times | 4.4 |
| Overnight job, nobody waiting | Message Batches API | Synchronous | 4.5 |
| Pre-merge check | Synchronous | Batch for the 50% | 4.5 |
| Some batch items failed | Resubmit those `custom_id`s only | Resubmit the whole batch | 4.5 |
| Review misses the author's own mistakes | Independent instance | Self-review, even with thinking | 4.6 |
| Cross-file bug missed | Second pass with signatures and call sites | Only per-file review | 4.6 |
| Low-confidence findings | Route to human review | Drop them | 4.6 |

---

## 2. Look-alike pairs

| Pair | Difference |
|---|---|
| Schema validation vs semantic validation | Shape (types, keys, enums) vs meaning (sums, dates, cross-field rules) in your code |
| Retry vs escalate | Info exists but output is wrong, so retry with feedback / info absent, so stop |
| Few-shot vs explicit criteria vs schema | Show the boundary / state the rule / guarantee the syntax |
| `any` vs forced tool vs `auto` | Some tool, type unknown / this tool first / may answer in text |
| Nullable vs optional | May be `null` in the output / may be left out. Both avoid forcing a value |
| Batch vs synchronous | No latency SLA, 50% cheaper / a person or merge is waiting |
| Same-session vs independent review | Shares the author's reasoning / fresh context |
| Confidence filter vs confidence routing | Drops findings / sends them to a person |

---

## 3. Exact values (checked against the Message Batches docs and tool-use docs)

- Batches: **50%** of standard prices on input and output. Most finish within 1 hour. Results available when all requests finish or after **24 hours**, whichever comes first. Unfinished requests **expire** after 24 hours.
- Limits: **100,000 requests or 256 MB** per batch (whichever first). Results kept **29 days** from creation. Oversized batch returns HTTP 413.
- `custom_id`: `^[a-zA-Z0-9_-]{1,64}$`, unique within the batch. Results can come back in **any order**, so always match on `custom_id`.
- Result types: `succeeded`, `errored`, `canceled`, `expired`. The last three are **not billed**. For `errored`, an `invalid_request_error` needs a fixed request body before resubmitting. Other errors can be retried directly.
- A submitted batch cannot be modified. Cancel and resubmit. Parameter validation runs asynchronously, so test one request shape with the Messages API first.
- Not supported in batch requests: `stream`, `speed`, `fallbacks`, `max_tokens: 0`. Tool use and extended thinking are supported, but each request is independent, so your own tool execution means a new request.
- Prompt caching in batches is best effort (cache hits roughly 30 to 98%). Use identical `cache_control` blocks and the 1-hour cache.
- Forced tool (`any` or named tool) with manual extended thinking is an error (HTTP 400). Forced tools prefill the assistant turn, so there is no text before `tool_use`.
- `strict: true` on a tool definition gives schema-valid inputs.
- Few-shot: 2 to 4 varied examples.

---

## 4. Elimination filters (reject on sight)

1. Any option that relies on wording ("be careful", "be conservative") instead of criteria or examples.
2. Any option that uses model confidence to filter or gate.
3. Any option that makes every schema field required.
4. Any option that retries on data missing from the source.
5. Any option that batches something a person or a merge is waiting on.
6. Any option where the generator also judges its own output.

---

## Where the detail is

[4.1](ts_4_1_explicit_criteria_classification/README.md) · [4.2](ts_4_2_few_shot_and_multi_instance/README.md) · [4.3](ts_4_3_structured_output_tool_use/README.md) · [4.4](ts_4_4_validation_retry_feedback/README.md) · [4.5](ts_4_5_message_batches_api/README.md) · [4.6](ts_4_6_multi_pass_review/README.md)
