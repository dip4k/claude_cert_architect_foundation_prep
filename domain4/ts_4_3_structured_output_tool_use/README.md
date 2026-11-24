# Task Statement 4.3: Structured Output with Tool Use and JSON Schemas

> Scenario: Scenario 6 (Structured Data Extraction).

## In One Minute
- **What**: Get structured data by defining a tool whose `input_schema` is your JSON schema.
- **Why**: Tool use removes JSON *syntax* errors. It does **not** remove *semantic* errors, such as line items that do not add up to the total.
- **How**: Make fields nullable when the source may lack them, add `"unclear"` and `"other"` + detail to enums, and validate the meaning in code.
- **Trade-off**: `tool_choice` `any` or a forced tool cannot be used together with extended thinking.
- **Exam answer in one line**: *Tool use + schema for syntax, nullable fields against fabrication, code validation for meaning.*

---

## 🧒 Explain Like I'm 13

**The picture:** A form with boxes, not an essay. A tool with an `input_schema` is the form: Claude must fill it in the right shape. Boxes that may not apply need an "N/A" (`null`) option, or Claude invents something to avoid leaving them blank. The form checks that the boxes exist, **not** that your sums add up.

**In plain steps:**
1. Define a tool with a JSON schema for the output.
2. Make uncertain fields nullable.
3. Add `other` and `unclear` to enums.
4. Recompute totals in your code and set `conflict_detected`.
5. Want a tool to be called? `tool_choice`. Want thinking? Then only `auto` or `none`.

**Tiny example:** Line items sum to 480 but the invoice says 840. The schema is happy. Your check is the one that notices.

---

## 📖 Concepts Explained

### 1. Why it matters
- Text JSON can have fences, trailing commas, or a chatty preamble.
- A required field that the document lacks pushes the model to make something up.
- A valid JSON object can still be wrong: `items` add up to 400 but `total` says 500.

### 2. How it works

**a. Tool schema.** Define one tool per extraction type. Claude returns a `tool_use` block whose `input` follows the schema. Add `"strict": true` at the top level of the tool definition and `"additionalProperties": false` on each object in `input_schema`. Claude's tokens are then constrained to the schema, so types and required fields always match. It still cannot check meaning, such as totals or a value in the wrong field.

**b. `tool_choice`:**

| Value | Meaning | Use when |
|---|---|---|
| `auto` | Claude may answer in text | Normal chat with tools |
| `any` | Claude must call *some* tool | Document type unknown and you have several extraction tools |
| `{"type": "tool", "name": "extract_metadata"}` | Claude must call that tool | You need a specific step first, for example run `extract_metadata` before anything else |

**c. Honest schema.**
- **Nullable or optional fields** (`"type": ["string", "null"]`) for anything the source may not state.
- **Enums with `"unclear"` and `"other"`**: `unclear` when the document gives no signal; `other` plus an `other_category_detail` string when it fits none of the values.
- **Format rules in the prompt**: dates as `YYYY-MM-DD`, amounts as plain numbers, `null` when not stated.

**d. Semantic checks in code.** Ask for `calculated_total`, `stated_total` and `conflict_detected`, and recompute the sum in Python. Schemas catch shape, not arithmetic.

**e. Absent vs wrong.** A `null` for something the document never says is correct. A bad date format is an error and is worth a retry with feedback (TS 4.4).

### 3. The thinking trade-off
With extended thinking, `tool_choice` may be only `auto` or `none`. A forced tool call (`any` or a named tool) returns HTTP 400 if `thinking` is enabled.

So for extraction you choose:
- **Forced tool, no `thinking`** (default for extraction; reliable and cheap), or
- **`thinking` with `auto`**, and handle the case where Claude answers in text.

Never send `temperature` with thinking. Leave `top_k`/`top_p` unset. In a tool loop, send thinking blocks back unchanged with their signatures.

---

## 🧪 Worked Example

**Invoice text**
```text
ACME Cloud   Total Due: $300.00
Hosting x2 @ $120 = $240     Support x1 @ $50 = $50
```
**Output** (note the `null`s and the flagged conflict)
```json
{
  "invoice_number": null,
  "vendor_name": "ACME Cloud",
  "issue_date": null,
  "due_date": null,
  "purchase_category": "software_subscription",
  "other_category_detail": null,
  "line_items": [
    {"description": "Hosting", "quantity": 2, "unit_price": 120.0, "total": 240.0},
    {"description": "Support", "quantity": 1, "unit_price": 50.0, "total": 50.0}
  ],
  "stated_total": 300.0,
  "calculated_total": 290.0,
  "conflict_detected": true
}
```
- The schema accepts this. It is valid JSON.
- Python sees `290 != 300`, so `conflict_detected` is true and a human or a retry resolves it.
- `invoice_number` is `null`. If it had been required, the model would likely invent one.

Request shape (see `build_extraction_request()` in [main.py](main.py)):
```python
{"model": "claude-haiku-4-5", "tools": [EXTRACTION_TOOL],
 "tool_choice": {"type": "tool", "name": "extract_invoice"}}   # no thinking, no temperature
```

---

## 🔑 Key Terms

