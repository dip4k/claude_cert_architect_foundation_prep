# Task Statement 5.6: Provenance and Uncertainty in Multi-Source Synthesis

> **Domain 5 (15% of exam)** | Scenario focus: **3 - Multi-Agent Research System** | Folder: `ts_5_6_provenance_and_uncertainty` | Previous: [TS 5.5](../ts_5_5_human_review_calibration/README.md) | Back to: [Domain 5 overview](../README.md)

> **Folder note:** Provenance helpers also appear in the [TS 5.2](../ts_5_2_escalation_and_provenance/README.md) folder for old imports. The canonical guide and code are here.

## In One Minute

- **What:** Every claim in a synthesised report must point back to its source.
- **Why it matters:** Summaries often drop the link between a claim and its evidence. Readers then cannot check it.
- **When sources disagree:** annotate both values with sources. Never average, never pick one silently.
- **Dates matter:** different dates (or periods) can explain a "contradiction".
- **Exam answer in one line:** *Keep claim-source mappings, annotate conflicts, include dates, separate established from contested.*

---

## 🧒 Explain Like I'm 13

**The picture:** Two news sources give different numbers. A good reporter shows **both**, with the name and date of each, and explains why they might differ. They do not average the numbers (nobody published that), and they do not quietly pick one.

**In plain steps:**
1. Keep each claim attached to its source and date through every summary.
2. Same metric, same period, different values: show both as contested.
3. Different years: show a timeline, it is not a conflict.
4. Split the report into established and contested.
5. Tables for finance, prose for news, lists for technical findings.

**Tiny example:** 1,200 employees in 2023 and 1,850 in 2025 is growth, not a contradiction.

---

## 📖 Concepts Explained

### 1. The Provenance Loss Trap in Multi-Source Summarization
When an orchestration system ingests research from multiple subagents, standard text summarization acts as a destructive compression algorithm:
- Verbatim evidence excerpts and source document citations are severed from individual claims.
- Publication and collection dates are dropped, flattening temporal changes.
- In subsequent turns, the agent presents assertions without attribution, making fact-checking impossible and hallucinating authority.
- **The Architectural Standard**: Every finding returned by a subagent must adhere to a strict **Claim-Source Mapping** schema containing: `claim`, `verbatim_excerpt`, `source_url_or_document`, `publication_date`, and `methodology`. Downstream synthesis agents must preserve and merge these mappings rather than dissolving them into unstructured prose.

### 2. Never Average Conflicting Statistics from Credible Sources
A signature scenario tested on the CCAR-F certification exam:
- Source A (Reuters) reports Q3 electric vehicle market share at 18.2%.
- Source B (Bloomberg) reports Q3 electric vehicle market share at 21.5%.
- **The Catastrophic Anti-Pattern**: The synthesis agent computes the arithmetic mean (19.85%) or arbitrarily picks one source without explanation. Averaging two credible measurements creates a **fabricated number that neither source reported**, violating journalistic and architectural integrity.
- **The Correct Architectural Action**: **Preserve both figures explicitly with source attribution and methodology notes**: *"Reuters reported 18.2% based on passenger vehicle registrations, while Bloomberg reported 21.5% including commercial fleet deliveries."*

### 3. Collection Dates Prevent False Temporal Contradictions
Apparent contradictions in enterprise data often reflect temporal change rather than factual error:
- Report A states Company X has 1,200 employees; Report B states Company X has 1,850 employees.
- If dates are omitted, the synthesis agent flags an unresolvable contradiction or rejects one document.
- When **publication and data collection dates** are preserved in structured metadata, the agent correctly recognizes organic headcount growth across consecutive years (`2024-Q1` vs `2026-Q1`) rather than a data conflict.

### 4. Structuring Reports: Established vs Contested Findings
To give executive readers instant clarity on confidence levels, multi-agent synthesis reports must separate findings into two explicit structural sections:
- **Well-Established Findings**: Facts and metrics where all credible sources corroborate the observation.
- **Contested or Divergent Findings**: Metrics, market estimates, or projections where credible sources diverge, explicitly annotating the methodological variations between sources.

### 5. Multi-Modal Content Type Formatting
Avoid converting all findings into uniform paragraphs of text:
- **Financial & Operational Data**: Render as structured Markdown **tables** with aligned columns and currency units.
- **News, Strategic Narratives & Incident Context**: Render as clear, cohesive **prose**.
- **Technical Invariants & API Specifications**: Render as structured bulleted **lists** with bold invariant headers.

---

## 🧪 Worked Example

