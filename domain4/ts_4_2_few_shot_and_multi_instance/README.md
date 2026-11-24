# Task Statement 4.2: Few-Shot Prompting for Consistent Output

> Scenarios: Scenario 6 (Structured Data Extraction) and Scenario 5 (CI review).

## In One Minute
- **What**: Put 2-4 short, targeted examples in the prompt.
- **Why**: Examples show Claude the exact output format and how to handle ambiguous cases. Rules alone often leave room to guess.
- **How**: Each example shows the input, the output, and *why* that action was chosen.
- **Include**: acceptable patterns vs genuine issues, different document layouts, and empty/null fields.
- **Exam answer in one line**: *A few well-chosen examples that explain the reasoning beat more rules or more examples.*

---

## 🧒 Explain Like I'm 13

**The picture:** Teaching a new helper to fill in forms. Two or three filled-in forms in **different styles** teach more than a page of rules. Include one where a box is empty and the right answer is "leave blank", or the helper will invent something.

**In plain steps:**
1. Pick 2 to 4 examples that sit on the tricky boundary.
2. Show input, output, and the **reason**.
3. Mix layouts (table, paragraph, receipt).
4. Include a "not present, so `null`" example and an "acceptable, do not flag" example.

**Tiny example:** Five invoices that all have the total at the bottom right will make Claude fail when the total is at the top.

---

## 📖 Concepts Explained

### 1. Why Few-Shot Examples Work: Show, Don't Just Tell
Written rules can be abstract and open to interpretation. When you tell a model to "be conservative" or "format nicely," it has to guess what you mean. 

Giving **2 to 4 concrete examples** of inputs and outputs removes that guesswork. Good examples don't just teach the shape of the data; they show **where the boundaries are** between acceptable code and real bugs, or how to handle missing data without making things up. By showing *why* an answer is right (with a short reasoning note), Claude learns the underlying logic and can apply it to new situations it hasn't seen before.

### 2. Four Key Syllabus Patterns Demonstrated Through Few-Shot Prompting
To maximize exam readiness and production reliability, few-shot demonstrations must target the primary failure modes tested in the CCAR-F blueprint:
1. **Ambiguous Tool Selection**: Demonstrating which tool to select when a user prompt contains multiple plausible identifiers (e.g. showing a query with both an order ID and customer email correctly routing to `lookup_order`).
2. **Acceptable Code Patterns vs Genuine Vulnerabilities**: Pairing contrastive examples showing why a mock credential in a test directory (`tests/test_auth.py: sk-ant-test_dummy`) is acceptable, while a hardcoded credential in an API handler (`src/api/client.py: sk-ant-live_key`) is a Critical security defect.
3. **Handling Varied Document Layouts**: Demonstrating extraction across structurally diverse documents—such as pulling citations from inline references (`[Author, 2024, p. 12]`) versus formal end-of-document bibliographies, or extracting operational metrics from narrative prose versus multi-column financial tables.
4. **Correct Handling of Missing Attributes**: Demonstrating that when a required document attribute (e.g. tax ID or shipping carrier) is physically missing from the source text, the model must output `null` or an empty list `[]` rather than fabricating plausible filler data.

### 3. The 2–4 Example Budget and the Law of Diminishing Returns
A common misconception is that more examples always improve accuracy. In production agent architectures:
- Providing 8–10 repetitive examples dramatically inflates turn token costs (consuming 2,000+ context tokens on every request) and induces **overfitting**, causing the model to rigidly parrot the syntax of the examples rather than generalizing.
- **The Optimal Architectural Standard**: Provide **2–4 carefully curated, structurally diverse examples**. Each example must carry an explicit `Reasoning:` clause explaining why the choice was made, giving Claude the conceptual principle needed to handle novel cases.

---

## 🧪 Worked Example

### ❌ Invalid Example (Anti-Pattern: 10 Identical Examples Without Reasons)
```text
# BROKEN: Floods the prompt with repetitive, easy examples and no reasoning
Prompt:
Classify tickets as "bug" or "feature_request":
Example 1: "Button broken" -> bug
Example 2: "App crashed" -> bug
Example 3: "Login failed" -> bug
... [8 more repetitive examples]

Why it fails in production:
1. High token cost: Burns 1,500+ context tokens on every request for zero extra learning.
2. Rigid overfitting: Claude copies exact phrasing instead of understanding the rule.
3. No reasoning: When given an ambiguous case like "Invoice page crashes on download", Claude flips a coin because it never learned whether crashes in billing count as billing or bug.
```

