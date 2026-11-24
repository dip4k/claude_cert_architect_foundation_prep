# CCAR-F Exam Practice Bank: Set 5
## Domain 2: Claude Code Configuration & Workflows (Part 2: Skills, Subagents, Plan Mode & Headless CI/CD)
### Questions 126 – 155

---

### Q126. Semantic Discovery of Skills
How does Claude Code discover and load modular developer Skills (`SKILL.md` files) without bloating the active conversation context at startup?

**A)** It searches Google to find skills.

**B)** Skills must be manually compiled into binary C++ libraries.

**C)** Semantic Discovery: At startup, Claude Code indexes only the lightweight metadata (name and description) of all available skills; when a user's prompt matches a skill's purpose, Claude prompts or auto-activates the skill and lazy-loads the full markdown instructions on-demand.

**D)** It reads all `SKILL.md` files entirely into memory on every session initialization.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
Skills provide modular, on-demand expertise. To maintain a clean context window, Claude Code does not load the full text of every `SKILL.md` at launch. Instead, it indexes only the names and descriptions into a lightweight discovery registry. When a user prompt matches a skill semantically, Claude recognizes the relevance, loads the complete instructions dynamically, and executes the specialized workflow.

**Why other options are incorrect:**
- **A)** Skills are local project or user files, not web searches.
- **B)** Skills are simple Markdown files with YAML frontmatter, not C++ binaries.
- **D)** Loading all skill bodies at startup would cause severe context bloat and high baseline costs.

</details>

---

### Q127. Skill YAML Frontmatter Configuration
What is the proper YAML frontmatter format for defining a Claude Code skill named `deploy-k8s` that triggers on Kubernetes-related prompts?

**A)**
```yaml
---
command: "kubectl apply -f"
auto_run: true
---
```

**B)**
```yaml
---
name: deploy-k8s
description: Validates manifests, runs dry-runs, and deploys services to Kubernetes clusters. Use when deploying or troubleshooting k8s pods and ingress.
---
```

**C)**
```yaml
---
execute_now: yes
---
```

**D)**
```yaml
---
trigger_words: ["k8s", "deploy"]
---
```

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
A skill's YAML frontmatter requires a unique `name` and a descriptive `description`. The description is crucial: Claude uses this text for semantic intent matching when evaluating user prompts. Clear descriptions detailing *what* the skill does and *when* to use it ensure accurate on-demand activation.

**Why other options are incorrect:**
- **A, C, D)** These do not match the standard Skill schema required by Claude Code.

</details>

---

### Q128. The `context: fork` Parameter in Skills
In an advanced `SKILL.md`, a developer adds `context: fork` to the YAML frontmatter. What architectural behavior does this trigger?

**A)** Isolated Subagent Execution: The skill runs inside a dedicated, isolated subagent context with a clean working memory, preventing verbose intermediate logs from polluting the primary user conversation, and returns only the final summary to the main thread.

**B)** It creates a new Git branch in the repository.

**C)** It duplicates the user's hard drive.

**D)** It forks the operating system kernel into two processes.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
Setting `context: fork` instructs Claude Code to execute the skill within an isolated subagent thread. This is particularly valuable for exploratory or noisy operations (e.g., deep test runs, codebase searches, large refactoring investigations). The subagent performs the heavy lifting in its own ephemeral context and reports back a concise summary to the main conversation, keeping the developer's primary context lean.

**Why other options are incorrect:**
- **B)** It is an execution context fork, not a Git branch.
- **C, D)** It does not duplicate hard drives or fork OS kernels.

</details>

---

### Q129. Overriding Reasoning Effort in Skills
A developer writes a skill for generating quick commit messages (`git-commit`). The skill does not require deep mathematical or architectural reasoning. How can the skill minimize latency and cost?

**A)** Delete the Git repository.

**B)** Hardcode `tokens: 1`.

**C)** Set `temperature: 2.0`.

**D)** Add `effort: low` to the skill configuration, allowing Claude to bypass extensive extended thinking for simple text formatting tasks.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
Skills can specify effort level overrides in their configuration (e.g. `effort: low`, `effort: medium`, `effort: high`). For simple, low-complexity tasks like drafting commit messages or formatting markdown, setting `effort: low` prevents the model from spending thousands of unnecessary tokens in deep extended thinking, optimizing both speed and token expenditure.

