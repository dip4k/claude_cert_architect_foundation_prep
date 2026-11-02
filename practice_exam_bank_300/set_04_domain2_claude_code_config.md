# CCAR-F Exam Practice Bank: Set 4
## Domain 2: Claude Code Configuration & Workflows (Part 1: Configuration Hierarchy & CLAUDE.md Scoping)
### Questions 96 – 125

---

### Q96. Claude Code Configuration Precedence Hierarchy
An engineer has a personal preference for tabs over spaces configured in `~/.claude/config.json`. The repository they are working on has `.claude/config.json` committed to Git specifying spaces. When running Claude Code inside this repository, which setting takes precedence?

**A)** The user-level setting (`~/.claude/`) overrides the repository setting.
**B)** The project-level setting (`.claude/`) overrides the user-level setting.
**C)** Claude Code randomly alternates between tabs and spaces.
**D)** The command fails with a configuration collision error.

**Correct Answer:** B

**Explanation:**
Claude Code resolves configurations through a strict scoping hierarchy where more specific scopes take precedence over broader ones:
1. Enterprise / Managed Settings (organizational baseline)
2. User-level (`~/.claude/`) (developer personal defaults)
3. Project-level (`.claude/`) (team/repository shared standards)
4. CLI / Session flags (immediate runtime invocation overrides)
Project-level configurations committed to version control explicitly override personal user-level defaults to ensure team-wide consistency.

**Why other options are incorrect:**
- **A)** Personal settings cannot override team-level repository standards.
- **C)** Configuration resolution is strictly deterministic.
- **D)** Precedence rules exist specifically to prevent collision errors.

---

### Q97. Enterprise Managed Configuration Overrides
An enterprise security team mandates that all developer machines must block raw bash execution in Claude Code. A developer attempts to add `"allowedTools": ["Bash"]` inside their personal `~/.claude/config.json`. What happens?

**A)** The developer's personal config overrides the enterprise policy.
**B)** The Enterprise / Managed configuration establishes an immutable security floor; personal and project configurations cannot grant permissions that are explicitly restricted by managed enterprise policies.
**C)** Claude Code prompts the user to choose which policy they prefer.
**D)** The user's operating system crashes.

**Correct Answer:** B

**Explanation:**
Enterprise / Managed configuration sits at the base of the governance hierarchy. In enterprise deployments, security policies (such as tool denylists, required audit logging endpoints, or disabled capabilities) are non-overridable. While project and user configs can customize styles or add restrictions, they cannot override or relax hard security constraints imposed by managed enterprise configurations.

**Why other options are incorrect:**
- **A)** Allowing individual developers to bypass enterprise security defeats organizational compliance.
- **C)** Security enforcement is deterministic, not user-prompted.
- **D)** OS crashes do not occur from config precedence checks.

---

### Q98. Keeping CLAUDE.md Concise (<200 Lines)
Why does Anthropic recommend keeping the root `CLAUDE.md` file concise (ideally under 200 lines) rather than dumping an entire 2,000-line wiki into it?

**A)** GitHub rejects files named `CLAUDE.md` if they exceed 5KB.
**B)** Context Window Saturation & Attention Dilution: `CLAUDE.md` is loaded into the prompt on EVERY single conversation turn. A bloated `CLAUDE.md` consumes baseline tokens, slows down time-to-first-token latency, and dilutes the model's attention away from the user's specific task.
**C)** Claude Code can only read the first 100 characters of any file.
**D)** Longer files cause syntax errors in Python.

**Correct Answer:** B

**Explanation:**
`CLAUDE.md` acts as persistent, global system context that is ingested on every interaction. Stuffing entire architecture documentation, coding guides, and API schemas into `CLAUDE.md` results in:
1. High token costs on every turn.
2. Latency degradation.
3. Attention dilution: when everything is marked as essential, the model prioritizes nothing effectively.
Detailed, task-specific documentation belongs in on-demand **Skills** or path-scoped rules, not the global `CLAUDE.md`.

**Why other options are incorrect:**
- **A)** GitHub has no such file-naming size restriction.
- **C)** Claude Code reads large files without issue; the concern is prompt efficiency.
- **D)** Markdown files do not cause Python syntax errors.

**Anti-Pattern Alert:**
*Monolithic CLAUDE.md*: Using `CLAUDE.md` as an exhaustive dumping ground for all company documentation, wasting tokens and diluting attention across all sessions.

