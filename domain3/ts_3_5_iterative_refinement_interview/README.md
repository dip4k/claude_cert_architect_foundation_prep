# Task Statement 3.5: Iterative Refinement & The Interview Pattern

## 🎯 Exam Objective
Understand how to apply the Interview Pattern to resolve underspecified requirements before code generation, use concrete I/O examples, and perform test-driven iterative refinement.

---

## 🏗️ Architecture: The Interview Gatekeeper Pattern

```mermaid
flowchart TD
    UserReq["User Prompt: 'Build an authentication service'"] --> Analyzer["Ambiguity & Scope Analyzer"]
    
    Analyzer --> AmbiguityCheck{"Is Scope Underspecified?<br/>(Ambiguity Score > 0.4)"}
    
    AmbiguityCheck -- "Yes (Missing tokens, DB choice, auth type)" --> Interview["Interview Mode Activated"]
    Interview --> Ask["Clarifying Questions + Concrete Options:<br/>1. JWT vs Session cookies?<br/>2. PostgreSQL vs SQLite?<br/>3. Passwordless vs OAuth?"]
    Ask --> UserFeedback["User Selects Exact Architecture"]
    
    UserFeedback --> ConcreteIO["Provide 2-3 Concrete Input/Output Examples"]
    AmbiguityCheck -- "No (Fully specified)" --> ConcreteIO
    
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