**Why other options are incorrect:**
- **A)** Deleting repos destroys project code.
- **B)** Setting tokens to 1 causes immediate truncation.
- **C)** High temperature does not reduce thinking tokens and increases randomness.

</details>

---

### Q130. Subagent Definition in `.claude/agents/`
Where are dedicated subagents defined in a Claude Code project, and what file format do they use?

**A)** Inside `package.json` under an `"agentDefinitions"` array.

**B)** Inside `.claude/settings.local.json` as serialized Python classes.

**C)** Inside `CLAUDE.md` using XML `<subagent>` tags.

**D)** Inside `.claude/agents/<agent-name>.md` using Markdown with YAML frontmatter specifying their system prompt and allowed tools.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
Claude Code subagents are defined as Markdown files inside `.claude/agents/` (project-level) or `~/.claude/agents/` (user-level). The YAML frontmatter specifies metadata such as `name`, `description`, `tools`, and model configuration, while the markdown body provides the specialized system prompt governing the subagent's behavior.

**Why other options are incorrect:**
- **A, B, C)** Subagents are standalone Markdown files in `.claude/agents/` with YAML frontmatter, not entries in `package.json`, `settings.local.json`, or XML blocks in `CLAUDE.md`.

</details>

---

### Q131. Subagent Tool Sandboxing for Code Review
You want to configure a subagent named `code-reviewer` to audit pull requests without the ability to modify any files or execute shell commands. What `tools` configuration should be placed in its frontmatter?

**A)** `tools: ["rm -rf"]`

**B)** `tools: ["all"]`

**C)** `tools: ["read_file", "list_directory", "git_diff"]` (strictly omitting `write_file`, `edit_file`, and `bash`)

**D)** `tools: ["bash"]`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
To create a read-only auditor, you restrict its tool allowlist exclusively to read operations (`read_file`, `list_directory`, `git_diff`). By withholding `write_file`, `edit_file`, and `bash`, the subagent is architecturally sandboxed: it cannot write code, delete assets, or execute arbitrary terminal commands.

**Why other options are incorrect:**
- **A, B, D)** Granting write or shell capabilities violates read-only isolation principles and allows unauthorized modifications.

</details>

---

### Q132. What is Plan Mode in Claude Code?
What is the primary function of Plan Mode (toggled via `Shift + Tab` or `/plan`, or CLI flag `--permission-mode plan`)?

**A)** It disables all AI features permanently.

**B)** Read-Only Analytical Exploration: Claude explores files, maps dependencies, and presents a comprehensive step-by-step implementation blueprint for human review BEFORE modifying any code in the repository.

**C)** It plans the developer's calendar and schedules lunch meetings.

**D)** It compiles the codebase directly to assembly language.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
Plan Mode shifts Claude Code from active execution to an upfront planning state. In Plan Mode, Claude is restricted from making direct file modifications or executing state-altering commands. It reads files, investigates the architecture, and drafts a clear, structured implementation plan. The developer reviews and approves the plan before Claude enters execution mode, preventing misguided refactors.

**Why other options are incorrect:**
- **A)** It is an intentional planning workflow, not a feature disablement.
- **C)** Plan Mode plans software changes, not personal schedules.
- **D)** Plan Mode does not compile assembly code.

</details>

---

### Q133. The Role of `useAutoModeDuringPlan`
What capability does `useAutoModeDuringPlan` provide during Plan Mode exploration?

**A)** It permits safe, read-only diagnostic commands (e.g. running `git status`, searching files, checking build status) to execute autonomously without repeatedly prompting the user for approval during the research phase, while still strictly blocking file writes.

**B)** It allows Claude to automatically push code to production without review.

**C)** It converts all tests to Python.

**D)** It orders pizza for the development team.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
When investigating a complex codebase during Plan Mode, Claude often needs to execute multiple read-only discovery commands (e.g. `grep`, `find`, checking types). If every single command requires human confirmation, the developer suffers from prompt fatigue. `useAutoModeDuringPlan` auto-approves verified read-only operations during planning while keeping edit and write operations locked down.

**Why other options are incorrect:**
- **B)** Plan Mode strictly prohibits unauthorized production pushes.
- **C, D)** Unrelated to language conversion or food ordering.

</details>

---

### Q134. When to Use Plan Mode vs. Direct Execution
Under which scenario is Plan Mode most strongly recommended?

