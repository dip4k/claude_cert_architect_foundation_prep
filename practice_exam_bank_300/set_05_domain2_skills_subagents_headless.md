# CCAR-F Exam Practice Bank: Set 5
## Domain 2: Claude Code Configuration & Workflows (Part 2: Skills, Subagents, Plan Mode & Headless CI/CD)
### Questions 126 – 155

---

### Q126. Semantic Discovery of Skills
How does Claude Code discover and load modular developer Skills (`SKILL.md` files) without bloating the active conversation context at startup?

**A)** It reads all `SKILL.md` files entirely into memory on every session initialization.
**B)** Semantic Discovery: At startup, Claude Code indexes only the lightweight metadata (name and description) of all available skills; when a user's prompt matches a skill's purpose, Claude prompts or auto-activates the skill and lazy-loads the full markdown instructions on-demand.
**C)** It searches Google to find skills.
**D)** Skills must be manually compiled into binary C++ libraries.

**Correct Answer:** B

**Explanation:**
Skills provide modular, on-demand expertise. To maintain a clean context window, Claude Code does not load the full text of every `SKILL.md` at launch. Instead, it indexes only the names and descriptions into a lightweight discovery registry. When a user prompt matches a skill semantically, Claude recognizes the relevance, loads the complete instructions dynamically, and executes the specialized workflow.

**Why other options are incorrect:**
- **A)** Loading all skill bodies at startup would cause severe context bloat and high baseline costs.
- **C)** Skills are local project or user files, not web searches.
- **D)** Skills are simple Markdown files with YAML frontmatter, not C++ binaries.

---

### Q127. Skill YAML Frontmatter Configuration
What is the proper YAML frontmatter format for defining a Claude Code skill named `deploy-k8s` that triggers on Kubernetes-related prompts?

