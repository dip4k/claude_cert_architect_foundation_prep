# Task Statement 1.7: Manage Session State, Resumption, and Forking

> Domain 1 (27% of the exam) · Scenarios 2 (Code Generation) and 4 (Developer Productivity) · [Back to Domain 1](../README.md)

## In One Minute

- **What**: a session is a saved conversation. You can continue it, branch it, or replace it with a summary.
- **Resume**: `claude --resume <session-name>` (or `-r`) continues a named session; name one with `--name` / `-n`. In the Agent SDK, pass `resume=<session_id>`. Good when nothing important changed.
- **Fork**: `fork_session` (CLI: `--fork-session` with `--resume`; Python SDK: `fork_session=True`; TypeScript: `forkSession: true`) makes an independent branch from a shared baseline. A fork copies the conversation history, not the files on disk. Good for comparing approaches.
- **Stale results**: if files changed, tell the resumed session which ones. If the old tool results are mostly stale, start a **new session with a structured summary**.
- **Exam answer in one line**: resume when results are still valid, fork to compare, summarise into a fresh session when tool results are stale.

---

## 📌 Overview

### Why it matters
Work spans days. On Monday Claude read `db/conn.py` and saw a pool size of 5. On Tuesday you edited it. If you resume Monday's session and say nothing, Claude still believes the old file. It will suggest changes to code that no longer exists. The old tool results are **stale**.

### What the exam tests
- `--resume <session-name>` for continuing named work.
- `fork_session` for parallel, independent exploration from one baseline.
- **Informing** a resumed session which files changed.
- Starting a **new session with a structured summary** when tool results are stale.
- Choosing between resuming and starting fresh.

---

## 📖 Concepts Explained

### 1. The simple idea
Three tools, three jobs:

| Tool | Job |
|---|---|
| **Resume** | Keep going exactly where you were |
| **Fork** | Try two directions from the same starting point |
| **Fresh session + summary** | Start clean with only the facts you trust |

### 2. Resume (`--resume <session-name>`)
Use it when earlier tool results are still true. If a few files changed, **say so**. In [main.py](main.py), `SessionManager.resume(name, changed_files=[...])` appends a user message that lists the changed files and asks the session to re-read them before relying on earlier output. With no changes, it adds nothing.

### 3. Fork (`fork_session`)
Use it to compare approaches. Branch A and Branch B both start from the same analysis. Edits in A never leak into B. In [main.py](main.py), `SessionState.fork` deep-copies the messages and records the parent session id, so the parent and each fork stay independent.

### 4. Fresh session with a structured summary
Use it when many tool results are stale, for example after a big merge. Write down what is still **verified** (decisions, confirmed facts, what changed), then start a new session with that summary and the new instruction. `SessionManager.resume_with_injected_summary` does this: the new session contains only the summary and the current task, never the old stale tool output.

### 5. How to choose

| Situation | Choose |
|---|---|
| Short break. Nothing changed | Resume |
| A few files changed | Resume and name the changed files |
| Compare two designs from one analysis | Fork |
| Large changes or a long gap. Results stale | New session with a structured summary |

---

## 🧪 Worked Example

Monday: you analyse a legacy database layer in session `legacy_db_analysis`. Claude reads `db/conn.py` (pool size 5).

| Day | Event | Right move |
|---|---|---|
| Monday | Baseline analysis is done | Keep session `legacy_db_analysis` |
| Monday | You want to compare Async SQLAlchemy and Prisma | **Fork** twice. Each branch gets its own question. The parent is untouched |
| Tuesday | You edit `db/conn.py` and `db/pool.py` | `--resume legacy_db_analysis`, then tell it: "These files changed: `db/conn.py`, `db/pool.py`. Re-read them." |
| Next week | You merged forty upstream commits | **New session** with a summary: "Decision: Async SQLAlchemy 2.0. 50 sync models. Changed since: schema, pool config." Then the new task: "Produce the migration plan." |

Each choice matches how much of the old context is still true.

---

## 🔑 Key Terms

- **Session**: a saved conversation that can be continued.
- **`--resume <session-name>`**: continue a named session.
- **`fork_session`**: create an independent branch from a baseline.
- **Stale tool results**: earlier file or data reads that no longer match reality.
- **Structured summary**: the verified facts and changes, used to seed a fresh session.
- **Changed-files notice**: a message telling a resumed session which files changed.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    Base["Baseline session<br>(analysis done)"] --> Choice{"What changed?"}

    Choice -->|"Compare two approaches"| Fork["fork_session"]
    Fork --> A["Branch A<br>(isolated)"]
    Fork --> B["Branch B<br>(isolated)"]

    Choice -->|"Nothing changed"| Resume["--resume session-name"]
    Choice -->|"A few files changed"| ResumeInform["--resume session-name<br>and list changed files"]

    Choice -->|"Many changes<br>(tool results stale)"| Fresh["New session with<br>structured summary"]
    Fresh --> Clean["Only verified facts<br>and the new task"]