**A)** A complex, multi-service architectural refactoring involving database schema changes and multiple API contract updates across several files.

**B)** Checking the current date in the terminal.

**C)** Renaming a single local variable in a test file.

**D)** Fixing a simple typo in a README file.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
Plan Mode is designed for high-risk, multi-file, or ambiguous engineering tasks. When touching multiple services, modifying database migrations, or altering public API contracts, jumping directly into file edits risks breaking systems midway. Upfront planning ensures all dependencies and potential failure modes are mapped and approved before code changes begin. Simple one-line edits or typos do not require Plan Mode overhead.

**Why other options are incorrect:**
- **B, C, D)** Trivial, low-risk edits are handled faster and more efficiently via direct execution.

</details>

---

### Q135. Headless Mode (`-p` Flag) in Automated Pipelines
How does Claude Code's headless mode (`claude -p "Analyze git diff"`) differ from standard interactive mode?

**A)** Headless mode enables an interactive TUI with auto-approved bash commands.

**B)** Headless mode routes the request through the 24-hour Message Batches API instead of real-time inference.

**C)** Headless mode runs without an interactive terminal UI, executes the prompt non-interactively, writes the result to stdout, and exits with a standard status code, making it ideal for scripts and CI/CD pipelines.

**D)** Headless mode skips reading `CLAUDE.md` unless `--memory` is explicitly passed.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
Interactive Claude Code provides a rich terminal UI designed for human chat, approvals, and diff reviews. The print flag (`-p`) activates Headless Mode: it takes an input prompt, processes it autonomously without blocking for keyboard input, outputs the response directly to stdout, and terminates cleanly. This enables seamless integration into bash scripts, GitHub Actions, and automated build runners.

**Why other options are incorrect:**
- **A)** `-p` disables the interactive terminal UI completely rather than auto-approving an interactive session.
- **B)** `-p` executes immediately using real-time inference, not the 24-hour Batches API.
- **D)** Project `CLAUDE.md` is still loaded in `-p` mode unless `--bare` is used to isolate configuration.

</details>

---

### Q136. Structured Output with `--output-format json` and `--json-schema`
In a CI/CD security scanning pipeline, you need Claude Code to evaluate a PR diff and return a guaranteed machine-readable vulnerability report. Which command configuration achieves this?

**A)** `claude -p "Find bugs" > output.txt`

**B)** `claude -p "Audit PR" --json-schema ./schema/vuln-report.json`

**C)** `claude --interactive --format json`

**D)** `claude -p "Audit PR" --output-format json --json-schema "$(cat ./schema/vuln-report.json)"`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
Combining headless mode (`-p`) with `--output-format json` and `--json-schema` enforces machine-readable JSON conforming to your schema. Crucially, `--json-schema` expects the schema as an **inline JSON string** (so if your schema lives in a file, pass `"$(cat ./schema/vuln-report.json)"` rather than a bare file path).

**Why other options are incorrect:**
- **A)** Raw text output can contain conversational filler that breaks downstream parsers.
- **B)** Passing a bare file path to `--json-schema` instead of an inline JSON string fails schema parsing, and omits `--output-format json`.
- **C)** Interactive mode blocks waiting for human input and does not enforce a JSON schema.

</details>

---

### Q137. The Purpose of `--bare` Mode in CI/CD Runners
Why is `--bare` mode recommended when running Claude Code in automated GitHub Actions or GitLab CI runners?

**A)** It deletes all files in the repository before running.

**B)** Deterministic Isolation: `--bare` mode bypasses auto-discovery of local user configuration (`~/.claude/`), custom developer hooks, and global personal skills, ensuring the CI runner operates in a clean, reproducible, strictly controlled environment.

**C)** It removes the need for an API key.

**D)** It runs Claude Code without installing Node.js.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
In CI/CD environments, builds must be completely deterministic and reproducible. If an agent runner accidentally inherits personal developer settings, unauthorized custom hooks, or local workstation aliases, build results can drift unpredictably. `--bare` ensures the runner boots from a pristine state, honoring only the repository's version-controlled configuration and explicit CLI flags.

**Why other options are incorrect:**
- **A)** Deleting repository files destroys the codebase being tested.
- **C)** API authentication is always required.
- **D)** The CLI runtime still requires its underlying execution environment.

</details>

---