---

### Q99. Modular Rule Organization with `.claude/rules/`
A large monorepo contains a frontend React app in `/frontend` and a backend Go service in `/backend`. What is the best practice for configuring coding standards without bloating the root `CLAUDE.md`?

**A)** Create a 5,000-line `CLAUDE.md` at the repository root covering both languages.
**B)** Use path-scoped rule files in `.claude/rules/` (e.g. `.claude/rules/frontend.md` and `.claude/rules/backend.md`) with path matching filters, so rules are only loaded when Claude operates on files in those specific directories.
**C)** Delete Go files when working on React, and delete React files when working on Go.
**D)** Force developers to type out all coding conventions in every prompt.

**Correct Answer:** B

**Explanation:**
Claude Code supports modular, path-scoped rules via `.claude/rules/`. By defining directory-specific rule files targeted to glob patterns (e.g., `paths: ["frontend/**"]` or `paths: ["backend/**"]`), instructions are conditionally activated only when Claude touches relevant files. This keeps the global baseline prompt lean while delivering precise guidance where needed.

**Why other options are incorrect:**
- **A)** Creates context bloat and mixes irrelevant language rules.
- **C)** Deleting codebase files is destructive and absurd.
- **D)** Requiring manual prompt typing wastes developer time and is error-prone.

---

### Q100. Root vs. Subdirectory CLAUDE.md Files
In a nested project structure:
```
/my-repo/
  CLAUDE.md (Root)
  /services/billing/
    CLAUDE.md (Subdirectory)
```
When a developer launches Claude Code while working inside `/my-repo/services/billing/`, how are the `CLAUDE.md` files processed?

**A)** Only the subdirectory `CLAUDE.md` is read; the root is ignored.
**B)** The root `CLAUDE.md` is loaded first for repo-wide baseline standards, and the subdirectory `CLAUDE.md` is loaded hierarchically to apply localized overrides and service-specific instructions.
**C)** Claude Code throws a fatal error because multiple `CLAUDE.md` files are illegal.
**D)** The root `CLAUDE.md` deletes the subdirectory file.

**Correct Answer:** B

**Explanation:**
Claude Code evaluates `CLAUDE.md` files hierarchically. The root `CLAUDE.md` establishes repository-wide baselines (e.g., global git conventions, PR guidelines), while nested `CLAUDE.md` files in subdirectories provide localized instructions (e.g., billing service build commands, local test runners) that inherit from and augment the root instructions.

**Why other options are incorrect:**
- **A)** Discarding root rules would lose global standards.
- **C)** Multiple hierarchical `CLAUDE.md` files are a core supported feature.
- **D)** Claude Code does not delete user configuration files.

---

### Q101. What Belongs in CLAUDE.md vs. Skills vs. Rules
An engineering team is reorganizing its Claude Code configuration. Match the content type to its proper storage location:
1. Standard repository build commands (`npm run build`, `pytest`)
2. Path-specific TypeScript strictness rules for `/src/core`
3. A complex multi-step database migration checklist used once a month

**A)** 1: Rules, 2: Skills, 3: CLAUDE.md
**B)** 1: CLAUDE.md, 2: Path-scoped Rule (`.claude/rules/`), 3: Skill (`.claude/skills/`)
**C)** 1: Skill, 2: CLAUDE.md, 3: Rules
**D)** All three must be stored in `~/.bashrc`

**Correct Answer:** B

**Explanation:**
- **`CLAUDE.md`**: For everyday, global repository commands that Claude needs on almost every turn (build commands, test invocations, lint scripts, primary architectural pattern).
- **Path-Scoped Rules (`.claude/rules/`)**: For localized file/directory constraints (TypeScript conventions, frontend styling guidelines) that apply whenever specific file paths are touched.
- **Skills (`.claude/skills/`)**: For specialized, episodic, multi-step workflows (database migrations, security releases, incident playbooks) that should only load into memory on-demand when explicitly triggered.

**Why other options are incorrect:**
- **A, C)** Misallocates on-demand tasks into permanent memory and routine commands into episodic skills.
- **D)** `~/.bashrc` is a shell script, not a Claude Code AI configuration file.

---

