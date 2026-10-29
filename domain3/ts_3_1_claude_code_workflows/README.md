# Task Statement 3.1: Configure CLAUDE.md Files with Appropriate Hierarchy and Scoping

## In One Minute

- **What**: `CLAUDE.md` files give Claude Code standing instructions. *Where a file lives decides who gets it.*
- **Three scopes**: user (`~/.claude/CLAUDE.md`, personal, **not** in version control), project (`CLAUDE.md` or `.claude/CLAUDE.md`, shared), and directory (`<subdir>/CLAUDE.md`, shared).
- **Stay modular**: use `@import` and topic files in `.claude/rules/` (`testing.md`, `api-conventions.md`, `deployment.md`). Run `/memory` to see which memory files are loaded.
- **Exam answer in one line**: a new teammate is not getting the instructions because they sit in *user-level* config. Move them to project level.

## Overview

- **Domain**: Domain 3, Claude Code Configuration & Workflows (**20%** of the exam).
- **Scenarios**: Scenario 2 (Code Generation) and Scenario 5 (CI).
- **Goal**: put each instruction at the right scope, and keep the files small and modular.
- **Exam focus**: who receives a file, and how to diagnose a missing instruction.

## Concepts Explained

### Simple idea
Claude Code reads `CLAUDE.md` files at the start of a session. Think of them as the team handbook it always has open.

### Why it matters
If your standards live only in your home folder, your teammates and the CI job never see them. Claude then behaves differently for each person.

### How it works

| Scope | Location | Shared via version control? | Typical content |
|---|---|---|---|
| **User** | `~/.claude/CLAUDE.md` | No, personal | Your editor habits, shell aliases |
| **Project** | `./CLAUDE.md` or `.claude/CLAUDE.md` | Yes | Build and test commands, team standards |
| **Directory** | `services/billing/CLAUDE.md` | Yes | Rules for one subtree |

- **Load order** (Claude Code memory docs): files are **concatenated, not overridden**. Broadest first: managed policy (organisation), user, then project files from the repo root down to your working directory; `CLAUDE.local.md` is read last at each level. Subdirectory files load on demand when Claude works there. If two files contradict, Claude may follow either, so keep them consistent.
- **Context, not enforcement**: `CLAUDE.md` guides Claude but cannot force it. To block an action whatever Claude decides, use a `PreToolUse` hook (TS 1.5).
- **Topic files**: put focused guidance in `.claude/rules/*.md` (for example `testing.md`, `api-conventions.md`, `deployment.md`). Add `paths:` to make one conditional (see TS 3.3).
- **`@import` syntax**: write `@path/to/file` in a `CLAUDE.md` to pull that file in. Relative paths resolve from the importing file, and imports can nest up to four hops. Imported files still load into context, so imports organise a file but do not shrink it:
  ```markdown
  # Project Standards
  See @.claude/rules/testing.md for test conventions.
  ```
- **`/memory`**: shows which memory files Claude Code has loaded. Use it first when an instruction seems ignored.
- **Keep it short**: this repo keeps the root `CLAUDE.md` under 200 lines as a house rule. Move rare, task-specific procedures into skills (TS 3.2).

## Key Terms

- **User-level config**: `~/.claude/CLAUDE.md`. Personal. Never reaches teammates or CI.
- **Project-level config**: root `CLAUDE.md` or `.claude/CLAUDE.md`. Committed and shared.
- **Directory-level config**: a `CLAUDE.md` inside a subfolder. Committed and shared.
- **`@import`**: the `@path/to/file` syntax that includes another file so a `CLAUDE.md` stays modular.
- **`/memory`**: command that shows the loaded memory files.

## Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    User["User scope<br>~/.claude/CLAUDE.md<br>(personal, not in git)"]
    Project["Project scope<br>CLAUDE.md or .claude/CLAUDE.md<br>(shared via git)"]
    Dir["Directory scope<br>services/billing/CLAUDE.md<br>(shared via git)"]
    Rules["Topic files<br>.claude/rules/*.md<br>(shared via git)"]
    Context["Instructions Claude sees<br>for the file being edited"]

    User -->|"loads first"| Context
    Project -->|"then"| Context
    Dir -->|"then, if editing under it"| Context
    Rules -->|"always, or only when paths match"| Context
    Project -.->|"@import"| Rules