### ❌ Invalid Example (Anti-Pattern / What Breaks)
*(Anti-Pattern: Averaging Conflicting Numbers & Omitting Dates)*
```text
# BROKEN 1: Averaging conflicting numbers into a fake mean
Source 1 (Oct 1 Preliminary Press Release): Revenue = $1.2B
Source 2 (Oct 15 Audited SEC 10-Q): Revenue = $1.4B
Synthesizer Output: "The company reported an average revenue of $1.3B."
Why it fails in production: Neither source said $1.3B! Averaging invents a fictional third number
and destroys legal and financial auditing compliance!

# BROKEN 2: Treating temporal differences as contradictions due to missing timestamps
Source A (2024-Q1): Headcount = 1,200 employees
Source B (2026-Q1): Headcount = 1,850 employees
Synthesizer Output: "CONTRADICTION DETECTED: Sources disagree on company headcount."
Why it fails: Omitting collection timestamps turns normal organizational growth into false contradictions!
```

### ✅ Valid Example (Production Pattern)
*(Production Pattern: Claim-to-Source Mapping & Side-by-Side Attribution)*
```markdown
# CORRECT: Preserving both statistics with dates, methodology, and direct citations

## Established Findings
- **Headcount**: 12,500 employees as of October 15, 2024 [SEC 10-Q Filing, payroll records].

## Temporal Progression (Timeline)
- **Inventory Levels**:
  - June 30, 2025: 50,000 units [Warehouse Audit Report A]
  - September 30, 2026: 12,000 units [Warehouse Audit Report B]
  *(Reflects seasonal drawdown rather than data conflict)*

## Contested & Divergent Findings
| Metric | Reported Value | Source | Publication Date | Accounting Method |
| :--- | :--- | :--- | :--- | :--- |
| **Q3 2024 Revenue** | $1.2B | Press Wire Release | 2024-10-01 | Preliminary Unaudited |
| **Q3 2024 Revenue** | $1.4B | SEC 10-Q Filing | 2024-10-15 | Formal Audited Filing |

*Note: The formal SEC filing reflects post-close adjustments and represents the authoritative figure.*
```

**Walkthrough:**
Subagents report:

| Metric | Value | Source | Pub. date | Period | Method |
|---|---|---|---|---|---|
| Q3 revenue | \$1.2B | Press wire | 2024-10-01 | 2024-Q3 | Preliminary |
| Q3 revenue | \$1.4B | 10-Q filing | 2024-10-15 | 2024-Q3 | Audited |
| Inventory | 50,000 units | Report A | 2025-06-30 | 2025-06 | Warehouse count |
| Inventory | 12,000 units | Report B | 2026-09-30 | 2026-09 | Warehouse count |
| Headcount | 12,500 | 10-Q filing | 2024-10-15 | n/a | Payroll |

**Synthesis result:**
- **Q3 revenue:** same period, different values $\to$ **contested**. Show both with source and method. Never average.
- **Inventory:** different periods $\to$ **temporal difference**, not a conflict. Present as a dated timeline.
- **Headcount:** single verified source $\to$ **established**.

`ProvenanceSynthesizer` and `render_report()` in `main.py` produce exactly this.

---

## 🔑 Key Terms

- **Claim-source mapping**: The programmatic association linking an extracted factual statement directly to its source document, verbatim text excerpt, publication date, and methodology.
- **Contested finding**: An architectural classification for metrics where two or more credible sources report divergent values for the exact same reporting period, requiring side-by-side presentation rather than mathematical averaging.
- **Temporal difference**: An apparent numerical disagreement between sources that actually represents valid evolution over different points in time, resolved by formatting the values as a dated chronological progression.
- **Methodology annotation**: Explicit explanatory text detailing how an extracted figure was calculated or gathered (such as distinguishing audited financial statements from preliminary analyst estimates).

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    SubA["Subagent A<br>claim + source + excerpt + date"] --> Merge["Synthesiser:<br>group by metric"]
    SubB["Subagent B<br>claim + source + excerpt + date"] --> Merge
    Merge --> Same{"Same value?"}
    Same -->|"Yes"| Est["Established findings"]
    Same -->|"No"| Period{"Different periods?"}
    Period -->|"Yes"| Time["Dated timeline<br>(not a conflict)"]
    Period -->|"No"| Cont["Contested findings<br>(both values + sources)"]
    Est --> Report["Report by content type<br>(table, prose, list)"]
    Time --> Report
    Cont --> Report
```

---

## ⚠️ Exam Traps and Correct Patterns

### Trap 1: Averaging or silently choosing between two sources

**Exam scenario**: Source A (Gartner) says the 2025 market is \$12.1B. Source B (IDC) says \$9.8B.

```text
ANTI-PATTERN: "The market is about $11B."   (a number neither source reported)
ANTI-PATTERN: "The market is $12.1B."       (picked the bigger publisher, hid the disagreement)