### Q138. Capturing and Resuming Sessions (`--resume`)
An automated CI pipeline has two distinct steps:
1. Step 1: Claude Code generates an implementation plan for an issue and saves the session.
2. Step 2 (after human PR review approval): Claude Code resumes the session to execute the approved plan.

How can Step 2 resume the exact context from Step 1?

**A)** Re-run Step 1 with `--continue-last` across a new ephemeral container without saving the session ID.

**B)** Re-run Step 1 from scratch and pass only the PR title in Step 2.

**C)** Store the conversation inside `CLAUDE.md` so Step 2 loads it automatically.

**D)** Capture the `session_id` from Step 1's output and pass `--resume <session_id>` in Step 2.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
Claude Code tracks conversation sessions via unique session IDs. In automated multi-step workflows, an orchestrator can capture the session ID from Step 1 (e.g. from structured JSON metadata) and supply `--resume <session_id>` in a subsequent step. This restores the exact conversation history, discovered file state, and planning context without re-executing previous turns.

**Why other options are incorrect:**
- **A)** Without persisting the session ID or session storage across fresh CI containers, `--continue-last` has no local session to resume.
- **B)** Re-running from scratch wastes tokens and loses the approved plan context.
- **C)** `CLAUDE.md` is for static project rules, not dynamic per-PR session transcripts.

</details>

---

### Q139. Restricting Tools in Headless CI Pipelines
You run Claude Code in a GitHub Action to generate documentation from source code. You want to ensure the agent cannot push commits, modify code, or access the external internet. How should the command be structured?

**A)** `claude -p "Generate docs" --allowedTools "*"`

**B)** `claude -p "Generate docs" --dangerously-skip-permissions`

**C)** `claude -p "Generate docs" --allowedTools "Read,Grep,Glob,Write:docs/**"`

**D)** `claude -p "Generate docs"` with only a prompt instruction saying `"Do not touch src/"`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
In automated pipelines, applying the Principle of Least Privilege via `--allowedTools` is critical for security. Restricting tools to read operations and limiting writes strictly to `docs/**` prevents the agent from modifying application logic, running shell commands, or making unauthorized network requests.

**Why other options are incorrect:**
- **A)** Granting all tools (`*`) allows arbitrary bash execution in CI.
- **B)** `--dangerously-skip-permissions` removes interactive safety confirmations rather than restricting available tools.
- **D)** Prompt instructions alone are probabilistic and do not enforce hard file-write boundaries.

</details>

---

### Q140. Piping Data into Headless Claude Code
How can a developer pipe the current Git staged changes directly into Claude Code for a commit message recommendation?

**A)** `git diff --staged | claude -p "Generate a conventional commit message for these changes"`

**B)** `claude --staged-diff "Generate a conventional commit message"`

**C)** `claude -p "Generate a conventional commit message" --git-stage-only`

**D)** `git diff --staged > CLAUDE.md && claude "Commit"`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
Headless Claude Code natively reads from standard input (stdin). Piping the output of any command (such as `git diff --staged`) into `claude -p "<prompt>"` allows developers to compose Claude seamlessly into Unix command chains, linters, and pre-commit hooks.

**Why other options are incorrect:**
- **B, C)** `--staged-diff` and `--git-stage-only` are non-existent CLI flags.
- **D)** Overwriting `CLAUDE.md` destroys project instructions and omits `-p` for non-interactive execution.

</details>

---

### Q141. Managing Non-Interactive Prompts in Headless Mode
When running `claude -p "Refactor the user model"`, Claude encounters an ambiguity: should the phone number field be optional or required? In headless mode, what happens if the model attempts to prompt the user for input?

**A)** The CI runner hangs indefinitely waiting for input.

**B)** Because stdin is non-interactive, Claude Code detects the headless environment, evaluates default assumptions based on existing code context, or exits gracefully with a message describing the ambiguity rather than hanging.

**C)** Claude Code automatically opens a browser window for OAuth confirmation.

**D)** Claude Code deletes the ambiguous field from the schema and continues.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
In headless mode (`-p`), the interactive TTY input stream is closed. Claude Code is designed to recognize non-interactive environments: instead of blocking forever on a terminal prompt, it either resolves ambiguity using surrounding codebase conventions or halts with an explicit informational message detailing the required decision.

**Why other options are incorrect:**
- **A)** Modern headless runtimes prevent terminal deadlocks on closed stdin.
- **C)** It does not send SMS messages without custom webhook integrations.
- **D)** Destructive schema changes are avoided when parameters are ambiguous.

