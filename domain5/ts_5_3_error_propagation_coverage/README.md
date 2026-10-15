# Task Statement 5.3: Multi-Agent Error Propagation & Coverage Tracking

## 🎯 Exam Objective
Understand how to propagate structured errors across multi-agent hierarchies, distinguish valid empty results from upstream system failures, and annotate partial synthesis coverage.

---

## 🏗️ Architecture: Coverage & Error Disambiguation

```mermaid
%%{init: {"flowchart": {"htmlLabels": true, "padding": 20}}}%%
flowchart TD
    Coordinator["Coordinator Agent"] --> SubA["Subagent A: Regulatory DB"]
    Coordinator --> SubB["Subagent B: Market Data API"]
    Coordinator --> SubC["Subagent C: Internal Wiki"]
    
    SubA --> ResA["status: SUCCESS<br/>records: 14 matches"]
    SubB --> ResB["status: UPSTREAM_FAILURE<br/>error: HTTP 504 Timeout"]
    SubC --> ResC["status: VALID_EMPTY<br/>records: 0 (No policy found)"]
    
    ResA --> Synthesizer["Coverage-Aware Synthesizer"]
    ResB --> Synthesizer
    ResC --> Synthesizer
    
    Synthesizer --> Decision{"Any Data Source Incomplete?"}
    
    Decision -- "Subagent B Failed (Timeout)" --> Partial["Annotate PARTIAL_COVERAGE<br/>Omit missing trends with warning"]
    
    Decision -- "Subagent C Empty Result" --> Legitimate["Valid Finding:<br/>No existing restrictions"]
```

---

## ⚠️ Critical Exam Distinction

| Event | Status Code | Synthesizer Action |
|---|---|---|
| Search query returns 0 documents in healthy database | `VALID_EMPTY` | Report finding: "No applicable policies exist." |
| Upstream database times out / network socket closes | `UPSTREAM_FAILURE` | **DO NOT report "No records exist"**! Must flag `PARTIAL_COVERAGE` with degraded confidence warning. |
| Malformed query / bad parameter | `VALIDATION_ERROR` | Retry or fail fast with parameter correction. |
