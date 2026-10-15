# Task Statement 3.5: Iterative Refinement & The Interview Pattern

## 🎯 Exam Objective
Understand how to apply the Interview Pattern to resolve underspecified requirements before code generation, use concrete I/O examples, and perform test-driven iterative refinement.

---

## 🏗️ Architecture: The Interview Gatekeeper Pattern

```mermaid
flowchart TD
    UserReq["User Prompt: 'Build an authentication service'"] --> Analyzer["Ambiguity & Scope Analyzer"]
    
    Analyzer --> AmbiguityCheck{"Scope Underspecified?"}
    
    AmbiguityCheck -- "Yes: Ambiguity Score > 0.4" --> Interview["Interview Mode Activated"]
    Interview --> Ask["Clarifying Questions (2-3 Options)<br/>Auth Type, DB & Session Model"]
    Ask --> UserFeedback["User Selects Exact Architecture"]
    
    UserFeedback --> ConcreteIO["Provide 2-3 Concrete Input/Output Examples"]
    AmbiguityCheck -- "No: Fully Specified" --> ConcreteIO
    
    ConcreteIO --> TestCases["Generate Test Suite First (TDD)"]
    TestCases --> CodeGen["Implement Targeted Solution"]
    CodeGen --> Verification["Run Offline Test Assertions"]
    Verification --> Success["Refinement Complete"]
```

---

## ⚠️ Anti-Patterns vs Best Practices

| Anti-Pattern (Fails on Exam) | Recommended Architectural Practice |
|---|---|
| **Silent Guesswork**: Claude assumes JWT + MongoDB without asking and implements 500 lines of throwaway code. | **The Interview Pattern**: Halt execution, outline 2-3 explicit options, and request user confirmation before writing code. |
| **Fragmented Hotfixes**: Fixing one bug at a time across 5 turns, introducing regression cycles. | **Interacting Issue Analysis**: Identify coupling across modules and resolve interacting defects in a unified plan. |
| **Abstract Specifications**: Describing output format purely in prose without examples. | **Concrete Examples**: Provide 2-3 exact Input/Output pairs with boundary conditions. |