### Q102. Auto-Discovery of Build and Test Commands
A developer opens a new Rust project with Claude Code. The project has a `Cargo.toml`. Why should the root `CLAUDE.md` explicitly list:
`Build command: cargo build`
`Test command: cargo test -- --nocapture`?

**A)** Claude Code cannot execute commands unless they are in `CLAUDE.md`.
**B)** Explicitly defining canonical commands eliminates guessing and experimentation: it prevents Claude from trying multiple incorrect command variants (`cargo check`, `cargo run test`), saving tokens, preventing failed tool runs, and accelerating execution.
**C)** Cargo commands are forbidden without written permission.
**D)** Rust code requires special encryption flags.

**Correct Answer:** B

**Explanation:**
While Claude Code can often infer standard tools from project manifests, ambiguous repositories (e.g., workspaces, monorepos, custom flags like `--nocapture` or specific virtualenvs) can cause Claude to experiment with different commands until one succeeds. Documenting the exact, verified commands in `CLAUDE.md` ensures first-turn accuracy and avoids wasted tool execution turns.

**Why other options are incorrect:**
- **A)** Claude Code can execute any allowed terminal command.
- **C, D)** Cargo commands are standard and do not require encryption.

---

### Q103. Path-Scoped Rules Syntax and Metadata
In `.claude/rules/python-standards.md`, which YAML frontmatter format correctly scopes the rule to all Python files in the repository?

**A)**
```yaml
---
paths:
  - "**/*.py"
---
```
**B)**
```yaml
---
model: python
language: py
---
```
**C)**
```yaml
---
include: "all"
---
```
**D)**
```yaml
---
trigger: "when python is mentioned in chat"
---
```

**Correct Answer:** A

**Explanation:**
Path-scoped rules use standard glob pattern matching in their YAML frontmatter under the `paths` key. The pattern `"**/*.py"` matches any file ending in `.py` anywhere in the repository hierarchy, ensuring that the enclosed standards are activated whenever Claude reads or edits Python files.

**Why other options are incorrect:**
- **B, C, D)** These do not follow the defined Claude Code rule schema for file-path glob triggering.

---

### Q104. Managing Secrets in CLAUDE.md
A developer places the following line in their repository's `CLAUDE.md`:
`AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE`
`DATABASE_PASSWORD=SuperSecretPass123`
Why is this an extreme security violation?

**A)** Claude Code refuses to run if it detects the word "Password".
**B)** `CLAUDE.md` is committed to version control and ingested directly into model context windows, exposing sensitive credentials in Git history and transmitting raw secrets across API boundaries.
**C)** Passwords in `CLAUDE.md` must be hashed using MD5.
**D)** AWS keys can only be stored in HTML files.

**Correct Answer:** B

**Explanation:**
`CLAUDE.md` files are version-controlled assets. Committing secrets to `CLAUDE.md` leaks credentials into Git history, where anyone with repository read access can view them. Furthermore, every session transmits `CLAUDE.md` contents into LLM API prompts, exposing credentials across network boundaries. Secrets must ALWAYS reside in environment variables (`.env`), secrets managers, or credential vaults, never in plain markdown instruction files.

**Why other options are incorrect:**
- **A)** Claude Code does not arbitrarily refuse words; security relies on human and pipeline discipline.
- **C)** MD5 is broken and secrets should never be in markdown at all.
- **D)** AWS keys belong in secure vaults, not HTML files.

**Anti-Pattern Alert:**
*Hardcoded Secrets in Project Prompts*: Storing API tokens, database credentials, or private keys inside `CLAUDE.md` or rule files.

---

### Q105. Custom Slash Commands in Claude Code
How can a team configure a project-specific shortcut command (e.g. `/deploy-staging`) for all developers in a repository?

**A)** By creating a custom script or markdown file inside `.claude/commands/` or configuring a custom Skill in `.claude/skills/deploy-staging/SKILL.md`.
**B)** By editing the Claude Code binary using a hex editor.
**C)** By emailing Anthropic customer support to add the command to the cloud server.
**D)** By renaming the Git repository to `/deploy-staging`.

**Correct Answer:** A

**Explanation:**
Custom slash commands and developer workflows are defined within project-scoped configurations: either via custom command definitions in `.claude/commands/` or by creating a modular Skill in `.claude/skills/<skill-name>/SKILL.md`. When developers type the corresponding slash command (or express intent matching the skill description), Claude Code loads and executes the workflow.