```

---

## ⚠️ Exam Traps and Correct Patterns

| Topic | Correct pattern | Trap | Why the trap fails |
|---|---|---|---|
| **Compare designs** | Fork from the baseline | Try both in one thread | Ideas from A leak into B |
| **Small file changes** | Resume and name the changed files | Resume and say nothing | Claude trusts stale reads |
| **Large changes** | New session with a structured summary | Resume and hope | Stale tool results mislead the work |
| **Continuing named work** | `--resume <session-name>` | Paste a whole transcript into a new prompt | Wastes tokens and loses structure |

---

## ❌ Common Mistakes

- Resuming after big edits without a changed-files notice.
- Using one thread for two competing approaches.
- Writing a vague summary ("we looked at the database") instead of decisions and facts.
- Carrying old tool output into the fresh session, which defeats the purpose.
- Forking when the real need is just to continue.

---

## 💡 Quick Decision Rules

| Question | Answer |
|---|---|
| Nothing changed? | Resume |
| Some files changed? | Resume and list them |
| Many things changed, or results are stale? | Fresh session with summary |
| Two options to compare? | Fork |
| What goes in the summary? | Verified decisions, facts, what changed, the next task |

---

## 🧠 Claude 4.5 Notes

- Models: `claude-sonnet-4-5` for the session turns (`COORDINATOR_MODEL` in [main.py](main.py)), `claude-haiku-4-5` for simple workers.
- Extended thinking: `thinking={"type": "enabled", "budget_tokens": N}` with `N >= 1024` and `N < max_tokens`.
- With thinking on: no `temperature` (HTTP 400), no `top_k`, `top_p` only 0.95 to 1.0, and `tool_choice` only `auto` or `none`.
- When a session with thinking blocks is resumed, keep the assistant content unchanged, including `signature`. A fresh session starts with none.

---

## 📝 Exam-Style Practice Questions

**Q1.** After a long analysis session, a developer wants to compare two refactoring approaches that both start from that same analysis, without either approach influencing the other. What is the best way?

- A) Explore both in the same conversation, one after the other.
- B) Start two new sessions and redo the analysis in each.
- C) Resume the session and ask Claude to forget Approach A before starting B.
- D) Use `fork_session` to create two independent branches from the analysis baseline.

**Q2.** A developer resumes yesterday's session. Two files were edited overnight; everything else is the same. What is the best approach?

- A) Resume with `--resume <session-name>` and tell the session which two files changed so it re-reads them.
- B) Resume and say nothing. Claude will notice the differences.
- C) Delete the session and start without any summary.
- D) Fork the session and use the fork as is.

**Q3.** After merging forty upstream commits, a developer wants to continue an old investigation. Most earlier tool results no longer match the code. What is best?

- A) Resume and rely on the earlier tool results.
- B) Start a new session seeded with a structured summary of verified findings and the changes, plus the new task.
- C) Resume and ask Claude to guess which results are stale.
- D) Fork the old session and continue in the fork.

### Answers

**Q1: D.**
- A) The two approaches contaminate each other in one thread.
- B) Redoing the analysis twice wastes time and may give different baselines.
- C) Asking to "forget" is unreliable, and the earlier text is still in context.

**Q2: A.**
- B) Claude has no way to know that files changed outside the session.
- C) Throwing away the context loses useful work for a two-file change.
- D) A fork carries the same stale reads. It adds nothing for this case.

**Q3: B.**
- A) The old tool results are stale and would mislead the work.
- C) Claude cannot know which results are stale without re-reading everything.
- D) A fork still contains the stale tool results.

---

## ✅ Self-Check Checklist

- [ ] I can say when to use `--resume <session-name>`.
- [ ] I can say when to use `fork_session`.
- [ ] I know to tell a resumed session which files changed.
- [ ] I can explain when to start a new session with a structured summary.
- [ ] I know what makes a good summary: verified facts, decisions, changes, next task.

**Memory hook**: *"Resume if true, fork to compare, summarise if stale."*

---

## 🛠️ Hands-on Workbook Guide

Open [ts_1_7_session_management.ipynb](ts_1_7_session_management.ipynb) (offline, mock client):

1. **Baseline**: create the first session.
2. **Fork**: an independent branch that leaves the parent unchanged.
3. **Resume**: continue a named session and tell it which files changed.
4. **Fresh session with summary**: the recovery pattern for stale results.
5. **Checks**: forks stay isolated, the changed-files notice is added, and summaries carry only verified facts.

Code: [main.py](main.py) (live API, run manually only) · Offline tests: [tests/test_domain1_enhancements.py](../../tests/test_domain1_enhancements.py)
