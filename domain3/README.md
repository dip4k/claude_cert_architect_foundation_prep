# Domain 3: Claude Code Configuration & Workflows (20% of Exam)

Domain 3 represents 20% of the **Claude Certified Architect – Foundations (CCAR-F)** exam. It tests configuring Claude Code for engineering teams, mastering the CLAUDE.md hierarchy, custom slash commands, agent skills with `context: fork`, path-specific rules, Plan Mode vs Direct Execution, and headless CI/CD pipeline automation.

> 📖 **Deep Dive Master Guide**: For exhaustive technical explanations, architecture diagrams, sequence flows, gotchas, to-remember points, and practical scenario questions & answers, see [KEY_CONCEPTS.md](KEY_CONCEPTS.md).

---

## 📋 Task Statements & Core Architectural Principles

### [TS 3.1: Configure CLAUDE.md Files with Appropriate Hierarchy, Scoping, and Modular Organization](ts_3_1_claude_code_workflows/main.py)
- **4-Tier Hierarchy Order**: User-level (`~/.claude/CLAUDE.md`) -> Project-level (root `CLAUDE.md` or `.claude/CLAUDE.md`) -> Directory-level (`<subdir>/CLAUDE.md`) -> Path-scoped rules (`.claude/rules/*.md`).
- **Scoping Principle**: User-level is personal and uncommitted; project-level is team-shared via git.
- **Modular Rules**: Use `@import ./path/to/rules.md` to avoid monolithic files.
- **Diagnostics**: Run `/memory` in Claude Code to inspect currently loaded configurations and active instructions.
- **Reference Exercise**: [ts_3_1_claude_code_workflows/](ts_3_1_claude_code_workflows/)

### [TS 3.2: Create and Configure Custom Slash Commands and Skills](ts_3_2_slash_commands_and_skills/main.py)
- **Custom Slash Commands**: `.claude/commands/*.md` with parameter substitution (`$1`, `$2`, `$@`).
- **Agent Skills**: `.claude/skills/<name>/SKILL.md` with YAML frontmatter.
- **The `context: fork` Directives**: Executes the skill inside an isolated subagent conversation, preventing verbose exploratory tool trails (20,000+ tokens) from polluting the main session context.
- **Additional Directives**: `allowed-tools` (least privilege whitelist) and `argument-hint`.
- **Reference Exercise**: [ts_3_2_slash_commands_and_skills/](ts_3_2_slash_commands_and_skills/)

### [TS 3.3: Apply Path-Specific Rules for Conditional Convention Loading](ts_3_3_path_specific_rules/main.py)
- **Glob Scoping**: YAML frontmatter `paths: ["**/*.test.ts"]` or `paths: ["src/api/**/*.py"]` in `.claude/rules/*.md`.
- **Advantage Over Directory CLAUDE.md**: Applies conventions across distributed files in arbitrary folders (co-located tests, migrations) without duplicating configuration files.
- **Dynamic Context Loading**: Rules load into context only when matching files are accessed.
- **Reference Exercise**: [ts_3_3_path_specific_rules/](ts_3_3_path_specific_rules/)

### [TS 3.4: Determine When to Use Plan Mode vs Direct Execution](ts_3_4_plan_mode_and_refinement/main.py)
- **Plan Mode (`Shift+Tab` / `/plan`)**: Architectural changes, service decomposition, multi-file refactoring (5+ files), and irreversible schema shifts. Uses read-only **Explore subagent** and human approval gates.
- **Direct Execution**: Localized, well-understood single-file fixes with known stack traces.
- **Reference Exercise**: [ts_3_4_plan_mode_and_refinement/](ts_3_4_plan_mode_and_refinement/)

### [TS 3.5: Apply Iterative Refinement Techniques for Progressive Improvement](ts_3_5_iterative_refinement_interview/main.py)
- **Concrete I/O Examples**: 2–3 concrete input/output pairs resolve ambiguity far better than abstract adjectives.
- **Interview Pattern**: Instruct Claude to ask 3–5 clarifying questions before writing code in complex or ambiguous domains.
- **Coupled vs Decoupled Issues**: Address interacting issues together in a single prompt; address independent issues sequentially.
- **Reference Exercise**: [ts_3_5_iterative_refinement_interview/](ts_3_5_iterative_refinement_interview/)

### [TS 3.6: Integrate Claude Code into CI/CD Pipelines](ts_3_6_cicd_pipeline_automation/main.py)
- **Headless Non-Interactive Mode**: Passing `-p` (or `--print`) is mandatory in CI/CD to prevent runners from hanging indefinitely on `stdin`.
- **Machine-Readable Output**: Combine `--output-format json` with `--json-schema` for deterministic PR gating and automated comments.
- **Mitigating Self-Review Bias**: Never use the generating session to review its own PR; spawn an independent Claude instance with a clean context.
- **Reference Exercise**: [ts_3_6_cicd_pipeline_automation/](ts_3_6_cicd_pipeline_automation/)

---

## 🛠️ Hands-on Exercises in this Domain
- `ts_3_1_claude_code_workflows/`: CLAUDE.md hierarchy resolution, precedence merging, and `@import`.
- `ts_3_2_slash_commands_and_skills/`: Custom slash commands and `context: fork` subagent skills.
- `ts_3_3_path_specific_rules/`: Path-scoped rules with glob matching in `.claude/rules/`.
- `ts_3_4_plan_mode_and_refinement/`: Plan Mode exploration, dependency analysis, and execution gates.
- `ts_3_5_iterative_refinement_interview/`: The Interview Pattern and concrete I/O refinement pairs.
- `ts_3_6_cicd_pipeline_automation/`: Headless CI execution, JSON schema validation, and self-review mitigation.
