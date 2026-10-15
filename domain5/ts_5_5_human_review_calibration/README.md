# Task Statement 5.5: Human Review & Confidence Calibration

## 🎯 Exam Objective
Understand how to design tiered routing based on calibrated confidence thresholds and enforce stratified audit sampling of high-confidence predictions to detect model drift.

---

## 🏗️ Architecture: Calibrated Tiered Routing Engine

```mermaid
flowchart TD
    Pred["Claude Extraction / Classification Result<br/>(confidence: score)"] --> Router{"Confidence Threshold Check"}
    
    Router -- "Score >= 0.90 (High Confidence)" --> SamplingCheck{"Stratified Random Audit?<br/>(e.g., 5% - 10% rate)"}
    
    SamplingCheck -- "Sampled (Audit)" --> HumanAudit["Human Audit Queue<br/>(Monitors Drift & ECE)"]
    SamplingCheck -- "Not Sampled" --> AutoApprove["Straight-Through Processing (STP)<br/>Immediate Auto-Approval"]
    
    Router -- "0.70 <= Score < 0.90 (Medium)" --> AsyncReview["Secondary Human Spot-Check Queue"]
    
    Router -- "Score < 0.70 (Low Confidence)" --> SyncEscalation["Mandatory Human-in-the-Loop Triage"]
```

---

## ⚠️ The "Zero Sampling of High Confidence" Exam Trap

### Trap:
A candidate assumes that if Claude's confidence is $\ge 0.95$, the system should process 100% automatically with zero human oversight.

### Exam Insight:
- Without **stratified random sampling** of high-confidence outputs:
  - Systematic hallucinations in niche categories go undetected for months.
  - Model drift (caused by API updates or shifting user data) is invisible until customers complain.
- **Architectural Requirement**:
  - Always maintain a **background audit stream (5–10% sampling)** of high-confidence outputs to continuously validate calibration against human ground truth.
