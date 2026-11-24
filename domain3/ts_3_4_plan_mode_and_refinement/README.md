# Task Statement 3.4: Determine When to Use Plan Mode vs Direct Execution

> Scenarios: Scenario 2 (Code Generation).

## In One Minute

- **Plan mode**: for large, multi-file, architectural changes, or when several approaches are valid. Claude investigates and proposes a plan before editing.
- **Direct execution**: for small, well-scoped changes, such as a single-file bug fix with a stack trace or adding one validation.
- **Explore subagent**: runs verbose discovery in its own context and returns a summary, so the main conversation stays clean.
- **Combine them**: plan mode to investigate, direct execution to implement the approved plan.
- **Exam answer in one line**: monolith to microservices means plan mode; a single-file fix with a stack trace means direct execution.

---

## Explain Like I'm 13

**The picture:** Renovating a house needs a blueprint first. Changing a light bulb does not. **Plan mode** is the blueprint step. **Direct execution** is just doing it. An **Explore subagent** is a scout who walks the neighbourhood and brings back a short report instead of you carrying every brick home.

**In plain steps:**
1. Big, many files, several valid designs: plan mode.
2. Small and clear (stack trace points at one line): direct execution.
3. Lots of reading needed: send an Explore subagent.
4. Large and unclear: plan first, then switch to direct to build.

**Tiny example:** "Split the monolith into microservices" without a plan means moving 40 files and then disagreeing about the boundaries.

---

## Concepts Explained

### 1. Architectural Risk and Blast Radius Assessment
When an engineer asks Claude Code to modify software, the primary architectural decision is choosing between **Plan Mode** and **Direct Execution Mode**. Making the wrong choice creates severe operational consequences:
- **Jumping Straight to Direct Execution on Architectural Tasks**: When tasked with restructuring a monolith into microservices, migrating a database ORM across 45 files, or integrating a new payment gateway, jumping directly into file editing is catastrophic. Claude will begin altering files sequentially, discovering circular dependencies or schema mismatches 30 files in, forcing massive rollbacks and corrupting repository state.
- **Using Plan Mode for Trivial Fixes**: Forcing a read-only architectural planning phase for a single-line null check with an unambiguous stack trace wastes turns and developer time.
- **The Core Rule**: Evaluate **blast radius, ambiguity, and architectural divergence** before selecting the mode.

### 2. When to Use Plan Mode
Plan Mode (`Shift+Tab` / `/plan`) switches Claude Code into a safe, read-only architectural exploration state. It is strictly required when:
- **Large-Scale Multi-File Changes**: The task touches multiple modules or services with cross-file contracts.
- **Multiple Valid Architectural Approaches**: Choosing between Event-Driven Pub/Sub vs Polling requires evaluating trade-offs and getting human engineer approval before writing code.
- **Unfamiliar Codebases with Hidden Dependencies**: You must understand existing conventions and call graphs before introducing new patterns.

### 3. The Explore Subagent: Context Preservation During Reconnaissance
During Plan Mode, exploring a large monorepo requires running dozens of `Glob` and `Grep` commands, which can produce thousands of lines of output:
- If this raw reconnaissance data is appended to the main conversation, the developer's context window fills with intermediate noise, degrading subsequent reasoning.
- Claude Code uses the dedicated **Explore subagent** to perform discovery in an isolated context buffer.
- The Explore subagent reads files, analyzes dependencies, and returns a concise, structured architectural summary to Plan Mode, leaving the main context clean and focused.

### 4. The Two-Phase Hybrid Workflow
The industry-standard production workflow combines both modes:
1. **Phase 1 (Reconnaissance & Architecture in Plan Mode)**: Claude explores the codebase, maps service boundaries, designs the step-by-step implementation blueprint, and presents it to the engineer for review.
2. **Phase 2 (Implementation in Direct Execution Mode)**: Once the human developer approves the blueprint, Claude switches into Direct Execution mode to execute surgical edits and run unit tests.

---

## 🔑 Key Terms