```

## Worked Example

A repo and two developers:

```text
~/.claude/CLAUDE.md                 <- user scope (Ana's laptop only)
my-repo/
  CLAUDE.md                         <- project scope
  .claude/rules/
    testing.md                      <- topic file
    api-conventions.md
    deployment.md
  services/billing/CLAUDE.md        <- directory scope
  services/billing/api.py
```

Ana edits `services/billing/api.py`. Claude sees: her user file, the project `CLAUDE.md`, and `services/billing/CLAUDE.md`.

Ben clones the repo and edits the same file. Claude sees: the project `CLAUDE.md` and `services/billing/CLAUDE.md`. **Ben never gets Ana's user file.** If the commit-message rules were only in Ana's user file, Ben's Claude ignores them.

Fix: move those rules to the project `CLAUDE.md` (or a topic file) and commit.

The `main.py` in this folder does this on the real files of this repo (`resolve_claude_md_chain`, `teammate_visible`).

## Exam Traps and Correct Patterns

| Concept | Correct | Trap | Why the trap fails |
|---|---|---|---|
| Team standards | Project-level file in version control | Putting them in `~/.claude/CLAUDE.md` | Teammates and CI never receive it |
| Big instruction set | Short `CLAUDE.md` plus `@import` and `.claude/rules/` topic files | One giant `CLAUDE.md` | Loads every time, buries the important parts |
| Missing instruction | Run `/memory`, check the scope of the file | Re-typing the rule in every prompt | Does not fix the cause; others still miss it |
| Secrets | Environment variables | Passwords in `CLAUDE.md` | Committed to git |

## Common Mistakes

- Saving team conventions in the user-level file because it was quicker.
- Assuming "it works on my machine" means the project is configured.
- Writing one huge `CLAUDE.md` instead of splitting topics.
- Putting rare task procedures in `CLAUDE.md` (they belong in skills).
- Forgetting that directory-level files only apply under their folder.

## Quick Decision Rules

| Question | Answer |
|---|---|
| Personal preference, only for me? | `~/.claude/CLAUDE.md` |
| Standard for the whole team? | Project `CLAUDE.md` or `.claude/CLAUDE.md` |
| Rules for one service folder? | That folder's `CLAUDE.md` |
| Topic guidance (testing, API, deploy)? | `.claude/rules/<topic>.md` |
| Rule spread across many folders, files by pattern? | Path-scoped rule (TS 3.3) |
| What did Claude actually load? | `/memory` |

## Claude 4.5 Notes

- Models in this repo: `claude-sonnet-4-5` (reasoning/coordinator), `claude-haiku-4-5` (workers).
- If extended thinking is on in API code: leave `temperature` unset, leave `top_k`/`top_p` unset, use only `tool_choice` `auto` or `none`, and echo thinking blocks with their signature unchanged.

## Exam-Style Practice Questions

**Q1 (Scenario 2: Code Generation).** A new developer clones the repo. Their Claude Code ignores the team's commit-message and test conventions. A senior developer's Claude Code follows them. What is the most likely cause?

- A) The conventions are in the senior developer's `~/.claude/CLAUDE.md`.
- B) The new developer must switch to `claude-sonnet-4-5`.
- C) Conventions only load for developers who have commit rights.
- D) The repo's `.claude/` folder is read only by CI.

**Q2 (Scenario 2).** The root `CLAUDE.md` has grown to 900 lines covering testing, API design and deployment. What is the best fix?

- A) Move it all to `~/.claude/CLAUDE.md`.
- B) Keep the root file short and split topics into `.claude/rules/testing.md`, `api-conventions.md` and `deployment.md` (use `@import` where needed).
- C) Delete it and paste the rules into each prompt.
- D) Copy the whole file into every subdirectory.

**Q3 (Scenario 5: CI).** A review job in CI seems to ignore a team rule. You reproduce locally in an interactive session. What do you check first?

- A) Ask Claude to recite its instructions and trust the answer.
- B) Run `/memory` to see which memory files were loaded and from which scope.
- C) Read the git history of `CLAUDE.md`.
- D) Restart the CI runner.

### Answers

**Q1: A.**
- B fails: the model choice does not decide whether `CLAUDE.md` files load.
- C fails: loading does not depend on commit rights.
- D fails: `.claude/` project files are read by developers' sessions too, not only CI.

**Q2: B.**
- A fails: user-level files are personal, so the team loses them.
- C fails: manual prompting is inconsistent and per person.
- D fails: copies drift apart and still load context that is not needed.

**Q3: B.**
- A fails: the model's recitation is not a reliable record of what was loaded.
- C fails: history shows edits, not what the session loaded.
- D fails: restarting changes nothing about which files exist at which scope.

## Self-Check Checklist

- [ ] I can name the three scopes and their file locations.
- [ ] I know the user-level file is not shared via version control.
- [ ] I can explain `@import` and `.claude/rules/` topic files.
- [ ] I know `/memory` shows loaded memory files.
- [ ] I can diagnose "teammate does not get the instructions".

**Memory hook**: *Home folder is private; the repo is shared.*

## Hands-on Workbook Guide

Open [`ts_3_1_claude_code_workflows.ipynb`](ts_3_1_claude_code_workflows.ipynb) (offline, no API calls). It runs the code in [main.py](main.py):

1. Setup and imports.
2. Resolve the real CLAUDE.md chain for a file and check which entries a teammate receives.
3. Load the real `.claude/rules/` files and see which match a file.
4. Assertions that confirm the order and the teammate view.

Next: [TS 3.2 Slash Commands and Skills](../ts_3_2_slash_commands_and_skills/README.md). Overview: [Domain 3 README](../README.md).