</details>

---

### Q142. Permission Boundaries in Interactive Mode
In interactive Claude Code, a developer runs a prompt that requires editing `package.json`. By default, what occurs before the file is edited?

**A)** Permission Prompting: Claude Code displays a unified diff of the proposed changes and requests human confirmation before writing changes to disk.

**B)** The file is edited immediately without any notice.

**C)** The developer must enter their credit card PIN.

**D)** The operating system reboots.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
By default, interactive Claude Code operates with human-in-the-loop safety boundaries. Before executing state-altering actions (such as editing files, deleting files, or running shell commands), Claude Code presents the exact proposed diff or command to the human operator for review and explicit approval.

**Why other options are incorrect:**
- **B)** Unannounced writes violate the default safety model.
- **C, D)** Financial PINs and reboots are completely unrelated to file edit permissions.

</details>

---

### Q143. Auto-Accepting Edits: The `--permission-mode` Flag
A developer is doing rapid prototyping on a disposable sandbox branch and wants Claude Code to edit files and run safe tests without prompting for every single micro-change. Which flag provides this mode?

**A)** `--run-as-hacker`

**B)** `--break-all-rules`

**C)** `--permission-mode auto` (or `--dangerously-skip-permissions` in sandboxed containers)

**D)** `--disable-safety`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
Claude Code provides configurable permission modes via `--permission-mode` (e.g. `plan`, `normal`, `auto`). In controlled sandbox environments or disposable development branches, developers can enable auto-mode to allow rapid iteration without constant manual approval prompts for routine file modifications.

**Why other options are incorrect:**
- **A, B, D)** These are fictional flags that do not exist in the official CLI.

</details>

---

### Q144. Secure Authentication in CI/CD Environments
What is the recommended practice for authenticating Claude Code within GitHub Actions or automated build systems?

**A)** Hardcoding the `ANTHROPIC_API_KEY` in the workflow `.yml` file in plain text.

**B)** Storing the `ANTHROPIC_API_KEY` in GitHub Encrypted Repository Secrets and injecting it as an environment variable in the workflow runner step.

**C)** Committing a `.env` file containing the key into the Git repository.

**D)** Having a developer manually type the key into the CI terminal on every commit.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
API keys must NEVER appear in version control, plain text workflow files, or public logs. In automated CI/CD environments, secrets must be stored in encrypted secret managers (such as GitHub Secrets or HashiCorp Vault) and passed dynamically as environment variables (`env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}`) to the runner step.

**Why other options are incorrect:**
- **A, C)** Hardcoding keys in YAML or committing `.env` files causes immediate credential leakage.
- **D)** Manual typing destroys pipeline automation.

</details>

---

### Q145. Controlling File Access with Path Denylists
A company wants to ensure Claude Code can never read or touch `/keys/production.pem` or `.env.production` even if a developer explicitly asks for it. Where should this restriction be configured?

**A)** By renaming the files to `.txt`.

**B)** By turning off the developer's computer.

**C)** Claude Code automatically reads all files on the hard drive regardless of config.

**D)** In `.claude/config.json` under `deniedPaths: ["keys/**", "**/*.pem", ".env.production*"]`.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
Project and enterprise configurations allow administrators to specify path denylists (`deniedPaths`). When paths are denylisted, Claude Code's file discovery, read, and write tools are blocked at the driver level from accessing matching files, preventing accidental exposure of sensitive keys or production credentials.

**Why other options are incorrect:**
- **A)** Renaming files does not protect them.
- **B)** Shutting down machines prevents work.
- **C)** Claude Code respects path restrictions strictly.

</details>

---

### Q146. Exit Codes in Headless Mode for Automated Quality Gates
A CI script executes:
`claude -p "Run tests and verify coverage > 80%"`
How does the CI script know whether the task succeeded or failed?

**A)** By checking the process exit code: Claude Code returns standard process exit codes (0 for success, non-zero for failure/error), allowing shell scripts (`set -e`) to fail the CI build automatically if quality criteria are unmet.

**B)** The CI script must count how many vowels Claude output.

**C)** The developer must watch the terminal live on a webcam.

**D)** Exit codes are always 0 regardless of failure.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
Standard Unix command-line utilities communicate execution status via process exit codes. Headless Claude Code exits with `0` when execution completes successfully within constraints, and returns non-zero codes (e.g. `1`, `2`) when errors, tool failures, or unfulfilled criteria occur, enabling automated build pipelines to break on failed checks.