**Why other options are incorrect:**
- **B)** Modifying binaries is fragile, unsupported, and fails on updates.
- **C)** Custom project commands are managed locally, not by Anthropic support.
- **D)** Git repository names do not define CLI slash commands.

---

### Q106. Preventing Instruction Conflicts Across Hierarchies
If the root `CLAUDE.md` says: `"Always format code using Prettier with single quotes"`, but `.claude/rules/legacy.md` (scoped to `/legacy/**`) says: `"Always format legacy code using double quotes"`, how does Claude resolve this when editing `/legacy/app.js`?

**A)** Claude crashes due to contradictory instructions.
**B)** Path-scoped rules are more specific than the global root `CLAUDE.md`; therefore, the localized rule applies and Claude uses double quotes for files in `/legacy/`.
**C)** Claude uses single quotes on odd lines and double quotes on even lines.
**D)** The root `CLAUDE.md` always overrides all subdirectory rules.

**Correct Answer:** B

**Explanation:**
In the configuration hierarchy, path-scoped rules are specifically designed to handle localized exceptions to general repository rules. Because `/legacy/app.js` matches the path filter of the localized rule, its explicit instruction regarding double quotes takes precedence over the global root guideline.

**Why other options are incorrect:**
- **A)** Claude models are trained to reconcile localized specific constraints over broad general baselines.
- **C)** Line-alternating formatting is absurd and non-standard.
- **D)** If root rules always overrode specific path rules, localized exceptions would be impossible.

---

### Q107. The Cost of Overly Verbose Project Prompts
A team's `CLAUDE.md` contains 15,000 tokens of architecture explanations, historical bug post-mortems, and employee biographies. In an active development team of 10 developers making 100 queries each per day, what is the operational impact of this configuration?

**A)** Zero impact, because `CLAUDE.md` is only billed once per year.
**B)** High Latency and Cost: 15,000 tokens are injected on every turn across all 1,000 daily queries (15 million extra input tokens daily), creating substantial financial waste and degrading response speed.
**C)** The developers receive free API credits for being descriptive.
**D)** Claude Code runs locally on the CPU without using API tokens.

**Correct Answer:** B

**Explanation:**
Every single token in `CLAUDE.md` is processed as input on every user interaction. 15,000 tokens injected into 1,000 queries per day represents 15 million input tokens daily purely in overhead. While prompt caching reduces the financial blow of repeated identical prefixes, it does not eliminate it (cache reads still cost tokens), and TTFT latency is measurably increased. Keeping `CLAUDE.md` lean (<200 lines / ~1,000 tokens) is essential.

**Why other options are incorrect:**
- **A, C)** Token billing occurs continuously per request; there are no annual free exemptions.
- **D)** Claude Code utilizes Anthropic's hosted cloud API for inference.

---

### Q108. Version Control Best Practices for `.claude/`
Which files in the `.claude/` directory should be committed to version control (`git`), and which should be placed in `.gitignore`?

**A)** Commit `.claude/config.json`, `.claude/rules/`, `.claude/skills/`, and `CLAUDE.md`; add `.claude/sessions/`, `.claude/cache/`, and developer-specific local state to `.gitignore`.
**B)** Commit nothing; the entire `.claude/` folder should always be gitignored.
**C)** Commit all session logs, API keys, and temporary files.
**D)** Zip the folder and commit the binary `.zip` file.

**Correct Answer:** A

**Explanation:**
Team configurations (shared build rules, coding standards, modular skills, path rules, and team configs) belong in version control so that the entire team shares identical agent behaviors. Ephemeral local state—such as past conversation transcripts, session caches, local token overrides, and temporary scratchpads—must be added to `.gitignore` to prevent repository bloat and credential leaks.

**Why other options are incorrect:**
- **B)** Gitignoring everything prevents the team from standardizing AI workflows.
- **C)** Committing session logs and keys causes repository bloat and massive security vulnerabilities.
- **D)** Zipping files destroys git diff tracking and version comparison.

---

### Q109. Using `CLAUDE.md` to Enforce Test-Driven Development (TDD)
How can a technical lead configure `CLAUDE.md` to enforce that Claude Code writes unit tests before modifying application logic?

