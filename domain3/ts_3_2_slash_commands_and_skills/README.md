# Task Statement 3.2: Configure Custom Slash Commands and Skills

> Scenarios: Scenario 2 (Code Generation), also useful in Scenario 5.

## In One Minute

- **Slash command** = a saved prompt. A **project-scoped command** lives in `.claude/commands/` and is shared through version control. A **user-scoped command** lives in `~/.claude/commands/` and is personal.
- **Skill** = an on-demand task workflow in `.claude/skills/<name>/SKILL.md`. Frontmatter keys: `context: fork`, `allowed-tools`, `argument-hint`.
- **`context: fork`** runs the skill in an isolated context, so noisy exploration does not fill your main conversation. Only the result comes back.
- **Skills vs CLAUDE.md**: skills load on demand for a task; `CLAUDE.md` is always loaded for universal standards. Personal skill variants go in `~/.claude/skills/` with a *different name*.
- **Exam answer in one line**: a team `/review` command goes in `.claude/commands/` in the repo.

---

## Explain Like I'm 13

**The picture:** A slash command is a **shortcut button** on the shared remote. A skill is a **recipe card** that can be cooked in a separate kitchen (`context: fork`) so the mess stays out of your main kitchen. Buttons and cards in the repo are shared. Ones in your home folder are yours.

**In plain steps:**
1. Team shortcut: `.claude/commands/`.
2. Multi-step workflow: a skill in `.claude/skills/`.
3. Messy output? Add `context: fork`; only a short summary comes back.
4. Want your own variant? Copy it to `~/.claude/skills/` with a different name.
5. Rule that must always apply? That is `CLAUDE.md`, not a skill.

**Tiny example:** An audit skill that only reads files should be limited to `Read`, `Grep`, `Glob`.

---

## 📖 Concepts Explained

### Why it matters
If a shared `/review` command sits in your home folder, teammates cannot use it. If a noisy audit runs in the main conversation, it floods the context and crowds out your real work.

### How it works

**Where things live**

| Item | Location | Shared? |
|---|---|---|
| Project-scoped command | `.claude/commands/<name>.md` | Yes, via version control |
| User-scoped command | `~/.claude/commands/<name>.md` | No, personal |
| Project skill | `.claude/skills/<name>/SKILL.md` | Yes |
| Personal skill | `~/.claude/skills/<name>/SKILL.md` | No |

**Skill frontmatter keys** (the ones this task statement covers)

| Key | Meaning |
|---|---|
| `context: fork` | Run in an isolated context; return only a summary |
| `allowed-tools` | Tools the skill may use **without a permission prompt** (exam wording: restricts tool access). Other tools stay under normal permissions; `disallowed-tools` removes tools |
| `argument-hint` | Hint shown to the user about the expected argument |

- **Fork**: verbose or exploratory work (reading many files, long searches) stays in the fork. The main conversation gets the summary.
- **Personal variants**: copy a team skill to `~/.claude/skills/` and give it a **different name**, so you do not change the shared one.
- **Skill or CLAUDE.md?** Universal standards that always apply go in `CLAUDE.md`. Task workflows that apply sometimes go in a skill.

---

## 🔑 Key Terms

- **Project-scoped command (`.claude/commands/<name>.md`)**: A custom slash command stored in the repo and committed to git so every team member can execute standardized prompts.
- **User-scoped command (`~/.claude/commands/<name>.md`)**: A personal slash command kept in the developer's home directory for private prototyping without altering shared repository configs.
- **Agent skill (`.claude/skills/<name>/SKILL.md`)**: A specialized, on-demand procedure equipped with YAML frontmatter metadata, detailed instructions, and scoped tool permissions.
- **`context: fork`**: A critical YAML frontmatter flag that launches the skill in an ephemeral sub-agent context, returning only its synthesized final output to keep the main chat clean.
- **`allowed-tools`**: A frontmatter permission whitelist designating which specific tools the skill can invoke without prompting the user for approval.
- **`argument-hint`**: A frontmatter string displaying placeholder text to guide the developer on what input parameters the slash command or skill expects.

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    Dev["Developer runs a skill<br>with context: fork"] --> Fork["Forked context<br>reads many files, runs searches"]
    Fork --> Summary["Short summary"]
    Summary --> Main["Main conversation<br>stays small and focused"]
    Fork -.->|"tools limited by"| Tools["allowed-tools<br>Read, Grep, Glob"]