- **Tool use**: Claude calls a tool; its `input` is your structured data.
- **`tool_choice`**: `auto`, `any`, a forced named tool, or `none`.
- **Syntax error**: invalid JSON. Tool schemas prevent these.
- **Semantic error**: valid JSON but wrong meaning. Needs validation in code.
- **Nullable field**: may be `null` when the source does not say.
- **Extensible enum**: fixed values plus `unclear` and `other` + detail.
- **`conflict_detected`**: flag set when computed and stated totals disagree.

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    Doc["Document"] --> Choice{"Which tool_choice?"}
    Choice -->|"type unknown, several tools"| Any["any"]
    Choice -->|"specific step first"| Forced["forced named tool"]
    Choice -->|"thinking needed"| Auto["auto + thinking<br>(forced tool not allowed)"]
    Any --> Call["tool_use with schema"]
    Forced --> Call
    Auto --> Call
    Call --> Check["Python validation<br>sum, dates, enum detail"]
    Check -->|"valid"| Done["Accept"]
    Check -->|"format or math error"| Retry["Retry with feedback (TS 4.4)"]
    Check -->|"null because absent"| Accept["Keep null<br>do not retry"]
```

---

## ⚠️ Exam Traps and Correct Patterns

### Trap 1: "Return JSON" in the prompt

Text output can come wrapped in markdown fences, with a trailing comment, or with a missing brace. `json.loads` then raises in production. A tool with `input_schema` makes the output arrive as a structured `tool_use` block.

```python
tools = [{"name": "record_invoice", "description": "Record extracted invoice fields.",
          "input_schema": {"type": "object", "properties": {
              "invoice_number": {"type": ["string", "null"]},
              "total": {"type": ["number", "null"]}}}}]
```

### Trap 2: Everything `required` forces fabrication

**Exam scenario**: The schema requires `invoice_number`, `vendor_name`, `issue_date`. A scanned receipt has no invoice number.

```text
ANTI-PATTERN: required: [invoice_number, ...]  -> model invents "INV-0001" to satisfy the schema.
PATTERN: only truly guaranteed fields required; others nullable/optional.
         "invoice_number": null  means "not in the document" (a correct answer, not an error).
```

### Trap 3: "The schema guarantees correctness"

A schema checks **shape**: types, required keys, enum values. It cannot check that line items add up.

```json
{"line_items_sum": 480.00, "stated_total": 840.00, "conflict_detected": true}
```

Compute `calculated_total` in code, compare to `stated_total`, and set `conflict_detected`. Do not trust the model's arithmetic or assume the schema covered it.

### Trap 4: Closed enum

```text
ANTI-PATTERN: category in ["invoice", "receipt", "contract"]  -> a purchase order is forced into one.
PATTERN: category in ["invoice", "receipt", "contract", "other", "unclear"]
         plus category_detail: "purchase order" when category is "other".
```

### Trap 5: `tool_choice` and thinking

| Need | Use |
|---|---|
| Must return structured output, document type unknown | `tool_choice: {"type": "any"}` (no thinking) |
| Must run one named extraction tool | `{"type": "tool", "name": ...}` (no thinking) |
| Thinking is on | Only `auto` or `none`. Forced or `any` returns HTTP 400. Also omit `temperature` |

---

## 📝 Exam-Style Practice Questions

**Q1 (Scenario 6).** Invoices from many vendors sometimes lack a PO number. With `po_number` required, the model returns values like `"PO-99999"`. What is the best change?
- A) Add "do not invent PO numbers" to the prompt only.
- B) Make `po_number` `["string", "null"]`, remove it from `required`, and say "null if not stated".
- C) Switch to JSON in a text reply and parse it.
- D) Run a second model at a higher temperature.

**Q2 (Scenario 6).** You have `extract_invoice`, `extract_receipt` and `extract_contract` tools. The document type is unknown and Claude sometimes replies in plain text. Which `tool_choice` fits?
- A) `auto`
- B) `{"type": "tool", "name": "extract_invoice"}`
- C) `any`
- D) `none`

**Q3 (Scenario 6).** A team enables extended thinking and forces `extract_invoice` with `tool_choice`. The API returns an error. What is the best fix?
- A) Add `temperature: 0`.
- B) Remove `thinking` for the forced extraction call (or use `auto` with thinking).
- C) Strip the thinking blocks from history.
- D) Raise `max_tokens` to 64000.

### Answers
**Q1: B.**
- A fails: a hard-required schema still pushes the model to fill the field.
- C fails: free text brings back syntax errors.
- D fails: higher temperature increases randomness, not honesty.

**Q2: C.**
- A fails: Claude may still answer in text.
- B fails: forces the invoice tool even for a contract.
- D fails: `none` prevents any tool call.

**Q3: B.**
- A fails: temperature is also rejected with thinking and does not address `tool_choice`.
- C fails: stripping blocks causes different errors and is not the cause here.
- D fails: token limits are unrelated to the `tool_choice` restriction.

---

## ✅ Self-Check Checklist
- [ ] I can say what tool use fixes (syntax) and what it does not (semantics).
- [ ] I can explain `auto`, `any` and a forced tool, with a use case for each.
- [ ] I know why nullable beats required for missing-prone fields.
- [ ] I can add `unclear` and `other` + detail to an enum.
- [ ] I know a forced tool cannot be combined with thinking.

**Memory hook**: *Schema for shape, null for honesty, code for sums.*

---

## 🛠️ Hands-on Workbook Guide

In [`ts_4_3_structured_output_tool_use.ipynb`](ts_4_3_structured_output_tool_use.ipynb):
1. **Step 1: Setup**: finds the repo root and adds it to the import path.
2. **Step 2: Schema and validator**: imports the nullable schema, request builder and validator from `main.py`.
3. **Step 3: Simulation**: validates an invoice with nulls and a conflicting total, and shows the thinking/forced-tool guard.
4. **Step 4: Verification**: asserts nulls are not errors, conflicts are flagged, and a forced tool with thinking is rejected.

Everything runs offline. The live extraction run in `main.py` is manual only (it uses the API).