**A)** Add an explicit policy instruction: `"Workflow Rule: When implementing new features or bug fixes, always write the failing unit test first. Run the test to confirm it fails, implement the minimal code required to pass, and run the test suite again to confirm 100% green."`
**B)** Delete the source code directory so Claude has no choice.
**C)** Set the test runner timeout to 1 millisecond.
**D)** Block all git commits at the operating system kernel level.

**Correct Answer:** A

**Explanation:**
`CLAUDE.md` is the primary mechanism for establishing engineering workflow policies. Clear, direct behavioral instructions outlining the required procedural steps (TDD cycle: write failing test → verify failure → write code → verify pass) are followed reliably by Claude Code during interactive development sessions.

**Why other options are incorrect:**
- **B)** Deleting code destroys the application.
- **C)** 1ms timeouts cause tests to fail before executing.
- **D)** Kernel-level blocking is an excessive, irrelevant OS hack.

---

### Q110. The Perils of Vague Instructions in `CLAUDE.md`
A developer writes in `CLAUDE.md`: `"Write clean, fast, beautiful, elegant, bug-free code."`
Why is this instruction considered ineffective in architectural review?

**A)** It is an anti-pattern of non-actionable platitudes: it provides zero concrete architectural guidelines, naming conventions, linting commands, or measurable constraints, wasting prompt tokens on subjective noise.
**B)** Claude only understands German.
**C)** The words "fast" and "clean" are reserved keywords that crash the tokenizer.
**D)** Claude automatically writes buggy code when asked to write bug-free code.

**Correct Answer:** A

**Explanation:**
Telling an AI model to "write clean, elegant code" is conversational filler. Modern LLMs are already trained to generate high-quality code by default. Useful `CLAUDE.md` instructions must be concrete and operational: specifying exact frameworks, state management patterns, error handling conventions, naming rules, and specific CLI commands.

**Why other options are incorrect:**
- **B)** Claude is fluent in dozens of languages.
- **C)** They are standard English tokens, not syntax-crashing keywords.
- **D)** Models do not invert intent out of spite.

**Anti-Pattern Alert:**
*Platitude Prompting*: Filling project configuration files with subjective platitudes ("make it scalable and pretty") rather than concrete technical standards.

---

### Q111. User-Level Global Overrides (`~/.claude/CLAUDE.md`)
What is the primary use case for maintaining a `CLAUDE.md` in the user's home directory (`~/.claude/CLAUDE.md`)?

**A)** To override the enterprise firewall.
**B)** To store personal developer ergonomic preferences, such as custom terminal aliases, preferred editor notification styles, or individual accessibility settings across all repositories on their machine.
**C)** To commit global secrets that all team members can read.
**D)** To replace the Linux kernel.

**Correct Answer:** B

**Explanation:**
`~/.claude/CLAUDE.md` is specific to the individual developer. It applies across every project they work on locally without contaminating shared team repositories. It is the ideal place for personal ergonomics (e.g., "Always display file diffs in unified format", personal shell shortcuts, preferred explanation verbosity).

**Why other options are incorrect:**
- **A, D)** Home directory markdown files cannot alter firewalls or replace OS kernels.
- **C)** Secrets should never be stored in markdown files.

---

### Q112. Structuring Test Invocations in `CLAUDE.md`
A repository has 10,000 end-to-end integration tests that take 45 minutes to run, alongside fast unit tests that run in 3 seconds. How should `CLAUDE.md` instruct Claude Code to run tests during active editing?

**A)** `"Run all 10,000 integration tests after every line of code you edit."`
**B)** `"Default Test Command: npm run test:unit. Only run targeted unit tests corresponding to modified files during iteration. Do NOT run full integration tests (npm run test:e2e) unless explicitly instructed by the user."`
**C)** `"Never run any tests under any circumstances."`
**D)** `"Run tests on another developer's laptop."`

**Correct Answer:** B

**Explanation:**
Autonomous agents will execute whatever test command is configured. If instructed to run a 45-minute suite on every minor change, developer iteration will grind to a halt. Documenting targeted, fast unit test commands as the default iteration loop preserves high development velocity while reserving heavyweight end-to-end suites for final verification.

**Why other options are incorrect:**
- **A)** Running 45-minute tests repeatedly destroys developer productivity.
- **C)** Eliminating testing removes verification guardrails entirely.
- **D)** Remote laptop hijacking is not a supported testing architecture.

---