### ✅ Valid Example (Production Pattern: 2–4 Diverse Examples with Reasons)
```text
# CORRECT: 2-4 targeted examples on tricky boundaries with explicit "Why" notes
<examples>
Example 1 (ACCEPTABLE - do not report):
  Input: tests/test_auth.py:12 mock_key = 'sk-ant-test_dummy_000000000000'
  Verdict: NO_ISSUE
  Why: Mock key located in a test directory; not a leaked production credential.

Example 2 (GENUINE BUG - report):
  Input: src/auth.py:30 user = db.get(uid); return user.orders
  Verdict: BUG | MEDIUM | Check if user is None before accessing orders
  Why: db.get() can return None, which causes an unhandled AttributeError.

Example 3 (MISSING ATTRIBUTE - return null):
  Input: Purchase order with vendor name and total, but no tax number or due date.
  Verdict: {"stated_total": 120.0, "tax_id": null, "due_date": null}
  Why: Attributes not printed in document must be null; never fabricate placeholders.
</examples>

Varied structure examples:
  Inline:        "as shown by Lee (2021, p. 4)"       -> {"author": "Lee", "year": 2021, "page": 4}
  Bibliography:  "References: [1] Kim, J. (2019)..."  -> {"author": "Kim", "year": 2019, "page": null}
  None:          memo without citations               -> {"citations": []}
```

See `FEW_SHOT_EXTRACTION_EXAMPLES`, `VARIED_STRUCTURE_EXAMPLES`, and `REVIEW_FEW_SHOT_EXAMPLES` in [main.py](main.py). `validate_example_count()` enforces the 2-4 range.

---

## 🔑 Key Terms

- **Few-Shot Prompting**: An in-context learning technique where 2 to 4 concrete input-output demonstrations are included in the prompt to illustrate formatting and decision logic.
- **Targeted Example**: A demonstration chosen specifically to illustrate a difficult boundary case, such as an ambiguous classification or a missing attribute, rather than an obvious happy path.
- **Acceptable Pattern Demonstration**: An example showing code or syntax that looks unconventional but is legitimately safe, preventing overzealous false positives.
- **Genuine Vulnerability Demonstration**: An example showing a true critical defect along with its root-cause explanation, ensuring the model maintains high detection recall.
- **Latent Generalization**: The model's ability to apply the underlying rationale learned from few-shot examples to novel, unseen inputs instead of rote keyword matching.
- **Structural Layout Diversity**: Providing examples across varied visual arrangements (such as tabular grids, narrative paragraphs, and receipts) so the model does not overfit to a single template.

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    Task["Ambiguous task"] --> Pick["Pick 2-4 targeted examples"]
    Pick --> Pair["Acceptable pattern<br>+ genuine issue"]
    Pick --> Layout["Varied layouts<br>inline vs bibliography"]
    Pick --> Empty["Empty or null case"]
    Pair --> Prompt["Prompt: input, reason,<br>exact output format"]
    Layout --> Prompt
    Empty --> Prompt
    Prompt --> Result["Consistent format<br>fewer false positives<br>better generalisation"]
```

---

## ⚠️ Exam Traps and Correct Patterns

### Trap 1: A long rule list instead of examples for ambiguous cases

**Exam scenario**: Classify support tickets into `billing`, `bug`, `feature_request`. "Your invoice page crashes when I click download" gets different labels on different runs, even though the prompt has 14 rules.

Rules describe a boundary in words. An example shows where the boundary is. Add 2 to 4 examples for the **ambiguous** cases, with the reason:

```text
<examples>
  Ticket: "Invoice page crashes on download"
  Label: bug
  Why: the user-visible failure is a crash. Billing is only where it happens.

  Ticket: "I was charged twice"
  Label: billing
  Why: money amount is wrong; no software malfunction is described.
