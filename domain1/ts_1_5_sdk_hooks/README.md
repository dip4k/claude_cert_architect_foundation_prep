# Task Statement 1.5: Apply Agent SDK Hooks for Tool Call Interception and Data Normalization

> Domain 1 (27% of the exam) · Scenarios 1 (Customer Support) and 4 (Developer Productivity) · [Back to Domain 1](../README.md)

## In One Minute

- **What**: hooks are code that runs around tool calls, outside the model.
- **Two kinds**: a **pre-tool interception hook** (`PreToolUse`) can block a call. A **`PostToolUse` hook** cleans the result before Claude reads it.
- **Examples**: block a refund over $500 and redirect to a human. Turn Unix timestamps into ISO 8601. Turn numeric status codes into names.
- **Hooks are deterministic. Prompts are probabilistic.**
- **Exam answer in one line**: policy that must always hold goes in a hook, and format cleanup goes in `PostToolUse`.

---

## 📌 Overview

### Why it matters
Business tools are messy. One returns `1728216000`, another returns `"2024-10-06"`. Status may be `404` in one system and `"not_found"` in another. If Claude sees all of that raw, it can misread dates or states. Separately, "never refund more than $500" written in a prompt can be talked around. A hook cannot be talked around, because it is plain code.

### What the exam tests
- **`PostToolUse`** normalises tool results (timestamps, status codes) **before** the model sees them.
- **Interception** hooks enforce policy before a tool runs (for example refund over $500: block and escalate).
- Hooks are **deterministic**. Prompts are **probabilistic**.
- Picking the right place: block **before** execution, clean **after** execution.

---

## 📖 Concepts Explained

### 1. The simple idea
Think of airport security. The **pre-tool hook** is the checkpoint before boarding (stop a bad action early). The **`PostToolUse` hook** is the baggage handler who repacks what comes out so it all looks the same.

### 2. Pre-tool interception: block before it runs
`compliance_interception_hook` in [main.py](main.py) looks at the tool name and input. For `process_payout`, if `amount > 500.00` (`MAX_AUTONOMOUS_THRESHOLD`), it returns a block result:

```json
{"blocked_by_hook": true, "reason": "... exceeds $500.00 limit ...", "redirect_action": "escalate_to_supervisor"}
```