- **Plan mode (`Shift+Tab` / `/plan`)**: A read-only exploration state in Claude Code where the model audits architecture, explores dependencies, and proposes an actionable plan before touching code.
- **Direct execution mode**: The standard operational mode where Claude actively edits files, executes shell commands, and iterates on changes without preliminary design sign-off.
- **Explore subagent**: An internal subagent spawned during Plan Mode that executes exploratory file searches and code reading in an isolated context, returning a compact summary to the parent session.
- **Well-scoped surgical change**: A localized modification targeting an isolated file or bug with an explicit stack trace, suited for immediate direct execution without full architectural review.

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    Task["New task"] --> Size{"Large, multi-file,<br>or several designs?"}
    Size -->|"Yes"| Plan["Plan mode<br>Explore subagent investigates"]
    Plan --> Approve["Review and approve the plan"]
    Approve --> Direct["Direct execution<br>implement the plan"]
    Size -->|"No: small and clear"| Direct
```

---

## 🧪 Worked Example

### ❌ Invalid Example (Anti-Pattern: Immediate Direct Execution on 45-File Refactor)
```bash
# BROKEN: Direct execution on a complex multi-file architectural migration
claude "Migrate our monolith billing system to 3 microservices"

What happens:
1. Without drafting a plan or getting developer approval, Claude immediately begins modifying files.
2. It renames models in 15 files, deletes 5 endpoints, and creates 2 half-finished services.
3. Mid-refactor, the developer realizes Claude picked the wrong database boundary!
4. The codebase is broken, git status has 45 dirty files, and the developer must run git reset --hard!
```

### ✅ Valid Example (Production Pattern: Plan Mode Blueprint Approval & Staged Direct Execution)
```bash
# CORRECT: Plan Mode for discovery and blueprinting; Direct Execution for applying approved steps

# Step 1: Enter Plan Mode (Shift+Tab or `claude --plan`)
# Claude is restricted to read-only tools: Read, Grep, Glob (Edit and Bash are disabled)
# Claude drafts the architectural blueprint:
cat << 'EOF'
# Microservice Migration Blueprint
1. Phase 1: Extract shared billing data schemas into `pkg/billing_types/`
2. Phase 2: Create new standalone invoice service under `services/invoicing/`
3. Phase 3: Migrate REST call sites in api_router to invoke new service
4. Risks: Database migration required for invoice_items foreign keys.
EOF

# Step 2: Developer reviews and approves blueprint (or requests adjustments)
# Step 3: Switch to Direct Execution mode to execute approved steps with surgical edits and tests.
```

**Walkthrough comparing tasks:**
- **Task A (Multi-file / Ambiguous)**: "Split our billing monolith into three microservices. About 45 files are involved."
  - Multiple valid designs, many files, high blast radius $\to$ **Plan mode** (draft blueprint, developer approves, execute staged steps).
- **Task B (Local / Unambiguous)**: "`NullPointerException` at `invoice.py:88`, stack trace attached."
  - One file, known cause $\to$ **Direct execution** (read line 88, apply surgical fix, verify test suite passes).

`main.py` encodes this: `evaluate_execution_mode(45, True, False, False)` returns plan mode with phases `plan mode: investigate and propose` then `direct execution: apply the plan`. `evaluate_execution_mode(1, False, True, True)` returns direct execution.

---

## Exam Traps and Correct Patterns

### Trap 1: Direct execution for an architectural change

**Exam scenario**: "Restructure the monolith into microservices." Direct execution starts editing at once.

```text
Anti-pattern trace: Claude picks service boundaries by guess, moves 40 files, then you disagree
  with the boundary. Now you undo 40 file moves.
Pattern: plan mode. Claude reads, proposes boundaries, lists affected files and risks. You agree.
  Then switch to direct execution for the approved plan.