```

---

## 🧪 Worked Example

### ❌ Invalid Example (Anti-Pattern: Running Noisy Exploration Skills in Main Session)
```yaml
# BROKEN: Custom skill defined without context: fork and unrestricted tools
---
name: scan-secrets
description: Scans 200 project files for potential hardcoded secrets
# Anti-pattern 1: Omitting 'context: fork' causes all 200 file contents to dump into main chat!
# Anti-pattern 2: Omitting 'allowed-tools' allows read-only skill to invoke Bash and Edit
---
Scan every source file in the repository for API keys.
```
What happens in production:
1. Context pollution: 200 file reads consume 80,000 tokens of the developer's main conversational memory.
2. Attention dilution: Subsequent coding turns suffer degraded performance and forget prior user instructions.
3. No safety restriction: The skill has permission to execute arbitrary shell commands.

### ✅ Valid Example (Production Pattern: Scoped Skills with `context: fork` & `allowed-tools`)
```yaml
# CORRECT: Isolated execution via context: fork and least-privilege tool whitelist
---
name: architect-eval
description: Evaluates an agent or tool implementation against CCAR-F certification criteria
context: fork          # Runs in an isolated subagent buffer; returns only concise summary to main chat
allowed-tools:        # Read-only exploration whitelist; blocks Bash, Edit, and Write
  - Read
  - Grep
  - Glob
argument-hint: "<domain_or_filepath>"
---
Evaluate the specified task statement implementation against official blueprint rules.
Emit a markdown summary table of findings. Do not output raw file text.
```

Directory layout:
```text
my-repo/
  .claude/
    commands/review.md              <- project-scoped: everyone gets /review
    skills/architect-eval/SKILL.md  <- project skill (context: fork, allowed-tools)
~/.claude/
  commands/my-notes.md              <- user-scoped: personal shortcuts
  skills/architect-eval-mine/SKILL.md <- personal variant (distinct name avoids collisions)