**A)**
```yaml
---
name: deploy-k8s
description: Validates manifests, runs dry-runs, and deploys services to Kubernetes clusters. Use when deploying or troubleshooting k8s pods and ingress.
---
```
**B)**
```yaml
---
command: "kubectl apply -f"
auto_run: true
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

**Correct Answer:** A

**Explanation:**
A skill's YAML frontmatter requires a unique `name` and a descriptive `description`. The description is crucial: Claude uses this text for semantic intent matching when evaluating user prompts. Clear descriptions detailing *what* the skill does and *when* to use it ensure accurate on-demand activation.

**Why other options are incorrect:**
- **B, C, D)** These do not match the standard Skill schema required by Claude Code.

---

### Q128. The `context: fork` Parameter in Skills
In an advanced `SKILL.md`, a developer adds `context: fork` to the YAML frontmatter. What architectural behavior does this trigger?

**A)** It creates a new Git branch in the repository.
**B)** Isolated Subagent Execution: The skill runs inside a dedicated, isolated subagent context with a clean working memory, preventing verbose intermediate logs from polluting the primary user conversation, and returns only the final summary to the main thread.
**C)** It duplicates the user's hard drive.
**D)** It forks the operating system kernel into two processes.

**Correct Answer:** B

**Explanation:**
Setting `context: fork` instructs Claude Code to execute the skill within an isolated subagent thread. This is particularly valuable for exploratory or noisy operations (e.g., deep test runs, codebase searches, large refactoring investigations). The subagent performs the heavy lifting in its own ephemeral context and reports back a concise summary to the main conversation, keeping the developer's primary context lean.

**Why other options are incorrect:**
- **A)** It is an execution context fork, not a Git branch.
- **C, D)** It does not duplicate hard drives or fork OS kernels.

---

### Q129. Overriding Reasoning Effort in Skills
A developer writes a skill for generating quick commit messages (`git-commit`). The skill does not require deep mathematical or architectural reasoning. How can the skill minimize latency and cost?

**A)** Add `effort: low` to the skill configuration, allowing Claude to bypass extensive extended thinking for simple text formatting tasks.
**B)** Delete the Git repository.
**C)** Hardcode `tokens: 1`.
**D)** Set `temperature: 2.0`.

**Correct Answer:** A

**Explanation:**
Skills can specify effort level overrides in their configuration (e.g. `effort: low`, `effort: medium`, `effort: high`). For simple, low-complexity tasks like drafting commit messages or formatting markdown, setting `effort: low` prevents the model from spending thousands of unnecessary tokens in deep extended thinking, optimizing both speed and token expenditure.

**Why other options are incorrect:**
- **B)** Deleting repos destroys project code.
- **C)** Setting tokens to 1 causes immediate truncation.
- **D)** High temperature does not reduce thinking tokens and increases randomness.

---

### Q130. Subagent Definition in `.claude/agents/`
Where are dedicated subagents defined in a Claude Code project, and what file format do they use?

**A)** Inside `.claude/agents/<agent-name>.md` using Markdown with YAML frontmatter specifying their system prompt and allowed tools.
**B)** In `/etc/passwd` as binary files.
**C)** In Python `.pyc` compiled files.
**D)** In Microsoft Word `.docx` documents.

**Correct Answer:** A

**Explanation:**
Claude Code subagents are defined as Markdown files inside `.claude/agents/` (project-level) or `~/.claude/agents/` (user-level). The YAML frontmatter specifies metadata such as `name`, `description`, `tools`, and model configuration, while the markdown body provides the specialized system prompt governing the subagent's behavior.

**Why other options are incorrect:**
- **B, C, D)** Subagents are human-readable, version-controllable Markdown assets, not system password files, bytecode, or Word documents.

---

### Q131. Subagent Tool Sandboxing for Code Review
You want to configure a subagent named `code-reviewer` to audit pull requests without the ability to modify any files or execute shell commands. What `tools` configuration should be placed in its frontmatter?

**A)** `tools: ["all"]`
**B)** `tools: ["read_file", "list_directory", "git_diff"]` (strictly omitting `write_file`, `edit_file`, and `bash`)
**C)** `tools: ["bash"]`
**D)** `tools: ["rm -rf"]`

**Correct Answer:** B

**Explanation:**
To create a read-only auditor, you restrict its tool allowlist exclusively to read operations (`read_file`, `list_directory`, `git_diff`). By withholding `write_file`, `edit_file`, and `bash`, the subagent is architecturally sandboxed: it cannot write code, delete assets, or execute arbitrary terminal commands.

**Why other options are incorrect:**
- **A, C, D)** Granting write or shell capabilities violates read-only isolation principles and allows unauthorized modifications.

---

### Q132. What is Plan Mode in Claude Code?
What is the primary function of Plan Mode (toggled via `Shift + Tab` or `/plan`, or CLI flag `--permission-mode plan`)?

**A)** It plans the developer's calendar and schedules lunch meetings.
**B)** Read-Only Analytical Exploration: Claude explores files, maps dependencies, and presents a comprehensive step-by-step implementation blueprint for human review BEFORE modifying any code in the repository.
**C)** It compiles the codebase directly to assembly language.
**D)** It disables all AI features permanently.

**Correct Answer:** B

**Explanation:**
Plan Mode shifts Claude Code from active execution to an upfront planning state. In Plan Mode, Claude is restricted from making direct file modifications or executing state-altering commands. It reads files, investigates the architecture, and drafts a clear, structured implementation plan. The developer reviews and approves the plan before Claude enters execution mode, preventing misguided refactors.

**Why other options are incorrect:**
- **A)** Plan Mode plans software changes, not personal schedules.
- **C)** Plan Mode does not compile assembly code.
- **D)** It is an intentional planning workflow, not a feature disablement.

---

### Q133. The Role of `useAutoModeDuringPlan`
What capability does `useAutoModeDuringPlan` provide during Plan Mode exploration?

**A)** It allows Claude to automatically push code to production without review.
**B)** It permits safe, read-only diagnostic commands (e.g. running `git status`, searching files, checking build status) to execute autonomously without repeatedly prompting the user for approval during the research phase, while still strictly blocking file writes.
**C)** It converts all tests to Python.
**D)** It orders pizza for the development team.

**Correct Answer:** B

**Explanation:**
When investigating a complex codebase during Plan Mode, Claude often needs to execute multiple read-only discovery commands (e.g. `grep`, `find`, checking types). If every single command requires human confirmation, the developer suffers from prompt fatigue. `useAutoModeDuringPlan` auto-approves verified read-only operations during planning while keeping edit and write operations locked down.

**Why other options are incorrect:**
- **A)** Plan Mode strictly prohibits unauthorized production pushes.
- **C, D)** Unrelated to language conversion or food ordering.

---

### Q134. When to Use Plan Mode vs. Direct Execution
Under which scenario is Plan Mode most strongly recommended?

**A)** Fixing a simple typo in a README file.
**B)** A complex, multi-service architectural refactoring involving database schema changes and multiple API contract updates across several files.
**C)** Checking the current date in the terminal.
**D)** Renaming a single local variable in a test file.

**Correct Answer:** B

**Explanation:**
Plan Mode is designed for high-risk, multi-file, or ambiguous engineering tasks. When touching multiple services, modifying database migrations, or altering public API contracts, jumping directly into file edits risks breaking systems midway. Upfront planning ensures all dependencies and potential failure modes are mapped and approved before code changes begin. Simple one-line edits or typos do not require Plan Mode overhead.

**Why other options are incorrect:**
- **A, C, D)** Trivial, low-risk edits are handled faster and more efficiently via direct execution.

---

### Q135. Headless Mode (`-p` Flag) in Automated Pipelines
How does Claude Code's headless mode (`claude -p "Analyze git diff"`) differ from standard interactive mode?

**A)** Headless mode runs without a graphical or interactive terminal UI, executes the prompt non-interactively, streams/outputs the result to stdout, and exits with a standard process status code, making it ideal for scripts and CI/CD pipelines.
**B)** Headless mode disconnects the developer's monitor.
**C)** Headless mode disables the internet.
**D)** Headless mode only works on headless Linux servers without USB ports.

**Correct Answer:** A

**Explanation:**
Interactive Claude Code provides a rich terminal UI designed for human chat, approvals, and diff reviews. The print flag (`-p`) activates Headless Mode: it takes an input prompt, processes it autonomously without blocking for keyboard input, outputs the response directly to stdout, and terminates cleanly. This enables seamless integration into bash scripts, GitHub Actions, and automated build runners.

**Why other options are incorrect:**
- **B, C, D)** Headless mode refers to non-interactive software execution, not hardware disconnection.

---

### Q136. Structured Output with `--output-format json` and `--json-schema`
In a CI/CD security scanning pipeline, you need Claude Code to evaluate a PR diff and return a guaranteed machine-readable vulnerability report. Which command configuration achieves this?

**A)** `claude -p "Find bugs" > output.txt`
**B)** `claude -p "Audit PR" --output-format json --json-schema ./schema/vuln-report.json`
**C)** `claude --interactive --format text`
**D)** `cat pr.diff | grep "vulnerability"`

**Correct Answer:** B

**Explanation:**
Combining headless mode (`-p`) with `--output-format json` and a formal `--json-schema` enables deterministic integration into CI/CD pipelines. The output is constrained to valid JSON strictly conforming to the specified schema, allowing downstream automation (e.g., `jq`, GitHub PR comment bots, Jira ticket creators) to parse findings reliably without regex guessing.

**Why other options are incorrect:**
- **A)** Raw text output can contain unstructured conversational filler that breaks downstream parsers.
- **C)** Interactive mode blocks waiting for human input and does not enforce JSON schemas.
- **D)** Basic grep lacks AI vulnerability analysis.

---

### Q137. The Purpose of `--bare` Mode in CI/CD Runners
Why is `--bare` mode recommended when running Claude Code in automated GitHub Actions or GitLab CI runners?

**A)** It runs Claude Code without installing Node.js.
**B)** Deterministic Isolation: `--bare` mode bypasses auto-discovery of local user configuration (`~/.claude/`), custom developer hooks, and global personal skills, ensuring the CI runner operates in a clean, reproducible, strictly controlled environment.
**C)** It deletes all files in the repository before running.
**D)** It removes the need for an API key.

**Correct Answer:** B

**Explanation:**
In CI/CD environments, builds must be completely deterministic and reproducible. If an agent runner accidentally inherits personal developer settings, unauthorized custom hooks, or local workstation aliases, build results can drift unpredictably. `--bare` ensures the runner boots from a pristine state, honoring only the repository's version-controlled configuration and explicit CLI flags.

**Why other options are incorrect:**
- **A)** The CLI runtime still requires its underlying execution environment.
- **C)** Deleting repository files destroys the codebase being tested.
- **D)** API authentication is always required.

---

### Q138. Capturing and Resuming Sessions (`--resume`)
An automated CI pipeline has two distinct steps:
1. Step 1: Claude Code generates an implementation plan for an issue and saves the session.
2. Step 2 (after human PR review approval): Claude Code resumes the session to execute the approved plan.
How can Step 2 resume the exact context from Step 1?

**A)** Capture the `session_id` from Step 1's output and pass `--resume <session_id>` in Step 2.
**B)** Copy the developer's RAM memory to a thumb drive.
**C)** Re-run Step 1 from scratch and hope it generates the same plan.
**D)** Claude Code sessions cannot be resumed once terminated.

**Correct Answer:** A

**Explanation:**
Claude Code tracks conversation sessions via unique session IDs. In automated multi-step workflows, an orchestrator can capture the session ID from Step 1 (e.g. from structured JSON metadata) and supply `--resume <session_id>` in a subsequent step. This restores the exact conversation history, discovered file state, and planning context without re-executing previous turns.

**Why other options are incorrect:**
- **B)** Physical RAM transfer is impractical and unnecessary.
- **C)** Re-running from scratch wastes tokens and introduces non-deterministic variations.
- **D)** Session resumption is a built-in feature of Claude Code.

---

### Q139. Restricting Tools in Headless CI Pipelines
You run Claude Code in a GitHub Action to generate documentation from source code. You want to ensure the agent cannot push commits, modify code, or access the external internet. How should the command be structured?

**A)** `claude -p "Generate docs" --allowedTools "read_file,list_directory,write_file:docs/**"`
**B)** `claude -p "Generate docs" --allowedTools "*"`
**C)** `sudo claude -p "Generate docs"`
**D)** Unplug the CI server from the wall.

**Correct Answer:** A

**Explanation:**
In automated pipelines, applying the Principle of Least Privilege via `--allowedTools` is critical for security. Restricting tools to read operations and limiting write operations strictly to the `docs/` directory prevents the agent from modifying application logic, running shell commands, or making unauthorized network requests.

**Why other options are incorrect:**
- **B)** Granting all tools (`*`) allows arbitrary bash execution in CI.
- **C)** Running as `sudo` unnecessarily elevates system privileges.
- **D)** Unplugging servers kills the CI runner.

---

### Q140. Piping Data into Headless Claude Code
How can a developer pipe the current Git staged changes directly into Claude Code for a commit message recommendation?

**A)** `git diff --staged | claude -p "Generate a conventional commit message for these changes"`
**B)** `claude --copy-paste-staged`
**C)** `claude -p "Open git diff in Microsoft Word"`
**D)** `git push origin main --force`

**Correct Answer:** A

**Explanation:**
Headless Claude Code natively reads from standard input (stdin). Piping the output of any command (such as `git diff --staged`) into `claude -p "<prompt>"` allows developers to compose Claude seamlessly into Unix command chains, linters, and pre-commit hooks.

**Why other options are incorrect:**
- **B, C)** These are non-existent commands.
- **D)** Force pushing bypasses review and risks overwriting remote repositories.

---

### Q141. Managing Non-Interactive Prompts in Headless Mode
When running `claude -p "Refactor the user model"`, Claude encounters an ambiguity: should the phone number field be optional or required? In headless mode, what happens if the model attempts to prompt the user for input?

**A)** The CI runner hangs indefinitely waiting for input.
**B)** Because stdin is non-interactive, Claude Code detects the headless environment, evaluates default assumptions based on existing code context, or fails gracefully with a message describing the ambiguity rather than hanging.
**C)** The CI runner sends a text message to the developer's phone.
**D)** Claude automatically deletes the phone number column.

**Correct Answer:** B

**Explanation:**
In headless mode (`-p`), the interactive TTY input stream is closed. Claude Code is designed to recognize non-interactive environments: instead of blocking forever on a terminal prompt, it either resolves ambiguity using surrounding codebase conventions or halts with an explicit informational message detailing the required decision.

**Why other options are incorrect:**
- **A)** Modern headless runtimes prevent terminal deadlocks on closed stdin.
- **C)** It does not send SMS messages without custom webhook integrations.
- **D)** Destructive schema changes are avoided when parameters are ambiguous.

---

### Q142. Permission Boundaries in Interactive Mode
In interactive Claude Code, a developer runs a prompt that requires editing `package.json`. By default, what occurs before the file is edited?

**A)** The file is edited immediately without any notice.
**B)** Permission Prompting: Claude Code displays a unified diff of the proposed changes and requests human confirmation before writing changes to disk.
**C)** The developer must enter their credit card PIN.
**D)** The operating system reboots.

**Correct Answer:** B

**Explanation:**
By default, interactive Claude Code operates with human-in-the-loop safety boundaries. Before executing state-altering actions (such as editing files, deleting files, or running shell commands), Claude Code presents the exact proposed diff or command to the human operator for review and explicit approval.

**Why other options are incorrect:**
- **A)** Unannounced writes violate the default safety model.
- **C, D)** Financial PINs and reboots are completely unrelated to file edit permissions.

---

### Q143. Auto-Accepting Edits: The `--permission-mode` Flag
A developer is doing rapid prototyping on a disposable sandbox branch and wants Claude Code to edit files and run safe tests without prompting for every single micro-change. Which flag provides this mode?

**A)** `--permission-mode auto` (or `--dangerously-skip-permissions` in sandboxed containers)
**B)** `--break-all-rules`
**C)** `--disable-safety`
**D)** `--run-as-hacker`

**Correct Answer:** A

**Explanation:**
Claude Code provides configurable permission modes via `--permission-mode` (e.g. `plan`, `normal`, `auto`). In controlled sandbox environments or disposable development branches, developers can enable auto-mode to allow rapid iteration without constant manual approval prompts for routine file modifications.

**Why other options are incorrect:**
- **B, C, D)** These are fictional flags that do not exist in the official CLI.

---

### Q144. Secure Authentication in CI/CD Environments
What is the recommended practice for authenticating Claude Code within GitHub Actions or automated build systems?

**A)** Hardcoding the `ANTHROPIC_API_KEY` in the workflow `.yml` file in plain text.
**B)** Storing the `ANTHROPIC_API_KEY` in GitHub Encrypted Repository Secrets and injecting it as an environment variable in the workflow runner step.
**C)** Committing a `.env` file containing the key into the Git repository.
**D)** Having a developer manually type the key into the CI terminal on every commit.

**Correct Answer:** B

**Explanation:**
API keys must NEVER appear in version control, plain text workflow files, or public logs. In automated CI/CD environments, secrets must be stored in encrypted secret managers (such as GitHub Secrets or HashiCorp Vault) and passed dynamically as environment variables (`env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}`) to the runner step.

**Why other options are incorrect:**
- **A, C)** Hardcoding keys in YAML or committing `.env` files causes immediate credential leakage.
- **D)** Manual typing destroys pipeline automation.

---

### Q145. Controlling File Access with Path Denylists
A company wants to ensure Claude Code can never read or touch `/keys/production.pem` or `.env.production` even if a developer explicitly asks for it. Where should this restriction be configured?

**A)** In `.claude/config.json` under `deniedPaths: ["keys/**", "**/*.pem", ".env.production*"]`.
**B)** By renaming the files to `.txt`.
**C)** By turning off the developer's computer.
**D)** Claude Code automatically reads all files on the hard drive regardless of config.

**Correct Answer:** A

**Explanation:**
Project and enterprise configurations allow administrators to specify path denylists (`deniedPaths`). When paths are denylisted, Claude Code's file discovery, read, and write tools are blocked at the driver level from accessing matching files, preventing accidental exposure of sensitive keys or production credentials.

**Why other options are incorrect:**
- **B)** Renaming files does not protect them.
- **C)** Shutting down machines prevents work.
- **D)** Claude Code respects path restrictions strictly.

---

### Q146. Exit Codes in Headless Mode for Automated Quality Gates
A CI script executes:
`claude -p "Run tests and verify coverage > 80%"`
How does the CI script know whether the task succeeded or failed?

**A)** By checking the process exit code: Claude Code returns standard process exit codes (0 for success, non-zero for failure/error), allowing shell scripts (`set -e`) to fail the CI build automatically if quality criteria are unmet.
**B)** The CI script must count how many vowels Claude output.
**C)** The developer must watch the terminal live on a webcam.
**D)** Exit codes are always 0 regardless of failure.

**Correct Answer:** A

**Explanation:**
Standard Unix command-line utilities communicate execution status via process exit codes. Headless Claude Code exits with `0` when execution completes successfully within constraints, and returns non-zero codes (e.g. `1`, `2`) when errors, tool failures, or unfulfilled criteria occur, enabling automated build pipelines to break on failed checks.

**Why other options are incorrect:**
- **B, C)** Vowel counting and webcam monitoring are absurd.
- **D)** Returning 0 on failure would break automated build gating.

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

**A)** Whenever the developer edits or queries files located in `migrations/` or touches `prisma/schema.prisma`.
**B)** On every computer startup.
**C)** Only on Sundays.
**D)** Whenever the developer opens Spotify.

**Correct Answer:** A

**Explanation:**
The `paths` field in a Skill's YAML frontmatter configures automatic path-based activation. When Claude Code detects that the active task involves files matching the specified glob patterns (e.g., editing database schemas or migration scripts), it automatically loads the associated skill into memory to provide specialized migration assistance.

**Why other options are incorrect:**
- **B, C, D)** Activation is strictly tied to matching file paths within the codebase.

---

### Q148. Memory Leaks in Multi-Turn Interactive CLI Sessions
During a long 4-hour interactive session in Claude Code, the developer notices that Claude's responses are becoming slower and token usage per turn is climbing. Which slash command compacts conversational memory without losing the active task state?

**A)** `/compact`
**B)** `/quit`
**C)** `/delete-everything`
**D)** `/reboot`

**Correct Answer:** A

**Explanation:**
The `/compact` command is built specifically for long interactive Claude Code sessions. It summarizes older conversational history, discards verbose intermediate tool outputs (like file read dumps and test runs), and retains only the essential facts, goals, and architectural decisions, refreshing the active context window and lowering latency.

**Why other options are incorrect:**
- **B)** `/quit` exits the session and loses in-memory context.
- **C, D)** These are destructive or non-existent commands.

---

### Q149. The "Approval Fatigue" Trap in CLI Tooling
A development team configures Claude Code with ultra-strict permissions: every single file read, directory listing, and grep query requires manual human approval. After three days, what failure mode is observed?

**A)** 100% bug-free software.
**B)** Approval Fatigue Anti-Pattern: Developers become so overwhelmed by dozens of repetitive, low-risk approval prompts that they begin pressing "Y" (Approve) automatically without reading, ultimately approving a high-risk destructive action without noticing.
**C)** The developers learn to type faster.
**D)** The CPU becomes colder.

**Correct Answer:** B

**Explanation:**
*Approval Fatigue* is a well-documented human factors security risk. When users are bombarded with continuous micro-approval requests for harmless operations (like reading a file or running `ls`), their critical attention degrades. Statistical studies show blind approval rates rise to ~93%, defeating the purpose of security gates. Best practice: auto-approve low-risk read operations, reserving manual approval gates strictly for destructive state changes.

**Why other options are incorrect:**
- **A)** Blind approvals lead to more bugs and accidental mistakes, not bug-free software.
- **C, D)** Unrelated to cognitive ergonomics.

**Anti-Pattern Alert:**
*Approval Fatigue*: Bombarding human operators with approval prompts for routine, low-risk actions, leading to habitual blind clicking that undermines safety.

---

### Q150. Inspecting Available Skills
Which command allows a developer inside Claude Code to view all currently indexed skills and their activation descriptions?

**A)** `/skills` (or `/help`)
**B)** `cat /dev/null`
**C)** `git status`
**D)** `ping google.com`

**Correct Answer:** A

**Explanation:**
The `/skills` slash command lists all active skills discovered in the current project (`.claude/skills/`) and user profile (`~/.claude/skills/`), displaying their names, descriptions, and trigger conditions so developers know what automated capabilities are available.

**Why other options are incorrect:**
- **B, C, D)** Standard shell commands do not inspect Claude Code skill registries.

---

### Q151. Disabling Telemetry in Enterprise Environments
In a highly regulated bank environment, developers are prohibited from transmitting anonymous telemetry data. How can telemetry be explicitly disabled in Claude Code?

**A)** Set `"telemetry": false` in Enterprise/User `config.json` or pass the environment variable `CLAUDE_CODE_DISABLE_TELEMETRY=1`.
**B)** Disconnect the company's power grid.
**C)** Uninstall Git.
**D)** Rename the project directory to `private`.

**Correct Answer:** A

**Explanation:**
Enterprise software must provide compliance controls. Claude Code supports explicit telemetry opt-out flags via configuration settings (`"telemetry": false`) or environment variables (`CLAUDE_CODE_DISABLE_TELEMETRY=1`), ensuring that no analytical usage metrics or telemetry payloads leave the corporate network.

**Why other options are incorrect:**
- **B, C, D)** Absurd actions that disrupt development operations.

---

### Q152. Pre-Commit Hooks Integration
An engineering organization wants Claude Code to review every local commit automatically for hardcoded credentials and formatting errors before allowing `git commit` to complete. Where should this workflow be wired?

**A)** In a Git pre-commit hook (e.g. `.git/hooks/pre-commit` or via Husky) executing `claude -p` in headless mode against staged diffs.
**B)** In the company's annual tax filing.
**C)** In the user's browser bookmarks.
**D)** In the DNS server.

**Correct Answer:** A

**Explanation:**
Git hooks run automatically at defined points in the version control lifecycle. A `.git/hooks/pre-commit` script that pipes staged diffs into `claude -p` with a security evaluation prompt ensures that every commit is audited before it can be committed to Git history.

**Why other options are incorrect:**
- **B, C, D)** Git hooks execute through version control scripts, not taxes, bookmarks, or DNS servers.

---

### Q153. Custom Subagent System Prompts
When creating a specialized subagent for SQL database optimization in `.claude/agents/db-optimizer.md`, what should the markdown body contain?

**A)** An image of a database server.
**B)** The specialized system prompt establishing the subagent's role, optimization heuristics, index analysis rules, and expected response structure.
**C)** A copy of the entire Linux operating system.
**D)** Nothing; subagent files must be empty.

**Correct Answer:** B

**Explanation:**
The markdown body of a subagent definition file serves as that subagent's dedicated system prompt. It defines the persona, domain-specific guidelines (e.g. EXPLAIN query plan analysis, B-tree vs GIN indexing guidelines), constraints, and output formatting rules that govern its execution when spawned.

**Why other options are incorrect:**
- **A, C, D)** The markdown body must contain clear textual system instructions.

---

### Q154. Managing Concurrent Claude Code Sessions
A developer opens three separate terminal tabs and runs Claude Code in each tab on the same Git repository simultaneously. What precaution should be taken to prevent Git index corruption?

**A)** Developers should not use computers.
**B)** Each session operates in an independent process; however, because they share the same physical filesystem and Git workspace, running concurrent writes across tabs can cause write lock collisions (`index.lock`) or conflicting edits. Developers should work on separate feature branches or separate git worktrees (`git worktree add`) when running concurrent sessions.
**C)** Git automatically merges all files every millisecond.
**D)** Claude Code will delete all three terminals.

**Correct Answer:** B

**Explanation:**
Running concurrent agent processes against the exact same working directory creates physical filesystem race conditions and Git lockfile collisions (`.git/index.lock`). The recommended practice for parallel AI development is using **Git Worktrees** (`git worktree`), which gives each concurrent session its own isolated working directory and branch while sharing the same underlying repository history.

**Why other options are incorrect:**
- **A, D)** Overreaction and non-existent behaviors.
- **C)** Git never auto-merges files silently in real-time.

---

### Q155. Domain 2 Configuration & Workflow Summary
Which architectural principle best summarizes modern Claude Code configuration?

**A)** Dump all possible instructions into a single root file and give all agents root access.
**B)** Layered, Least-Privilege, On-Demand Architecture: Use concise root configuration for global standards, path-scoped rules for localized syntax, on-demand skills for episodic tasks, isolated subagents for heavy exploration, and headless pipelines with strict tool allowlists for CI/CD automation.
**C)** Disable version control and run everything interactively.
**D)** Rely exclusively on natural language conversation without any configuration files.

**Correct Answer:** B

**Explanation:**
Enterprise AI software engineering requires a clean separation of concerns. A layered architecture keeps baseline context lean, triggers localized rules only when relevant paths are touched, loads complex workflows on-demand via skills, isolates exploratory workloads into subagents, and applies least-privilege tool allowlists to automated CI/CD runners.

**Why other options are incorrect:**
- **A, C, D)** Monolithic dumping, abandoning version control, or omitting structured configuration violates production engineering best practices.