```

Signals for plan mode: many files, multiple valid approaches, architectural decision, unfamiliar code. File count is one signal, not a rule.

### Trap 2: Plan mode "to be safe" on a one-line fix

**Exam scenario**: A stack trace points at a null check in `user_service.py` line 88.

Plan mode here adds a proposal step, an approval step, and no benefit, since the cause and fix are clear. Use direct execution: fix, run the tests.

### Trap 3: Verbose discovery in the main chat

Reading 60 files to answer "where is auth handled?" leaves the main context full of file contents. Delegate to an **Explore** subagent. It reads in its own context and returns a summary, so the main conversation keeps room for the real work.

### Trap 4: One mode for the whole job

| Job | Right mix |
|---|---|
| Large task with an unclear start | Plan mode to investigate and propose, then direct execution to implement |
| Typo, rename in one file | Direct only |

Using plan for everything wastes time. Using direct for everything risks expensive rework on large changes.

---

## Exam-Style Practice Questions

**Q1 (Scenario 2: Code Generation).** You must restructure a monolith into microservices. The change spans many files and has several valid designs. Which workflow fits?

- A) Direct execution, starting with the first service.
- B) Plan mode to explore and propose before editing.
- C) Run it once in CI with `-p`.
- D) Add 10 example microservices to `CLAUDE.md`.

**Q2 (Scenario 2).** A production error shows a clear stack trace pointing at one function in one file. What is the best approach?

- A) Plan mode with an Explore subagent across the whole repo.
- B) Plan mode, then ask for three alternative designs.
- C) Direct execution: fix the function and run the tests.
- D) Open a design review before touching any file.

**Q3 (Scenario 5: CI flavour).** You must replace a logging library used at unknown places across the codebase. The call sites are not mapped yet. What is the best workflow?

- A) Direct execution from the start, fixing call sites as you find them.
- B) Plan mode for everything, including the final edits.
- C) Plan mode to investigate (Explore subagent returns a summary), then direct execution of the approved plan.
- D) Skip investigation and let CI find the call sites.

### Answers

**Q1: B.**
- A fails: large, multi-design work needs agreement before edits.
- C fails: `-p` is for non-interactive runs; it does not choose a design.
- D fails: `CLAUDE.md` examples do not replace investigating this codebase.

**Q2: C.**
- A fails: exploring the whole repo is overkill for a known location.
- B fails: there is one obvious fix; alternatives add no value.
- D fails: process overhead for a small, well-scoped change.

**Q3: C.**
- A fails: unknown scope makes edits-as-you-go risky and incomplete.
- B fails: after the plan is approved, direct execution is the efficient way to implement.
- D fails: CI is a late check, not a discovery tool.

---

## ✅ Self-Check Checklist

- [ ] I can list signals for plan mode and for direct execution.
- [ ] I know the monolith to microservices example is plan mode.
- [ ] I know a single-file fix with a stack trace is direct execution.
- [ ] I can explain what the Explore subagent isolates.
- [ ] I can describe the hybrid: plan to investigate, direct to implement.

**Memory hook**: *Big or unclear: plan first. Small and clear: just do it.*

---

## 🛠️ Hands-on Workbook Guide

Open [`ts_3_4_plan_mode_and_refinement.ipynb`](ts_3_4_plan_mode_and_refinement.ipynb) (offline). It uses [main.py](main.py):

1. Setup and imports.
2. Run `evaluate_execution_mode` on the two example tasks.
3. Inspect the decision phases and the Explore subagent flag.
4. Assertions on both decisions.

---

## 🧭 Navigation & Study Links
- ⬅️ **Previous Topic**: [TS 3.3: Path-Specific Rules & Directory Scoping](../ts_3_3_path_specific_rules/README.md)
- 📋 **Domain Overview**: [Domain 3: Claude Code & Developer Workflows](../README.md)
- ➡️ **Next Topic**: [TS 3.5: Interactive Refinement & Plan Clarification](../ts_3_5_iterative_refinement_interview/README.md)
- 🎯 **Scenario Practice**: [Master Scenario Practice](../../scenarios/MASTER_SCENARIO_PRACTICE.md)
