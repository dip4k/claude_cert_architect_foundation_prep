# Task Statement 4.6: Multi-Instance & Multi-Pass Review Architectures

## 🎯 Exam Objective
Understand how to eliminate author bias through independent Claude review instances and implement a two-pass review architecture (per-file local pass + cross-file integration pass).

---

## 🏗️ Architecture: Multi-Instance Two-Pass Review Pipeline

```mermaid
%%{init: {"flowchart": {"htmlLabels": true, "padding": 20}}}%%
flowchart TD
    Generator["Agent 1:<br/>Code Generator Instance"] --> Codebase["Generated Code Artifacts<br/>(auth.py, client.py)"]
    
    subgraph Pass1["Pass 1: File-Level Reviewers (Isolated)"]
        ReviewerA["Claude Instance A<br/>(Reviews auth.py)"]
        ReviewerB["Claude Instance B<br/>(Reviews client.py)"]
    end
    
    Codebase --> ReviewerA
    Codebase --> ReviewerB
    
    ReviewerA --> FileFindingsA["Local Issues:<br/>Off-by-one, typing, edge cases"]
    ReviewerB --> FileFindingsB["Local Issues:<br/>Error handling, logging"]
    
    subgraph Pass2["Pass 2: System Architecture Reviewer"]
        CrossReviewer["Claude Instance C<br/>(Cross-File Integration)<br/>Reviews interactions & API contracts"]
    end
    
    Codebase --> CrossReviewer
    CrossReviewer --> ContractFindings["Contract Mismatches:<br/>Token expiration mismatch,<br/>parameter name discrepancies"]
    
    FileFindingsA --> Aggregator["Synthesis Aggregator"]
    FileFindingsB --> Aggregator
    ContractFindings --> Aggregator
    
    Aggregator --> FinalAudit["Consolidated, Deduplicated<br/>Audit Report"]
```

---

## ⚠️ Anti-Patterns vs Best Practices

| Anti-Pattern (Fails on Exam) | Recommended Architectural Practice |
|---|---|
| **Author Self-Review**: The same agent generates code and then in the same prompt is asked "Now check if there are bugs in your code". (Symptom: confirmation bias). | **Independent Fresh Instances**: Spawn fresh review instances with zero generation memory. |
| **Monolithic Single Pass**: Reviewing a 20-file PR in a single prompt. (Symptom: misses both local syntax bugs and cross-module interface drifts). | **Two-Pass Architecture**: Pass 1 reviews individual files for micro-correctness; Pass 2 reviews cross-file contracts. |