**Why other options are incorrect:**
- **B, C)** Vowel counting and webcam monitoring are absurd.
- **D)** Returning 0 on failure would break automated build gating.

</details>

---

### Q147. Glob Triggers in Skill Configurations
A developer creates a skill in `.claude/skills/migrate-db/SKILL.md` with:
```yaml
---
name: migrate-db
paths:
  - "prisma/schema.prisma"
  - "migrations/**"
---
```
When does this skill automatically activate?

**A)** Whenever the developer opens Spotify.

**B)** On every computer startup.

**C)** Whenever the developer edits or queries files located in `migrations/` or touches `prisma/schema.prisma`.

**D)** Only on Sundays.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
The `paths` field in a Skill's YAML frontmatter configures automatic path-based activation. When Claude Code detects that the active task involves files matching the specified glob patterns (e.g., editing database schemas or migration scripts), it automatically loads the associated skill into memory to provide specialized migration assistance.

**Why other options are incorrect:**
- **A, B, D)** Activation is strictly tied to matching file paths within the codebase.

</details>

---

### Q148. Memory Leaks in Multi-Turn Interactive CLI Sessions
During a long 4-hour interactive session in Claude Code, the developer notices that Claude's responses are becoming slower and token usage per turn is climbing. Which slash command compacts conversational memory without losing the active task state?

**A)** `/quit`

**B)** `/compact`

**C)** `/delete-everything`

**D)** `/reboot`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
The `/compact` command is built specifically for long interactive Claude Code sessions. It summarizes older conversational history, discards verbose intermediate tool outputs (like file read dumps and test runs), and retains only the essential facts, goals, and architectural decisions, refreshing the active context window and lowering latency.

**Why other options are incorrect:**
- **A)** `/quit` exits the session and loses in-memory context.
- **C, D)** These are destructive or non-existent commands.

</details>

---

### Q149. The "Approval Fatigue" Trap in CLI Tooling
A development team configures Claude Code with ultra-strict permissions: every single file read, directory listing, and grep query requires manual human approval. After three days, what failure mode is observed?

**A)** The CPU becomes colder.

**B)** 100% bug-free software.

**C)** The developers learn to type faster.

**D)** Approval Fatigue Anti-Pattern: Developers become so overwhelmed by dozens of repetitive, low-risk approval prompts that they begin pressing "Y" (Approve) automatically without reading, ultimately approving a high-risk destructive action without noticing.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
*Approval Fatigue* is a well-documented human factors security risk. When users are bombarded with continuous micro-approval requests for harmless operations (like reading a file or running `ls`), their critical attention degrades. Statistical studies show blind approval rates rise to ~93%, defeating the purpose of security gates. Best practice: auto-approve low-risk read operations, reserving manual approval gates strictly for destructive state changes.

**Why other options are incorrect:**
- **A, C)** Unrelated to cognitive ergonomics.
- **B)** Blind approvals lead to more bugs and accidental mistakes, not bug-free software.

**Anti-Pattern Alert:**
*Approval Fatigue*: Bombarding human operators with approval prompts for routine, low-risk actions, leading to habitual blind clicking that undermines safety.

</details>

---

### Q150. Inspecting Available Skills
Which command allows a developer inside Claude Code to view all currently indexed skills and their activation descriptions?

**A)** `cat /dev/null`

**B)** `git status`

**C)** `/skills` (or `/help`)

**D)** `ping google.com`

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** C

**Explanation:**
The `/skills` slash command lists all active skills discovered in the current project (`.claude/skills/`) and user profile (`~/.claude/skills/`), displaying their names, descriptions, and trigger conditions so developers know what automated capabilities are available.

**Why other options are incorrect:**
- **A, B, D)** Standard shell commands do not inspect Claude Code skill registries.

</details>

---

### Q151. Disabling Telemetry in Enterprise Environments
In a highly regulated bank environment, developers are prohibited from transmitting anonymous telemetry data. How can telemetry be explicitly disabled in Claude Code?

**A)** Set `"telemetry": false` in Enterprise/User `config.json` or pass the environment variable `CLAUDE_CODE_DISABLE_TELEMETRY=1`.

**B)** Rename the project directory to `private`.