### Q113. Specifying Code Formatting Tools
Why should `CLAUDE.md` explicitly reference the project's automated formatter (e.g., `black .` or `prettier --write .`) rather than listing 50 separate manual whitespace and indentation rules?

**A)** Let the deterministic tool do deterministic work: offload formatting to automated linters/formatters via CLI execution, saving prompt tokens and guaranteeing exact adherence to team standards.
**B)** Claude cannot generate whitespace.
**C)** Formatters do not work on computers.
**D)** Python requires manual formatting only.

**Correct Answer:** A

**Explanation:**
Attempting to teach an LLM 50 nuanced spacing, brace-placement, and line-wrapping rules via natural language prompt instructions is inefficient and prone to subtle errors. The proper architectural pattern is to instruct Claude to invoke the project's existing deterministic formatting tool (`npm run format` or `black`) after making edits.

**Why other options are incorrect:**
- **B)** Claude outputs whitespace accurately.
- **C)** Automated code formatters are standard software tooling.
- **D)** Python standard tooling includes deterministic formatters like Black and Ruff.

---

### Q114. Temporary Instruction Scoping via CLI Flags
A developer wants Claude Code to run a single session in an extra-cautious mode where every file modification requires a detailed security explanation, without permanently modifying `CLAUDE.md`. How should this be done?

**A)** Edit `CLAUDE.md`, run the task, and remember to revert the file using `git checkout`.
**B)** Pass the instructions directly in the initial user prompt or use session CLI flags (`--append-system-prompt` or runtime flag), leaving the persistent version-controlled `CLAUDE.md` untouched.
**C)** Delete the repository and clone it again.
**D)** Create a new GitHub account.

**Correct Answer:** B

**Explanation:**
One-off, session-specific constraints should not be committed to persistent configuration files. Passing the constraint in the invocation prompt or leveraging CLI session flags provides immediate behavioral adaptation without introducing dirty git states or accidental commits of temporary instructions.

**Why other options are incorrect:**
- **A)** Modifying and reverting files is error-prone; developers frequently forget to revert, polluting Git history.
- **C, D)** Cloning repos or making new accounts is unnecessary overhead.

---

### Q115. Architectural Blueprint Referencing in `CLAUDE.md`
A complex backend follows Clean Architecture (Domain → Use Cases → Repositories → Controllers). How should `CLAUDE.md` guide Claude to respect this architecture?

**A)** Paste the entire 500-page book on Clean Architecture into `CLAUDE.md`.
**B)** Summarize the layer dependency rule concisely in `CLAUDE.md`: `"Architecture: Clean Architecture. Invariant: Domain models must have zero external dependencies. Controllers may only call Use Cases; never call Repositories directly from Controllers."`
**C)** Tell Claude to do whatever is easiest.
**D)** Forbid Claude from creating new files.

**Correct Answer:** B

**Explanation:**
Concise, high-leverage architectural invariants belong in `CLAUDE.md`. Stating the fundamental dependency rules (Layer A cannot import Layer C) provides Claude with the structural boundaries needed to generate idiomatic, properly architected code without bloating the prompt with hundreds of pages of theory.

**Why other options are incorrect:**
- **A)** Pasting entire books saturates the context window and dilutes attention.
- **C)** "Whatever is easiest" leads to spaghetti architecture.
- **D)** Forbidding file creation prevents standard development work.

---

### Q116. Path Scoping: Excluding Generated Files
A repository generates large GraphQL and OpenAPI client files in `/src/generated/`. Why should `.claude/rules/` or `CLAUDE.md` explicitly instruct Claude Code to avoid manual edits in this directory?

**A)** Generated files will be overwritten on the next build, rendering manual edits futile and corrupting generator state.
**B)** Generated files are legally owned by the compiler.
**C)** Claude Code cannot read generated files.
**D)** Editing generated files breaks internet access.

**Correct Answer:** A

**Explanation:**
Directly editing autogenerated artifacts (Protobuf, GraphQL, OpenAPI codegen, build outputs) is a classic junior developer mistake that agents will also make if unguided. The changes will be wiped out the next time the build pipeline runs. Documenting `"Do NOT edit files in /src/generated/ directly; modify schema.graphql and run npm run codegen instead"` prevents wasted effort.

**Why other options are incorrect:**
- **B)** Legal ownership is irrelevant to compiler output.
- **C)** Claude Code can read generated files without difficulty.
- **D)** File edits do not disrupt network connectivity.