```

When you run it: Claude forks an isolated context, uses only `Read`, `Grep`, and `Glob`, and returns a short evaluation. The main session receives only the final table, preserving precious context tokens.

The `main.py` here parses these real files (`load_skills_from_dir`) and classifies commands as project-scoped or user-scoped (`classify_command_path`).

---

## Exam Traps and Correct Patterns

### Trap 1: Team command in the home folder

| Location | Scope |
|---|---|
| `.claude/commands/review.md` (in repo) | Everyone who clones the repo |
| `~/.claude/commands/review.md` | Only you |

**Exam scenario**: "Create a `/review` command available to every developer when they clone or pull." The answer is the project directory. A home-folder command works for you and silently does not exist for others.

### Trap 2: Noisy exploration run inline

```text
ANTI-PATTERN: /analyze-codebase runs in the main chat. 80 file reads fill the context.
PATTERN: a skill with `context: fork` runs in an isolated context and returns a short summary.
```

```markdown
---
name: architect-eval
description: Evaluates an agent implementation against the exam criteria
context: fork
allowed-tools: Read, Grep, Glob
---
```

`allowed-tools` keeps a read-only audit skill to read tools so it cannot edit files.

### Trap 3: Editing a shared skill for a personal tweak

Editing `.claude/skills/review/SKILL.md` changes it for the whole team on the next pull. For a personal variant, create `~/.claude/skills/my-review/` with a **different name**.

### Trap 4: Skill vs CLAUDE.md

| Content | Where | Why |
|---|---|---|
| "Always use type hints", "tests live in `tests/`" | `CLAUDE.md` | Must apply to every task, loaded always |
| 12-step release procedure used monthly | Skill | Loaded only when invoked. Does not cost context every session |

An "always" rule in a skill is a trap: the skill might never be invoked. A rare procedure in `CLAUDE.md` is a trap too: it wastes context every session.

---

## Exam-Style Practice Questions

**Q1 (Scenario 2: Code Generation).** Your team wants every developer to have the same `/review` command. Where should it be created?

- A) `~/.claude/commands/review.md` on each developer's machine.
- B) `.claude/commands/review.md` in the repository.
- C) A paragraph inside `~/.claude/CLAUDE.md`.
- D) `.claude/skills/review/` with `context: fork` removed.

**Q2 (Scenario 2).** A codebase-analysis skill reads dozens of files. After running it, the main conversation is full of file contents and Claude loses earlier instructions. What is the best change?

- A) Add `argument-hint` to the frontmatter.
- B) Move the skill steps into the root `CLAUDE.md`.
- C) Raise the response length in the prompt.
- D) Add `context: fork` to the skill frontmatter.

**Q3 (Scenario 5: CI flavour).** A developer wants a stricter personal version of the team's `deploy-check` skill without affecting teammates. What should they do?

- A) Edit `.claude/skills/deploy-check/SKILL.md` and avoid committing it.
- B) Copy it to `~/.claude/skills/` under a different name.
- C) Create `~/.claude/skills/deploy-check/` with the same name and hope it wins.
- D) Put the stricter steps in the project `CLAUDE.md`.

### Answers

**Q1: B.**
- A fails: each machine would need its own copy; nothing is shared.
- C fails: a user-level `CLAUDE.md` is personal, and a paragraph is not a command.
- D fails: that is a skill, not a project-scoped command, and the fork setting is irrelevant to sharing.

**Q2: D.**
- A fails: `argument-hint` only describes the argument.
- B fails: `CLAUDE.md` loads every session and would make context worse.
- C fails: response length does not stop tool output filling the chat.

**Q3: B.**
- A fails: it edits the shared file and risks an accidental commit.
- C fails: reusing the name is ambiguous and not the recommended pattern; use a different name.
- D fails: that changes the rules for the whole team.

---

## ✅ Self-Check Checklist

- [ ] I can say where project-scoped and user-scoped commands live.
- [ ] I can write a `SKILL.md` frontmatter with `context`, `allowed-tools`, `argument-hint`.
- [ ] I can explain what `context: fork` protects.
- [ ] I know personal skill variants need a different name.
- [ ] I can say when to use a skill and when to use `CLAUDE.md`.

**Memory hook**: *Team shortcut in the repo, personal shortcut at home, noisy work in a fork.*

---

## 🛠️ Hands-on Workbook Guide

Open [`ts_3_2_slash_commands_and_skills.ipynb`](ts_3_2_slash_commands_and_skills.ipynb) (offline). It uses [main.py](main.py):

1. Setup and imports.
2. Classify this repo's commands and parse its real `SKILL.md` frontmatter.
3. Expand a command template and simulate fork vs inline.
4. Assertions on parsed `context`, `allowed-tools`, `argument-hint`.

---

## 🧭 Navigation & Study Links
- ⬅️ **Previous Topic**: [TS 3.1: Claude Code CLI Configuration & Architecture](../ts_3_1_claude_code_workflows/README.md)
- 📋 **Domain Overview**: [Domain 3: Claude Code & Developer Workflows](../README.md)
- ➡️ **Next Topic**: [TS 3.3: Path-Specific Rules & Directory Scoping](../ts_3_3_path_specific_rules/README.md)
- 🎯 **Scenario Practice**: [Master Scenario Practice](../../scenarios/MASTER_SCENARIO_PRACTICE.md)