PATTERN:
  CONTESTED: 2025 market size
    - $12.1B (Gartner, report dated 2025-06, includes services)
    - $9.8B  (IDC, report dated 2025-09, hardware only)
  Note: definitions differ, so the numbers may not be comparable.
```

Show both values with their sources, and annotate the likely reason.

### Trap 2: Treating a date difference as a contradiction

```text
Source 1 (2023): "Company has 1,200 employees."
Source 2 (2025): "Company has 1,850 employees."
NOT a conflict. It is change over time. Report with dates:  2023: 1,200 -> 2025: 1,850.
```

Rule: same metric and same period with different values is contested. Different periods is a timeline.

### Trap 3: Summaries that lose claim-source links

A subagent returns `{claim, source, date}`. Synthesis that rewrites them into prose without sources leaves unattributed facts that nobody can verify. Keep the mapping through the summary, and name source and date next to each claim.

### Trap 4: Everything at the same certainty

| Section | Content |
|---|---|
| Established | Claims with agreement or a single reliable cited source |
| Contested | Claims where sources disagree, shown side by side |
| Not found | Areas checked with no evidence |

A flat list makes a disputed number look as solid as a confirmed one.

### Trap 5: One format for all content

Financial figures go in a table, news in prose, technical findings in a list. Forcing everything into bullets loses structure and comparisons.

---

## 📝 Exam-Style Practice Questions

**Q1 (Scenario 3).** Two subagents report different market-size statistics for the same year, from two credible sources. What should the synthesis agent do?

- A. Report the average.
- B. Keep the number from the larger publisher.
- C. Report both values, each attributed to its source, and note any known method difference.
- D. Omit the metric.

**Q2 (Scenario 3).** A report says revenue was \$800M (published 2024) and \$950M (published 2026). The synthesiser flags a "conflict". What was missed?

- A. Nothing; this is a real contradiction.
- B. The dates and periods; the values may describe different years.
- C. The need to average them.
- D. The need for a longer summary.

**Q3 (Scenario 3).** The final report mixes quarterly financials, news events and technical findings in one bullet list, and many claims lack sources. What two improvements fit best?

- A. Shorten everything into one paragraph and remove the sources.
- B. Keep claim-source mappings and render each content type suitably (table, prose, list).
- C. Merge all claims into one confidence score.
- D. Sort alphabetically.

### Answers

- **Q1: C.** A fails: it invents a number. B fails: it hides a credible source. D fails: it throws away evidence.
- **Q2: B.** A fails: it ignores that values describe different times. C fails: averaging is never right. D fails: length does not help.
- **Q3: B.** A fails: it removes traceability. C fails: a single score hides what is contested. D fails: order does not fix traceability or format.

---

## ✅ Self-Check Checklist

- [ ] I can list what a claim-source mapping contains.
- [ ] I know why conflicting values are annotated, not averaged.
- [ ] I can explain how dates turn a "conflict" into a timeline.
- [ ] I can describe a report that separates established from contested findings.
- [ ] I know the right format for financial, news and technical content.

**Memory hook:** *"Every claim carries its receipt."*

---

## 🛠️ Hands-on Workbook Guide

Notebook: [`ts_5_6_provenance_and_uncertainty.ipynb`](ts_5_6_provenance_and_uncertainty.ipynb). Code: [`main.py`](main.py). Both run offline.

1. **Record claims:** `ProvenanceSynthesizer.add_claim()` with excerpt, date, methodology, period.
2. **Classify:** `synthesize_metrics()` returns `CONSENSUS`, `PRESERVED_CONFLICT` or `TEMPORAL_DIFFERENCE`.
3. **Render:** `render_claims()` per content type; `render_report()` for the two-section layout.
4. **Verify:** `uv run pytest tests/test_domain5_enhancements.py -q` in WSL.

**Related:** [TS 5.1](../ts_5_1_context_preservation/README.md) (structured subagent output) | [TS 5.3](../ts_5_3_error_propagation_coverage/README.md) (coverage annotations).

---

## 🧭 Navigation & Study Links
- ⬅️ **Previous Topic**: [TS 5.5: Human Review Calibration & Uncertainty Triage](../ts_5_5_human_review_calibration/README.md)
- 📋 **Domain Overview**: [Domain 5: Operational Excellence, Monitoring & Production Readiness](../README.md)
- ➡️ **Next Topic**: [Master Scenario Practice](../../scenarios/MASTER_SCENARIO_PRACTICE.md)
- 🎯 **Scenario Practice**: [Master Scenario Practice](../../scenarios/MASTER_SCENARIO_PRACTICE.md)