---

### Q117. Environment Variable Handling in `CLAUDE.md`
What is the proper guidance to provide in `CLAUDE.md` regarding local development environment files like `.env`?

**A)** `"Always copy .env.example to .env if .env is missing. Never commit .env to version control. Read config values from process.env rather than hardcoding."`
**B)** `"Commit .env to Git so all team members share the same credentials."`
**C)** `"Delete .env on startup."`
**D)** `"Post .env contents in Slack."`

**Correct Answer:** A

**Explanation:**
Documenting environment bootstrapping conventions (e.g. copying `.env.example`, maintaining `.gitignore` isolation, reading from environment variables) ensures that Claude sets up local environments properly while strictly honoring credential security boundaries.

**Why other options are incorrect:**
- **B, D)** Exposing `.env` in Git or Slack creates severe security leaks.
- **C)** Deleting `.env` destroys local configuration.

---

### Q118. Linting Failure Recovery Instructions
An agent modifies a file and runs the linter, which outputs 3 syntax errors. What instruction in `CLAUDE.md` ensures the agent handles this properly?

**A)** `"If the linter fails, disable the linter and push the code."`
**B)** `"Linting Policy: All edits must pass linting. If the linter reports errors, inspect the error output, fix the underlying code, and re-run the linter until 0 errors are reported before declaring the task complete."`
**C)** `"Delete the file if linting fails."`
**D)** `"Ask the user to fix the linting errors manually."`

**Correct Answer:** B

**Explanation:**
Establishing an explicit quality gate in `CLAUDE.md` ensures that the agent takes ownership of automated code health. Instructing the agent to iterate on linter feedback until achieving a green state prevents broken code from being left in the repository.

**Why other options are incorrect:**
- **A)** Disabling linters degrades codebase quality and bypasses CI checks.
- **C)** Deleting files is destructive.
- **D)** Delegating routine lint fixes back to the user defeats the purpose of developer automation.

---

### Q119. Language and Toolchain Version Pinning
Why should `CLAUDE.md` specify explicit versions (e.g., `"Python 3.12, Node.js 22, Go 1.23"`)?

**A)** To prevent Claude from using deprecated syntax or using features from newer language versions not yet supported by the project's production runtime.
**B)** Compilers refuse to run unless versions are written in markdown.
**C)** Claude cannot write code without knowing the year the language was created.
**D)** Older language versions cost more tokens.

**Correct Answer:** A

**Explanation:**
LLMs are trained on massive corpuses spanning decades of language syntax. Without explicit version pinning, Claude might generate Python 3.8 syntax (missing modern type unions like `int | str`) or conversely generate Python 3.13 features on a project deployed to Python 3.10. Stating the active toolchain version grounds the model in the appropriate syntax subset.

**Why other options are incorrect:**
- **B, C)** Compilers and models do not require creation years to function.
- **D)** Token pricing is completely independent of language versions.

---

### Q120. Defining Branching and Git Commit Conventions
How can `CLAUDE.md` ensure that all Git commits generated by Claude Code adhere to Conventional Commits?

**A)** Install a custom operating system.
**B)** Include a clear convention guideline: `"Git Commit Standards: Follow Conventional Commits format strictly (e.g., feat(auth): add OAuth2 token refresh, fix(db): resolve connection pool leak). Do not push directly to main."`
**C)** Claude Code cannot execute Git commands.
**D)** Commit messages must be written in binary.

**Correct Answer:** B

**Explanation:**
Claude Code natively executes git commands. By defining clear commit message standards in `CLAUDE.md`, commits generated by the tool will seamlessly integrate into automated changelog generators, semantic release pipelines, and team PR review conventions.

**Why other options are incorrect:**
- **A)** OS changes are irrelevant.
- **C)** Claude Code has full terminal access and routinely executes git commands.
- **D)** Commit messages are standard text strings.

---

### Q121. Directory-Specific Testing Configurations
In a monorepo, running `pytest` from the root fails because tests must be run inside their respective package directories (`cd packages/core && poetry run pytest`). Where should this instruction be placed?

**A)** In `.claude/rules/packages.md` or a localized `CLAUDE.md` inside `packages/core/`.
**B)** On a sticky note on the developer's monitor.
**C)** In the user's global `~/.bashrc`.
**D)** In the cloud database schema.

**Correct Answer:** A

