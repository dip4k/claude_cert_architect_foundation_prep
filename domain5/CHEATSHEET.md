# Domain 5 Cheatsheet: Context Management & Reliability (15%)

One-page revision. **Not a copy of [KEY_CONCEPTS.md](KEY_CONCEPTS.md)**: that file already holds the golden rules, the distractor teardown and a decision matrix. This sheet adds question wording to answer, look-alike pairs, the numbers worth remembering, and elimination filters. Worked traps are in each study guide (links at the bottom).

---

## 1. Question wording → answer

| If the question says... | Choose | Reject | TS |
|---|---|---|---|
| Exact IDs, amounts or dates drift over many turns | Case facts block, re-sent every turn | "Summarise harder", "keep numbers" | 5.1 |
| Tool returns dozens of fields | Trim to needed fields before it enters context | Append everything, trim later | 5.1 |
| Key finding gets ignored in a long input | Key findings first, headers, question last | Leave it in the middle | 5.1 |
| Subagents return long reasoning | Structured facts: claim, source, date | Full reasoning chains | 5.1, 5.4 |
| Customer says "get me a human" | Escalate now | Investigate first, ask why | 5.2 |
| Angry customer, simple fix | Acknowledge, fix, escalate if they repeat | Escalate on sentiment | 5.2 |
| Search returns several matching customers | Ask for another identifier | Pick the most recent | 5.2 |
| Policy does not cover the request | Escalate as a policy gap | Invent a rule | 5.2 |
| Too many wrong escalations | Explicit criteria plus few-shot examples | Confidence score, sentiment model, classifier | 5.2 |
| Subagent timed out | Structured error: type, query, partial results, alternatives | "Search unavailable" | 5.3 |
| Source searched, nothing found | Valid empty result | Error | 5.3 |
| Source could not be searched | Failure | Empty list as success | 5.3 |
| One of five sources fails | Continue and annotate coverage | Abort the run | 5.3 |
| Specifics fade late in a long session | `scratchpad.md` of findings | "Remember this" | 5.4 |
| Run was interrupted | Manifest plus state files, resume pending work | Start over | 5.4 |
| "97% accurate overall" | Accuracy by document type and field | Approve on the aggregate | 5.5 |
| How to sample for review | Stratified random, including high-confidence items | Only low-confidence items | 5.5 |
| Two credible sources disagree | Show both with source and date | Average or pick one | 5.6 |
| Values from different years | Timeline with dates | Flag a contradiction | 5.6 |

---

## 2. Look-alike pairs

| Pair | Difference |
|---|---|
| Case facts vs summary | Structured, never paraphrased / compressed prose that loses exact values |
| Scratchpad vs `/compact` | File of exact findings that survives compaction / summary of history |
| Explore subagent vs main-chat reading | Reads in its own context, returns a summary / fills the main context |
| `UPSTREAM_FAILURE` vs `VALID_EMPTY` | Could not check (a gap) / checked, found nothing (evidence) |
| Local recovery vs propagation | Retry transient errors inside the subagent / pass up only what stays unresolved |
| Escalation trigger vs proxy | Explicit request, policy gap, no progress / sentiment, self-reported confidence |
| Contested vs timeline | Same metric and period, different values / same metric, different periods |
| Stratified vs flat sample | Per (type, field) so rare segments appear / rare segments barely sampled |
| Calibrated vs raw confidence | Checked against labelled data in bins / the model's own number |
| Established vs contested claims | Agreement or single reliable source / sources disagree, show both |

---

## 3. Numbers and names worth remembering

- Monitoring sample for automation: a stratified random sample of roughly 5 to 10%, including items the model was confident about (as used in [KEY_CONCEPTS.md](KEY_CONCEPTS.md)).
- Tool payload: keep the few fields the next step needs (for example 4 of 47).
- Example check on aggregates: 90% of volume at 99.5%, 6% at 81%, 4% at 78% still reports about 97.6% overall.
- Placement: critical rules and facts at the start, the question or latest turns at the end.
- Escalation fields for a handoff: customer, verified status, issue, what was tried, why it escalated, recommended action.
- Coverage line in a report: sources answered, sources not checked and why.
- Thinking in a long loop: echo `thinking` blocks with signatures unchanged, no `temperature`, `budget_tokens` at least 1024 and below `max_tokens`.

---

## 4. Elimination filters (reject on sight)

1. Any option that asks the model to "remember" or "be careful" instead of storing facts outside the history.
2. Any option that escalates or does not escalate based on sentiment or self-reported confidence.
3. Any option that guesses (which customer, what the policy says, which number is right).
4. Any option that turns a failure into an empty success, or a valid zero into an error.
5. Any option that approves automation on a single aggregate accuracy figure.
6. Any option that averages or silently chooses between conflicting sources.

---

## Where the detail is

[5.1](ts_5_1_context_preservation/README.md) · [5.2](ts_5_2_escalation_and_provenance/README.md) · [5.3](ts_5_3_error_propagation_coverage/README.md) · [5.4](ts_5_4_scratchpads_and_human_review/README.md) · [5.5](ts_5_5_human_review_calibration/README.md) · [5.6](ts_5_6_provenance_and_uncertainty/README.md)