**C)** Disconnect the company's power grid.

**D)** Uninstall Git.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
Enterprise software must provide compliance controls. Claude Code supports explicit telemetry opt-out flags via configuration settings (`"telemetry": false`) or environment variables (`CLAUDE_CODE_DISABLE_TELEMETRY=1`), ensuring that no analytical usage metrics or telemetry payloads leave the corporate network.

**Why other options are incorrect:**
- **B, C, D)** Absurd actions that disrupt development operations.

</details>

---

### Q152. Pre-Commit Hooks Integration
An engineering organization wants Claude Code to review every local commit automatically for hardcoded credentials and formatting errors before allowing `git commit` to complete. Where should this workflow be wired?

**A)** In the DNS server.

**B)** In a Git pre-commit hook (e.g. `.git/hooks/pre-commit` or via Husky) executing `claude -p` in headless mode against staged diffs.

**C)** In the company's annual tax filing.

**D)** In the user's browser bookmarks.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
Git hooks run automatically at defined points in the version control lifecycle. A `.git/hooks/pre-commit` script that pipes staged diffs into `claude -p` with a security evaluation prompt ensures that every commit is audited before it can be committed to Git history.

**Why other options are incorrect:**
- **A, C, D)** Git hooks execute through version control scripts, not taxes, bookmarks, or DNS servers.

</details>

---

### Q153. Custom Subagent System Prompts
When creating a specialized subagent for SQL database optimization in `.claude/agents/db-optimizer.md`, what should the markdown body contain?

**A)** Nothing; subagent files must be empty.

**B)** An image of a database server.

**C)** A copy of the entire Linux operating system.

**D)** The specialized system prompt establishing the subagent's role, optimization heuristics, index analysis rules, and expected response structure.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** D

**Explanation:**
The markdown body of a subagent definition file serves as that subagent's dedicated system prompt. It defines the persona, domain-specific guidelines (e.g. EXPLAIN query plan analysis, B-tree vs GIN indexing guidelines), constraints, and output formatting rules that govern its execution when spawned.

**Why other options are incorrect:**
- **A, B, C)** The markdown body must contain clear textual system instructions.

</details>

---

### Q154. Managing Concurrent Claude Code Sessions
A developer opens three separate terminal tabs and runs Claude Code in each tab on the same Git repository simultaneously. What precaution should be taken to prevent Git index corruption?

**A)** Each session operates in an independent process; however, because they share the same physical filesystem and Git workspace, running concurrent writes across tabs can cause write lock collisions (`index.lock`) or conflicting edits. Developers should work on separate feature branches or separate git worktrees (`git worktree add`) when running concurrent sessions.

**B)** Git automatically merges all files every millisecond.

**C)** Claude Code will delete all three terminals.

**D)** Developers should not use computers.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** A

**Explanation:**
Running concurrent agent processes against the exact same working directory creates physical filesystem race conditions and Git lockfile collisions (`.git/index.lock`). The recommended practice for parallel AI development is using **Git Worktrees** (`git worktree`), which gives each concurrent session its own isolated working directory and branch while sharing the same underlying repository history.

**Why other options are incorrect:**
- **B)** Git never auto-merges files silently in real-time.
- **C, D)** Overreaction and non-existent behaviors.

</details>

---

### Q155. Domain 2 Configuration & Workflow Summary
Which architectural principle best summarizes modern Claude Code configuration?

**A)** Dump all possible instructions into a single root file and give all agents root access.

**B)** Layered, Least-Privilege, On-Demand Architecture: Use concise root configuration for global standards, path-scoped rules for localized syntax, on-demand skills for episodic tasks, isolated subagents for heavy exploration, and headless pipelines with strict tool allowlists for CI/CD automation.

**C)** Disable version control and run everything interactively.

**D)** Rely exclusively on natural language conversation without any configuration files.

<details>
<summary>Show Answer & Explanation</summary>

**Correct Answer:** B

**Explanation:**
Enterprise AI software engineering requires a clean separation of concerns. A layered architecture keeps baseline context lean, triggers localized rules only when relevant paths are touched, loads complex workflows on-demand via skills, isolates exploratory workloads into subagents, and applies least-privilege tool allowlists to automated CI/CD runners.

**Why other options are incorrect:**
- **A, C, D)** Monolithic dumping, abandoning version control, or omitting structured configuration violates production engineering best practices.

</details>
