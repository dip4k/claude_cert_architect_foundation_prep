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

### 1. Why it matters
- Without examples, output format drifts: sometimes prose, sometimes a table, sometimes missing fields.
- Without examples of acceptable code, the model flags everything that looks unusual.
- Without layout variety, extraction works on one document style and returns nulls on the next.

### 2. How it works
1. **Pick 2-4 examples**, aimed at the cases where the model is unsure.
2. **State the reason** in each example ("ACCEPTABLE: mock key in a test file").
3. **Show the exact format**: for reviews, `location | issue | severity | suggested_fix`.
4. **Pair opposites**: one acceptable pattern, one genuine issue.
5. **Vary the structure**: inline citations (`Lee, 2021, p. 4`) vs a bibliography at the end; a table vs a narrative paragraph.
6. **Include an empty case**: a document with no citations returns `[]`, a missing date returns `null`.

Why reasons matter: the model learns the *principle* ("test mocks are not live secrets"), so it generalises to a mock it has never seen.

### 3. Where more examples stop helping
Five or six near-identical examples add cost and make the model copy their surface form. A small, varied set generalises better.

---

## 🧪 Worked Example

**Review prompt with two examples**
```text
Output format: location | issue | severity | suggested_fix

Example 1 (ACCEPTABLE - do not report)
  tests/test_auth.py:12  mock_key = 'sk-ant-test_dummy_000000000000'
  Reason: mock key in a test file, not a live credential.

Example 2 (GENUINE - report)
  src/auth.py:30  user = db.get(uid); return user.orders
  Output: src/auth.py:30 | possible None dereference | MEDIUM | if user is None: raise UserNotFound(uid)
  Reason: get() can return None, so .orders raises AttributeError.
```

**Extraction prompt with a null example**
```text
Input: Purchase order with no tax number and no due date.
Output: {"stated_total": 120.0, "due_date": null, "tax_id": null, "conflict_detected": false}
Reason: the document does not state them, so return null. Never invent.
```

**Varied structure**
```text
Inline:        "as shown by Lee (2021, p. 4)"       -> {"author": "Lee", "year": 2021, "page": 4}
Bibliography:  "References: [1] Kim, J. (2019)..."  -> {"author": "Kim", "year": 2019, "page": null}
None:          memo without citations               -> {"citations": []}
```

See `FEW_SHOT_EXTRACTION_EXAMPLES`, `VARIED_STRUCTURE_EXAMPLES`, and `REVIEW_FEW_SHOT_EXAMPLES` in [main.py](main.py). `validate_example_count()` enforces the 2-4 range.

---

## 🔑 Key Terms

- **Few-shot prompting**: giving worked examples inside the prompt.
- **Targeted example**: one that covers an ambiguous case, not an easy one.
- **Acceptable pattern**: code that looks odd but is fine; showing it cuts false positives.
- **Genuine issue**: a real defect; showing it keeps recall.
- **Generalisation**: handling unseen inputs because the example taught the reason.
- **Varied structure**: examples with different layouts of the same information.

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
    Pair --> Prompt["Prompt: input, reason, exact output format"]
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