**Explanation:**
Package-specific execution requirements belong in localized rule files or subdirectory `CLAUDE.md` files. This ensures that whenever Claude Code operates within `packages/core/`, it executes tests using the correct local virtualenv context rather than failing from the monorepo root.

**Why other options are incorrect:**
- **B)** AI models cannot read physical sticky notes.
- **C)** Global shell files pollute other repositories.
- **D)** Database schemas have no connection to local test runners.

---

### Q122. Preventing Unintended Database Migrations
A developer is working on a feature and doesn't want Claude Code to execute destructive database drop commands against the shared development database. What policy should be in `CLAUDE.md`?

**A)** `"Database Policy: Never run migrations that drop tables or columns without explicit user confirmation. All local migrations must be executed against local Docker containers, never shared dev databases."`
**B)** `"Drop all databases before every test."`
**C)** `"Delete the database password from the server."`
**D)** `"Only use SQLite."`

**Correct Answer:** A

**Explanation:**
Explicitly stating environmental boundaries and destructive action prohibitions in `CLAUDE.md` prevents accidental data loss during autonomous exploration. Clearly distinguishing between local test containers and shared development instances protects team infrastructure.

**Why other options are incorrect:**
- **B)** Dropping databases causes catastrophic data loss.
- **C)** Deleting passwords breaks database functionality.
- **D)** Arbitrarily restricting to SQLite prevents working with production databases.

---

### Q123. The Role of `CLAUDE.md` in Onboarding New Developers
Beyond guiding Claude Code, what secondary organizational benefit does a well-crafted `CLAUDE.md` provide to engineering teams?

**A)** It replaces the CEO.
**B)** Human Developer Onboarding: Because `CLAUDE.md` contains concise, verified commands for building, testing, linting, and architectural standards, new human engineers can read it to immediately understand how to develop in the repository.
**C)** It automatically pays cloud hosting bills.
**D)** It eliminates the need for Git.

**Correct Answer:** B

**Explanation:**
A concise, well-maintained `CLAUDE.md` serves as single-source-of-truth documentation for both AI agents and human engineers. New hires can inspect `CLAUDE.md` to instantly discover working build commands, test patterns, and code conventions, dramatically accelerating developer onboarding.

**Why other options are incorrect:**
- **A, C, D)** Markdown documentation files do not manage executive leadership, process credit cards, or replace version control.

---

### Q124. Auditing `CLAUDE.md` for Outdated Instructions
A project migrated from Webpack to Vite six months ago, but `CLAUDE.md` still lists `npm run webpack:build`. What failure occurs during Claude Code sessions?

**A)** Claude Code attempts to run the non-existent Webpack script, encounters errors, and wastes turns debugging a legacy toolchain until it discovers the Vite config.
**B)** Vite automatically uninstalls itself.
**C)** The repository is deleted.
**D)** Claude Code converts all files to CoffeeScript.

**Correct Answer:** A

**Explanation:**
Stale documentation in `CLAUDE.md` misleads the agent. When instructions contradict the actual repository state (referencing deleted scripts or removed package managers), the agent trusts `CLAUDE.md` first, executes the invalid command, fails, and wastes token budget recovering. Regular audits of `CLAUDE.md` are critical.

**Why other options are incorrect:**
- **B, C, D)** Stale markdown instructions cause execution failures and wasted turns, not spontaneous file uninstallation or language mutation.

---

### Q125. Scoping Summary: Order of Evaluation
To summarize Domain 2 configuration precedence, in what exact order does Claude Code resolve conflicting configuration values (from lowest precedence to highest precedence)?

**A)** Session Flags → Project Config → User Config → Enterprise Managed
**B)** Enterprise Managed (baseline floor) → User-level (`~/.claude/`) → Project-level (`.claude/`) → CLI / Session Flags (highest immediate override)
**C)** Random order on each turn
**D)** Alphabetical order by file path

**Correct Answer:** B

**Explanation:**
Configuration resolution starts with the Enterprise floor (which sets immutable boundaries), layered by User personal preferences (`~/.claude/`), overridden by Project-specific repository standards (`.claude/`), and finally overridden by explicit CLI / Session flags passed during the immediate runtime command.

**Why other options are incorrect:**
- **A)** Inverts the precedence order.
- **C, D)** Configuration resolution is strictly hierarchical and deterministic.