The tool never runs. The loop sends this back as an `is_error` `tool_result`, so Claude can explain the limit and route the case to a human. A refund that has already gone out cannot be taken back by a later check, so the block must come first. (The exam describes this as a refund over $500. The code's tool is named `process_payout`.)

### 3. `PostToolUse`: clean the result
`post_tool_use_normalization_hook` runs on the raw tool output before it is appended as a `tool_result`:

| Raw field | Becomes |
|---|---|
| `epoch_timestamp: 1728216000` | `iso_timestamp: "2024-10-06T12:00:00+00:00"` (ISO 8601, UTC) |
| `raw_status_code: 200` | `status: "active"` (also 201 `created`, 400 `client_error`, 404 `not_found`, 500 `server_error`, else `unknown`) |
| fields starting with `_` | removed, so internal fields never reach the context window |

`execute_with_hooks` runs the whole chain: pre-tool hook, the tool, then `PostToolUse`.

### 4. Why not just tell Claude in the prompt?
- "Please convert timestamps" costs tokens every time, and Claude may still get it wrong.
- "Never refund over $500" is followed most of the time, not every time.
- A hook does it the same way on every call.

---

## 🧪 Worked Example

**Part A: normalisation.** User: *"Check the status of account ACC-100."*

| Step | What happens |
|---|---|
| 1 | Claude: `stop_reason = "tool_use"`, `check_account_status("ACC-100")` |
| 2 | Tool returns raw `{"epoch_timestamp": 1728216000, "raw_status_code": 200, "balance": 1250.0}` |
| 3 | `PostToolUse` changes it to `{"iso_timestamp": "2024-10-06T12:00:00+00:00", "status": "active", "balance": 1250.0}` |
| 4 | Claude sees only the clean form and answers: "The account is active." (`end_turn`) |

**Part B: interception.** User: *"Issue a payout of $850 to ACC-100."*

| Step | What happens |
|---|---|
| 1 | Claude: `tool_use`, `process_payout(ACC-100, 850.0)` |
| 2 | Pre-tool hook: 850 > 500, so **block**. `process_payout` is never called |
| 3 | `tool_result` with `is_error: true` and `redirect_action: "escalate_to_supervisor"` |
| 4 | Claude: `end_turn`, "That is over the $500 limit. I am routing it to a supervisor." |

---

## 🔑 Key Terms

- **Hook**: code that runs at a defined point in the tool lifecycle, outside the model.
- **Pre-tool interception (`PreToolUse`)**: runs before the tool. Can block or redirect.
- **`PostToolUse`**: runs after the tool, before Claude reads the result. Normalises or trims.
- **Normalisation**: one consistent format for dates, codes, and enums.
- **Deterministic vs probabilistic**: hooks always apply. Prompts usually apply.

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart LR
    Model["Claude tool_use<br>(claude-sonnet-4-5)"] --> Pre["Pre-tool hook<br>(policy check)"]
    Pre --> Allowed{"Allowed?<br>e.g. amount at most 500"}

    Allowed -->|"No"| Block["Block the call<br>return is_error tool_result<br>redirect to human"]
    Allowed -->|"Yes"| Tool["Run the tool"]

    Tool --> Post["PostToolUse hook<br>normalise and trim"]
    Post --> Clean["Clean tool_result<br>appended to messages"]
    Block --> Back["tool_result back to Claude"]
    Clean --> Back
```

---

## ⚠️ Exam Traps and Correct Patterns

| Topic | Correct pattern | Trap | Why the trap fails |
|---|---|---|---|
| **Policy limit** | Pre-tool hook blocks and redirects | A prompt rule only | Probabilistic. Can be talked around |
| **Policy limit** | Block before running | Let it run, then undo | Money and deletions cannot be reliably undone |
| **Mixed formats** | `PostToolUse` normalises | Ask Claude to convert each time | Costs tokens. Can still go wrong |
| **Noisy results** | Trim fields in a hook | Tell Claude to "ignore" fields | They still use the context window |
| **Blocked call** | Return a clear error and a redirect | Silently drop the call | Claude gets no signal and may retry or hallucinate |

---

## ❌ Common Mistakes

- Putting a hard business rule only in the system prompt.
- Using `PostToolUse` to enforce a limit. It runs after the action happened.
- Using the pre-tool hook to reformat data. Cleanup belongs after execution.
- Returning a block with no reason, so Claude cannot explain it to the user.
- Normalising only some tools, so formats stay mixed.

---

## 💡 Quick Decision Rules

| Need | Use |
|---|---|
| Stop an action that breaks policy | Pre-tool interception hook |
| Make dates and codes consistent | `PostToolUse` |
| Remove fields Claude does not need | `PostToolUse` |
| Route over-limit cases to a person | Hook returns a redirect |
| Style or tone | Prompt |

---

## 🧠 Claude 4.5 Notes

- Models: `claude-sonnet-4-5` for the agent loop (`COORDINATOR_MODEL` in [main.py](main.py)), `claude-haiku-4-5` for workers.
- Extended thinking: `thinking={"type": "enabled", "budget_tokens": N}` with `N >= 1024` and `N < max_tokens`.
- With thinking on: no `temperature` (HTTP 400), no `top_k`, `top_p` only 0.95 to 1.0, and `tool_choice` only `auto` or `none`.
- Hooks change tool results, never earlier assistant content. Echo assistant `thinking` blocks and `signature` back unchanged.

---

## 📝 Exam-Style Practice Questions

**Q1.** Different backend tools return dates as Unix timestamps, ISO strings, and local formats, and status as numbers (200, 404). Claude sometimes misreads them. What is the best fix?

- A) Add a system prompt paragraph explaining all the formats.
- B) Add a `PostToolUse` hook that normalises timestamps to ISO 8601 and numeric codes to named statuses before Claude sees the result.
- C) Switch to a larger model.
- D) Add few-shot examples of every format.

**Q2.** Company policy: refunds above $500 must never run automatically and must go to a human. Which implementation is best?

- A) A pre-tool interception hook that blocks `process_refund` when `amount > 500` and redirects to escalation.
- B) A system prompt rule that says "never refund more than $500".
- C) A `PostToolUse` hook that flags refunds over $500 after they run.
- D) Setting `temperature` to 0.

**Q3.** An order-lookup tool returns 50 fields, including internal shard IDs and debug headers. Only five fields matter. Context fills up fast. What is the best fix?

- A) Tell Claude in the system prompt to ignore the extra fields.
- B) Base64-encode the payload to make it smaller.
- C) Wait for the context window to fill and summarise it.
- D) A `PostToolUse` hook that trims the result to the needed fields before it is appended.

### Answers

**Q1: B.**
- A) The model must re-interpret each time and can still be wrong.
- C) A larger model is still guessing at inconsistent data.
- D) Examples raise the odds but cannot cover every format, and they cost tokens on every call.

**Q2: A.**
- B) A prompt rule is probabilistic and may be bypassed.
- C) After the refund has run it is too late to stop it.
- D) Temperature does not enforce policy (and it is rejected when extended thinking is on).

**Q3: D.**
- A) The fields still sit in context and use tokens and attention.
- B) Base64 is longer in tokens and unreadable to the model.
- C) That reacts after the damage. Trimming first avoids the problem.

---

## ✅ Self-Check Checklist

- [ ] I can say what a pre-tool hook does and when it runs.
- [ ] I can say what `PostToolUse` does and what it must not be used for.
- [ ] I can give three normalisations: timestamps, status codes, trimming fields.
- [ ] I can explain why hooks are deterministic and prompts are not.
- [ ] I block before the action and clean after it.

**Memory hook**: *"Pre blocks, Post cleans."*

---

## 🛠️ Hands-on Workbook Guide

Open [ts_1_5_sdk_hooks.ipynb](ts_1_5_sdk_hooks.ipynb) (offline, mock client):

1. **Setup**: tools returning raw, legacy-format data.
2. **Interception**: block a payout above $500.
3. **Normalisation**: epoch to ISO 8601, status code to name, internal `_` fields removed.
4. **Hook chain**: pre-tool hook, the tool, then `PostToolUse`.
5. **Checks**: assertions on the blocked $800 payout and the cleaned account result.

Code: [main.py](main.py) (live API, run manually only) · Offline tests: [tests/test_domain1_enhancements.py](../../tests/test_domain1_enhancements.py)