</examples>
```

### Trap 2: Asking for JSON with no example of the exact shape

"Return JSON" produces `{"total": 12}` in one run and `{"invoice_total": "$12.00"}` in another. Show the exact output in every example. For a guaranteed syntax, use a tool schema (TS 4.3). Examples guide the content, the schema guards the structure.

### Trap 3: Only showing bugs

If every example contains a defect, the model learns "unusual means defective" and flags harmless patterns.

```text
Include an ACCEPTABLE example:
  code: for i in range(len(items)): ...   # index needed for the log message below
  verdict: no issue. Why: the index is used. Do not flag index loops that use the index.
```

### Trap 4: One layout, and no example of absence

| Gap in examples | Failure on real input |
|---|---|
| Five invoices, all with the total at the bottom right | Fails on invoices with the total at the top, returns null |
| No example where a field is missing | Model fills the field with a plausible guess |

Fix: examples with different layouts, and at least one that returns `"po_number": null` with the reason "not present in the document".

---

## 📝 Exam-Style Practice Questions

**Q1 (Scenario 6).** Your extraction prompt works on tabular invoices but returns empty citations for papers whose references are in a bibliography at the end. What is the best change?
- A) Add five more tabular invoice examples.
- B) Add one example with inline citations and one with a bibliography, each showing the expected output.
- C) Lower the temperature.
- D) Add "extract all citations carefully" to the prompt.

**Q2 (Scenario 5).** A review prompt flags harmless code that the team uses on purpose. Which change reduces false positives while still catching real bugs?
- A) Add examples that show only buggy code.
- B) Add two examples: one acceptable pattern with the reason it is fine, one genuine issue with the reason it is a bug.
- C) Tell Claude to report only critical findings.
- D) Add twelve examples of acceptable code.

**Q3 (Scenario 6).** Some purchase orders lack a due date and the model writes made-up dates. What helps most?
- A) A rule: "never be wrong".
- B) A few-shot example where the document has no due date and the output is `null`, with the reason.
- C) Require `due_date` in every example.
- D) Retry until the date looks plausible.

### Answers
**Q1: B.**
- A fails: more of the same layout increases overfitting.
- C fails: temperature does not teach layouts.
- D fails: it names no concrete layout or output.

**Q2: B.**
- A fails: bug-only examples teach the model that anything unusual is a bug.
- C fails: it hides real high-impact issues without defining them.
- D fails: too many examples add cost and the model may copy surface form; it also lacks a genuine-issue example.

**Q3: B.**
- A fails: a vague instruction gives no pattern to copy.
- C fails: forcing a date in every example teaches fabrication.
- D fails: retrying cannot find a date that is not in the source.

---

## ✅ Self-Check Checklist
- [ ] I can explain why 2-4 targeted examples beat many similar ones.
- [ ] I can give the reason line for an acceptable-pattern example.
- [ ] I can write the exact review output format (location, issue, severity, suggested fix).
- [ ] I know which layouts to vary (inline vs bibliography, table vs narrative).
- [ ] I know to include an empty/null example.

**Memory hook**: *Few, varied, explained.*

---

## 🛠️ Hands-on Workbook Guide

In [`ts_4_2_few_shot_and_multi_instance.ipynb`](ts_4_2_few_shot_and_multi_instance.ipynb):
1. **Step 1: Setup**: finds the repo root and adds it to the import path.
2. **Step 2: Examples**: imports the extraction, varied-structure, and review examples from `main.py`.
3. **Step 3: Render**: builds the few-shot block and the independent-reviewer payload (used again in TS 4.6).
4. **Step 4: Verification**: asserts the 2-4 example rule, the null and empty cases, and the review format.

Everything runs offline; no API calls.

---

## 🧭 Navigation & Study Links
- ⬅️ **Previous Topic**: [TS 4.1: Explicit Criteria & Negative Boundaries](../ts_4_1_explicit_criteria_classification/README.md)
- 📋 **Domain Overview**: [Domain 4: Prompt Engineering & Structured Output](../README.md)
- ➡️ **Next Topic**: [TS 4.3: Reliable Structured Output via Tool Use](../ts_4_3_structured_output_tool_use/README.md)
- 🎯 **Scenario Practice**: [Master Scenario Practice](../../scenarios/MASTER_SCENARIO_PRACTICE.md)
