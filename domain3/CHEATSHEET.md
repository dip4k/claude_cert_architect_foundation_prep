# Domain 3 Cheatsheet: Claude Code Configuration & Workflows (20%)

One-page revision. **Not a copy of [KEY_CONCEPTS.md](KEY_CONCEPTS.md)**: that file explains scopes, commands, skills, rules and CI. This sheet adds question wording to answer, look-alike pairs, exact flags, and elimination filters. Worked traps are in each study guide (links at the bottom).

---

## 1. Question wording → answer

| If the question says... | Choose | Reject | TS |
|---|---|---|---|
| New teammate does not get the team's rules | Move them to the project `CLAUDE.md` (committed) | Keep in `~/.claude/CLAUDE.md` | 3.1 |
| `CLAUDE.md` is huge | Short file plus `@import` and `.claude/rules/` topic files | One giant file | 3.1 |
| Claude ignores an instruction | `/memory` to see what loaded | Retype it each prompt | 3.1 |
| Shortcut for everyone who clones the repo | `.claude/commands/` | `~/.claude/commands/` | 3.2 |
| Workflow with verbose output | Skill with `context: fork` | Run inline | 3.2 |
| Personal tweak of a team skill | Own copy in `~/.claude/skills/`, different name | Edit the shared file | 3.2 |
| Rule must always apply | `CLAUDE.md` | A skill | 3.2 |
| Convention tied to a file pattern across folders | Path-scoped rule (`paths:` glob) | `CLAUDE.md` in every folder | 3.3 |
| Monolith to microservices | Plan mode | Direct execution | 3.4 |
| Single-file fix with a stack trace | Direct execution | Plan mode "to be safe" | 3.4 |
| Wide exploration would flood the chat | Explore subagent | Read everything in the main chat | 3.4 |
| Output interpreted inconsistently | 2 to 3 input/output examples | "Be more careful" | 3.5 |
| Requirements are open | Interview pattern | Guess and rewrite | 3.5 |
| Issues interact / are independent | One message / sequential messages | The reverse | 3.5 |
| CI job hangs | `-p` | `CLAUDE_HEADLESS`, `--batch` (do not exist) | 3.6 |
| CI findings must be machine-readable | `--output-format json` plus `--json-schema` | Regex over prose | 3.6 |
| Review of code Claude just wrote | Independent instance | Same session | 3.6 |
| Re-review after a new push | Prior findings plus "only new or unaddressed" | Re-run with no history | 3.6 |
| Pre-merge check vs overnight audit | Synchronous / Message Batches API | The reverse | 3.6 |

---

## 2. Look-alike pairs

| Pair | Difference |
|---|---|
| `CLAUDE.md` vs rule vs skill | Always loaded / loaded by file path / invoked on demand |
| User vs project vs directory scope | Personal, not shared / shared / shared, one subtree |
| Command vs skill | Single prompt shortcut / folder with `SKILL.md`, supports `context: fork` and `allowed-tools` |
| Plan mode vs direct execution | Large, ambiguous, architectural / small and well defined |
| `--allowedTools` vs `--tools` vs `--disallowedTools` | Run without prompting / restrict which built-ins exist / deny rules |
| `--append-system-prompt` vs `--system-prompt` | Adds to the default prompt (keeps tool guidance and safety) / replaces all of it |
| `--resume` vs `--continue` vs `--fork-session` | By id or name / most recent in this directory / new session id when resuming |
| Interactive `claude` vs `claude -p` | Waits for a human / runs once and exits |
| Same-session review vs independent review | Biased by its own reasoning / fresh context |

---

## 3. Exact flags and names (checked against the Claude Code CLI reference)

- `-p` / `--print` runs non-interactively. `--output-format` takes `text`, `json`, `stream-json`. `--json-schema` takes an inline JSON schema string and works in print mode only.
- `--max-turns` and `--max-budget-usd` are print-mode safety caps. Hitting `--max-turns` exits with an error.
- `--resume` / `-r` takes a session id or name. `-n` names a session. `--fork-session` creates a new id when resuming.
- `--permission-mode plan` starts in plan mode. Other values include `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`.
- `--bare` skips auto-discovery of hooks, skills, commands, subagents, MCP servers, memory and `CLAUDE.md`. A CI job that needs the repo's `CLAUDE.md` standards must not use it.
- `--no-session-persistence` (print mode) means the session is not saved and cannot be resumed.
- `claude setup-token` creates a long-lived token for CI.
- Skill frontmatter: `name`, `description`, `context: fork`, `allowed-tools`, `argument-hint`. Rule frontmatter: `paths:` list of globs.
- `allowed-tools` pre-approves tools. For a hard restriction at the CLI use `--tools`. The exam answer for a read-only audit is still to limit tools in the skill frontmatter.
- Imports in `CLAUDE.md`: `@path/to/file`. Files from different scopes are combined, not overridden.
- Glob reminder: `*.md` matches the root only. `**/*.md` matches everywhere.

---

## 4. Elimination filters (reject on sight)

1. Any option that stores team standards in a home-directory file.
2. Any option that uses a skill for something that must always apply, or `CLAUDE.md` for a rare procedure.
3. Any option that copies one convention into many folders.
4. Any option with an invented flag or variable (`CLAUDE_HEADLESS`, `--batch`).
5. Any option where the author reviews its own work.
6. Any option that batches a blocking check.

---

## Where the detail is

[3.1](ts_3_1_claude_code_workflows/README.md) · [3.2](ts_3_2_slash_commands_and_skills/README.md) · [3.3](ts_3_3_path_specific_rules/README.md) · [3.4](ts_3_4_plan_mode_and_refinement/README.md) · [3.5](ts_3_5_iterative_refinement_interview/README.md) · [3.6](ts_3_6_cicd_pipeline_automation/README.md)
