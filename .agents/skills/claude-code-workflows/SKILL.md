---
name: claude-code-workflows
description: Guide to Claude Code configuration hierarchy (CLAUDE.md), path-scoped rules, skills with context fork, plan mode, CI/CD, and Mermaid standards.
---

# Claude Code Workflows & Configuration (Domain 3)

## 1. CLAUDE.md Configuration Hierarchy (TS 3.1)
1. **User-level**: `~/.claude/CLAUDE.md` (Personal preferences, NOT committed).
2. **Project-level**: `.claude/CLAUDE.md` or root `CLAUDE.md` (Shared standards committed to git).
3. **Directory-level**: Subdirectory `CLAUDE.md` files (Local to package or folder).
4. **Size Rule**: Keep `CLAUDE.md` **under 200 lines**. Only universal facts belong here; tier procedural workflows into skills.
5. **Modular Rules**: Use `.claude/rules/` with `paths: [...]` or `@path/to/standards.md` imports.
6. **Inspection**: Use `/memory` command to verify which context files are loaded.

## 2. Skills vs Slash Commands (TS 3.2)
- **Commands**: Project commands in `.claude/commands/`, user commands in `~/.claude/commands/`.
- **Skills**: In `.claude/skills/<name>/SKILL.md`.
- **Frontmatter options**:
  - `context: fork` — runs in isolated subagent context, preventing verbose exploration or testing from polluting the main conversation.
  - `allowed-tools` — restrict tool capabilities (e.g. read-only vs file modification).
  - `argument-hint` — prompts for required parameters if omitted.

## 3. Path-Specific Rules (TS 3.3)
Place rule files in `.claude/rules/` with YAML frontmatter:
```markdown
---
paths:
  - "src/api/**/*"
  - "**/*.test.ts"
---
```
Rules load only when editing matching files, saving context tokens and eliminating irrelevant rules.

## 4. Plan Mode vs Direct Execution (TS 3.4)
- **Plan Mode**: Complex, multi-file changes (>= 3 files), microservices migrations, architectural refactoring, multiple valid approaches. Safe exploration via Explore subagent before writing code.
- **Direct Execution**: Isolated, well-scoped fixes (e.g., single-file bug fix with clear stack trace, date validation check).

## 5. Iterative Refinement (TS 3.5)
- Provide 2–3 concrete input/output examples when natural language descriptions are ambiguous.
- Test-driven iteration: write failing tests first, then iterate using test output.
- Interview pattern: prompt Claude to ask clarifying questions with concrete choices before implementation.

## 6. CI/CD Integration (TS 3.6)
- **Non-interactive**: Run with `-p` (or `--print`) flag so the process exits on completion without hanging for interactive input.
- **Structured output**: Use `--output-format json` and `--json-schema` to produce machine-parseable findings.
- **Independent review instance**: Never use the same Claude session to review its own generated code.

## 7. October 2026 Mermaid Architecture Standards
- Wrap node labels with punctuation, colons, or spaces in double quotes: `Node["Clean Label"]`.
- Explicit flow direction (`flowchart TD` or `flowchart LR`).
- No raw HTML tags like `<b>` or `</b>` inside node labels. Use `<br>` inside double quotes for line breaks.
- No fragile `%%{init: ...}%%` directives.
