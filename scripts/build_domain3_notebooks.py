"""
Domain 3 Notebook Generator: Claude Code Configuration & Workflows (TS 3.1 - TS 3.6).
Generates comprehensive Jupyter notebooks with step-by-step walkthroughs,
offline simulations, and automated verification checks.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.notebook_builder import code_cell, markdown_cell, save_notebook


def build_ts_3_1():
    cells = [
        markdown_cell("""# Domain 3: Claude Code Configuration & Workflows
## TS 3.1: Configure CLAUDE.md Files with Appropriate Hierarchy and Scoping
**Certification Focus**: CCAR-F Domain 3 (20% Exam Weight) | **Scenario Alignment**: Scenario 2 & 5

---

### 🎯 Key Architectural Principles
1. **The 5-Layer Configuration Hierarchy**:
   - Layer 1: **Enterprise Managed Policies** (`managed-policy.json`) - immutable constraints set by system administrators.
   - Layer 2: **User Global Settings** (`~/.claude/CLAUDE.md`) - user-level preferences across all repositories.
   - Layer 3: **Project Root Configuration** (`.claude/CLAUDE.md` or repo `CLAUDE.md`) - repository-wide standards.
   - Layer 4: **Path-Scoped Rules** (`.claude/rules/*.md`) - dynamically loaded conventions based on edited file paths.
   - Layer 5: **Local Invocation Flags** (CLI arguments).
2. **Precedence Contract**: More specific project and path rules extend or override general user rules, but cannot violate enterprise managed policies.
3. **Headless CI Review**: Invoking Claude Code in CI/CD requires `-p` / `--non-interactive` mode and deterministic exit codes."""),

        code_cell("""# Step 1: Environment & Setup
import fnmatch
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 3.1 Claude Code Workflows.")"""),

        markdown_cell("""### 📜 Step 2: Path-Scoped Rules Engine & CI Review Simulator
We define the rule store and implement rule matching and CI review execution."""),

        code_cell("""# Step 2: Rule Matching & CI Simulator
@dataclass
class PathScopedRule:
    rule_name: str
    globs: List[str]
    rule_content: str

    def matches(self, filepath: str) -> bool:
        return any(fnmatch.fnmatch(filepath, pattern) for pattern in self.globs)

RULE_STORE: List[PathScopedRule] = [
    PathScopedRule(
        rule_name="api_conventions",
        globs=["src/api/**/*", "**/api/**/*.py"],
        rule_content="All API handlers must use explicit Pydantic response models and async/await.",
    ),
    PathScopedRule(
        rule_name="test_conventions",
        globs=["**/*.test.*", "tests/**/*.py"],
        rule_content="All tests must use pytest patterns and include docstrings with AAA structure.",
    ),
]

def resolve_active_rules_for_file(filepath: str) -> List[str]:
    \"\"\"Determines which rules apply to a given file path.\"\"\"
    active = []
    for rule in RULE_STORE:
        if rule.matches(filepath):
            active.append(rule.rule_content)
    return active

def simulate_ci_review_execution(git_diff: str, active_rules: List[str], is_non_interactive: bool = True) -> Dict[str, Any]:
    \"\"\"Simulates headless CI audit (-p mode). Fails if interactive input is expected.\"\"\"
    if not is_non_interactive:
        raise RuntimeError("Missing -p flag: CI/CD runners must execute in non-interactive mode!")
    
    findings = []
    if "eval(" in git_diff or "exec(" in git_diff:
        findings.append({
            "severity": "CRITICAL",
            "rule": "SEC001_NO_DYNAMIC_EXECUTION",
            "message": "Dynamic code execution (eval/exec) strictly prohibited in pull requests."
        })
    return {
        "status": "completed",
        "total_findings": len(findings),
        "findings": findings,
        "exit_code": 1 if findings else 0,
    }

print(" Rule matcher and CI reviewer initialized.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Test rule resolution for test vs API files.
2. Simulate CI review of a PR containing dangerous `eval()` code."""),

        code_cell("""# Step 3: Simulation
# 1. Rule Resolution
test_rules = resolve_active_rules_for_file("tests/unit/test_auth.py")
print("Active Rules for test_auth.py:", test_rules)

api_rules = resolve_active_rules_for_file("src/api/v1/orders.py")
print("Active Rules for orders.py:", api_rules)

# 2. CI/CD Audit Simulation
unsafe_diff = \"\"\"
@@ -10,3 +10,4 @@
 def handle_request(raw_code):
+    return eval(raw_code)
\"\"\"
ci_result = simulate_ci_review_execution(unsafe_diff, active_rules=api_rules, is_non_interactive=True)
print("\\nCI Review Result:", json.dumps(ci_result, indent=2))"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Test rules apply only to test paths.
2. API rules apply only to API paths.
3. CI review correctly flags `eval()` as critical with exit code 1.
4. Non-interactive mode enforcement raises RuntimeError if flag is missing."""),

        code_cell("""# Step 4: Verification Checks
assert any("pytest" in r for r in test_rules)
assert any("Pydantic" in r for r in api_rules)

assert ci_result["exit_code"] == 1
assert ci_result["findings"][0]["severity"] == "CRITICAL"

# Verify non-interactive safeguard
try:
    simulate_ci_review_execution(unsafe_diff, api_rules, is_non_interactive=False)
    assert False, "Should have failed without non-interactive mode!"
except RuntimeError as exc:
    assert "Missing -p flag" in str(exc)

print(" All verification assertions passed! Configuration hierarchy verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Know the 5 hierarchy levels: Enterprise > User Global > Project Root > Path Rules > CLI Flags.
- **Rule 2**: Use path-specific rules to conditionally load conventions only when matching files are edited.
- **Rule 3**: In CI/CD pipelines, always pass `-p` / `--non-interactive` to prevent hanging processes."""),
    ]
    return save_notebook("domain3", "ts_3_1_claude_code_workflows", cells)


def build_ts_3_2():
    cells = [
        markdown_cell("""# Domain 3: Claude Code Configuration & Workflows
## TS 3.2: Create and Configure Custom Slash Commands and Skills
**Certification Focus**: CCAR-F Domain 3 (20% Exam Weight) | **Scenario Alignment**: Scenario 2 & 4

---

### 🎯 Key Architectural Principles
1. **Slash Commands**: Declared in `.claude/commands/`. Expand arguments using `$ARGUMENTS` (full argument string), `$1`, `$2` (positional tokens).
2. **Claude Code Skills**: Declared in `.claude/skills/<name>/SKILL.md` with YAML frontmatter:
   - `name`: Unique skill identifier.
   - `description`: When Claude should trigger this skill.
   - `context: fork`: **Crucial architectural setting** that isolates the skill's execution into a separate sub-thread, preventing context bloat in the main session.
   - `allowed-tools`: Restricts which tools the skill may invoke."""),

        code_cell("""# Step 1: Environment & Setup
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 3.2 Slash Commands & Skills.")"""),

        markdown_cell("""### ⚙️ Step 2: Skill & Command Parsers
We implement the parsing of custom slash commands and YAML frontmatter skills."""),

        code_cell("""# Step 2: Command & Skill Parsers
@dataclass
class SkillDefinition:
    name: str
    description: str
    context: str  # 'main' | 'fork'
    allowed_tools: List[str]
    body: str


class SkillCommandParser:
    @staticmethod
    def parse_slash_command(template: str, user_args: str) -> str:
        \"\"\"Replaces $ARGUMENTS and $1, $2 with user-supplied arguments.\"\"\"
        tokens = user_args.strip().split()
        expanded = template.replace(\"$ARGUMENTS\", user_args.strip())
        for i, token in enumerate(tokens, start=1):
            expanded = expanded.replace(f\"${i}\", token)
        return expanded

    @staticmethod
    def parse_skill_markdown(skill_md: str) -> SkillDefinition:
        \"\"\"Parses YAML frontmatter and markdown body from SKILL.md.\"\"\"
        match = re.match(r\"^---\\s*\\n(.*?)\\n---\\s*\\n(.*)$\", skill_md, re.DOTALL)
        if not match:
            raise ValueError(\"Invalid SKILL.md format: missing YAML frontmatter delimiters (---)\")
        
        frontmatter_raw, body = match.groups()
        metadata = {}
        for line in frontmatter_raw.splitlines():
            if \":\" in line:
                k, v = line.split(\":\", 1)
                k, v = k.strip(), v.strip()
                if v.startswith(\"[\") and v.endswith(\"]\"):
                    v = [item.strip() for item in v[1:-1].split(\",\") if item.strip()]
                metadata[k] = v

        return SkillDefinition(
            name=metadata.get(\"name\", \"unnamed\"),
            description=metadata.get(\"description\", \"\"),
            context=metadata.get(\"context\", \"main\"),
            allowed_tools=metadata.get(\"allowed-tools\", []),
            body=body.strip(),
        )


class ClaudeCodeRunner:
    def execute_skill(self, skill: SkillDefinition, target_path: str) -> Dict[str, Any]:
        \"\"\"Executes skill, observing the context: fork isolation contract.\"\"\"
        is_forked = (skill.context == \"fork\")
        return {
            \"skill_name\": skill.name,
            \"execution_mode\": \"forked\" if is_forked else \"main_thread\",
            \"target_path\": target_path,
            \"allowed_tools\": skill.allowed_tools,
            \"main_context_bloat_prevented\": is_forked,
        }

print(\" Command & Skill parser engine initialized.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Test slash command argument expansion (`/deploy branch stage`).
2. Parse a custom skill with `context: fork`.
3. Verify forked execution mode."""),

        code_cell("""# Step 3: Simulation
# 1. Slash Command Expansion
template = \"git checkout $1 && git merge $ARGUMENTS && deploy --env=$2\"
expanded = SkillCommandParser.parse_slash_command(template, \"feature-auth staging\")
print(\"Expanded Command:\", expanded)

# 2. Skill Parsing
sample_skill_md = \"\"\"---
name: security-audit
description: Audits target repository directory for security flaws.
context: fork
allowed-tools: [Read, Grep]
---
Inspect all files for hardcoded credentials and unsafe deserialization.
\"\"\"
skill = SkillCommandParser.parse_skill_markdown(sample_skill_md)
print(f\"\\nParsed Skill: {skill.name} (Context: {skill.context})\")

# 3. Skill Execution
runner = ClaudeCodeRunner()
exec_res = runner.execute_skill(skill, \"src/auth\")
print(\"Skill Execution Result:\", exec_res)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Positional tokens `$1`, `$2` and `$ARGUMENTS` are accurately expanded.
2. YAML frontmatter correctly extracts `context: fork` and `allowed-tools`.
3. Execution mode is `forked` and main context bloat is prevented."""),

        code_cell("""# Step 4: Verification Checks
assert \"git checkout feature-auth\" in expanded
assert \"--env=staging\" in expanded

assert skill.name == \"security-audit\"
assert skill.context == \"fork\"
assert \"Read\" in skill.allowed_tools
assert \"Grep\" in skill.allowed_tools

assert exec_res[\"execution_mode\"] == \"forked\"
assert exec_res[\"main_context_bloat_prevented\"] is True

print(\" All verification assertions passed! Skills and commands verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Set `context: fork` in SKILL.md to execute exploratory/audit tasks without bloating main session context.
- **Rule 2**: Use `$ARGUMENTS` in slash command templates for the entire query string, and `$1`, `$2` for positional tokens.
- **Rule 3**: Restrict `allowed-tools` in skill frontmatter to enforce least privilege."""),
    ]
    return save_notebook("domain3", "ts_3_2_slash_commands_and_skills", cells)


def build_ts_3_3():
    cells = [
        markdown_cell("""# Domain 3: Claude Code Configuration & Workflows
## TS 3.3: Apply Path-Specific Rules for Conditional Convention Loading
**Certification Focus**: CCAR-F Domain 3 (20% Exam Weight) | **Scenario Alignment**: Scenario 2 (Code Generation with Claude Code)

---

### 🎯 Key Architectural Principles
1. **Dynamic Path Scoping**: Instead of packing every project rule into a single bloated `CLAUDE.md`, rules should live in `.claude/rules/<name>.md` with frontmatter `paths: [...]`.
2. **Conditional Convention Loading**: Rules are dynamically loaded into Claude's prompt context **only when** modified or targeted files match the glob patterns.
3. **Preventing Instruction Conflict**: Frontend styling conventions should not pollute backend SQL query development; path scoping ensures domain guidelines remain separated."""),

        code_cell("""# Step 1: Environment & Setup
import fnmatch
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 3.3 Path-Specific Rules.")"""),

        markdown_cell("""### 🎯 Step 2: Rule Engine Implementation
The `RuleEngine` stores rules with glob patterns and returns only instructions applicable to currently touched files."""),

        code_cell("""# Step 2: Scoped Rule Engine
@dataclass
class ScopedRule:
    rule_id: str
    paths: List[str]
    instructions: str

    def matches_files(self, touched_files: List[str]) -> bool:
        for f in touched_files:
            clean_path = f.replace("\\\\", "/")
            for p in self.paths:
                clean_p = p.replace("\\\\", "/")
                if fnmatch.fnmatch(clean_path, clean_p) or fnmatch.fnmatch(clean_path, f"*/{clean_p}"):
                    return True
                if clean_p.endswith("/**"):
                    prefix = clean_p[:-3]
                    if clean_path.startswith(prefix) or f"/{prefix}" in clean_path:
                        return True
        return False


class RuleEngine:
    def __init__(self) -> None:
        self.rules: List[ScopedRule] = []

    def register_rule(self, rule_id: str, raw_markdown: str) -> None:
        paths: List[str] = []
        instructions = raw_markdown
        match = re.match(r"^---\\s*\\n(.*?)\\n---\\s*\\n(.*)$", raw_markdown, re.DOTALL)
        if match:
            frontmatter, instructions = match.groups()
            for line in frontmatter.splitlines():
                line = line.strip()
                if line.startswith("paths:"):
                    continue
                if line.startswith("- "):
                    val = line[2:].replace("'", "").replace('"', "").strip()
                    if val:
                        paths.append(val)
        self.rules.append(ScopedRule(rule_id=rule_id, paths=paths, instructions=instructions.strip()))

    def get_applicable_instructions(self, touched_files: List[str]) -> List[Dict[str, Any]]:
        applicable = []
        for rule in self.rules:
            if rule.matches_files(touched_files):
                applicable.append({
                    "rule_id": rule.rule_id,
                    "scoped_patterns": rule.paths,
                    "instructions": rule.instructions,
                })
        return applicable

print(" Scoped RuleEngine ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We register backend and frontend rules and inspect which instructions activate when different files are touched."""),

        code_cell("""# Step 3: Simulation
engine = RuleEngine()

# Register Backend Rule
engine.register_rule(
    \"backend_api_rule\",
    \"\"\"---
paths:
  - "backend/**"
  - "*.py"
---
Use FastAPI dependency injection and explicit Pydantic response models.
\"\"\"
)

# Register Frontend Rule
engine.register_rule(
    \"frontend_ui_rule\",
    \"\"\"---
paths:
  - "frontend/**"
  - "*.tsx"
---
Use Tailwind CSS classes and React functional components with hooks.
\"\"\"
)

# Scenario A: Editing backend file
backend_active = engine.get_applicable_instructions([\"backend/routers/orders.py\"])
print(\"Active rules for backend/routers/orders.py:\")
for r in backend_active:
    print(f\"  [{r['rule_id']}]: {r['instructions']}\")

# Scenario B: Editing frontend file
frontend_active = engine.get_applicable_instructions([\"frontend/components/Navbar.tsx\"])
print(\"\\nActive rules for frontend/components/Navbar.tsx:\")
for r in frontend_active:
    print(f\"  [{r['rule_id']}]: {r['instructions']}\")"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Backend files activate backend rules and strictly exclude frontend rules.
2. Frontend files activate frontend rules and strictly exclude backend rules."""),

        code_cell("""# Step 4: Verification Checks
backend_ids = [r[\"rule_id\"] for r in backend_active]
assert \"backend_api_rule\" in backend_ids
assert \"frontend_ui_rule\" not in backend_ids

frontend_ids = [r[\"rule_id\"] for r in frontend_active]
assert \"frontend_ui_rule\" in frontend_ids
assert \"backend_api_rule\" not in frontend_ids

print(\" All verification assertions passed! Path-scoped rules validated.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Keep root `CLAUDE.md` concise (<200 lines); offload domain-specific conventions to `.claude/rules/*.md`.
- **Rule 2**: Use glob matching (`paths: ["src/api/**"]`) in frontmatter to conditionally load instructions.
- **Rule 3**: Scoping prevents conflicting instructions between disparate sub-stacks (e.g. frontend vs backend)."""),
    ]
    return save_notebook("domain3", "ts_3_3_path_specific_rules", cells)


def build_ts_3_4():
    cells = [
        markdown_cell("""# Domain 3: Claude Code Configuration & Workflows
## TS 3.4: Determine When to Use Plan Mode vs Direct Execution
**Certification Focus**: CCAR-F Domain 3 (20% Exam Weight) | **Scenario Alignment**: Scenario 2 & 4

---

### 🎯 Key Architectural Principles
1. **Plan Mode Triggers**:
   - Multi-file architectural refactors (>3 files affected).
   - Tasks involving trade-offs between libraries, databases, or protocols.
   - Ambiguous or underspecified requirements.
   - High blast-radius operations where unintended edits would break dependent services.
2. **Direct Execution Triggers**:
   - Single-file isolated bug fixes.
   - Tasks accompanied by explicit stack traces with known root causes.
   - Simple refactors with pre-existing, comprehensive test coverage.
3. **Plan Mode Execution Contract**: In Plan Mode, Claude uses **read-only tools** (`Read`, `Grep`, `Glob`) to explore, formulates a numbered step-by-step plan, and asks the user for explicit approval before modifying code."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 3.4 Plan Mode vs Direct Execution.")"""),

        markdown_cell("""### ⚖️ Step 2: Mode Evaluation Engine & Interview Prompts
We implement the decision logic evaluating whether a task warrants Plan Mode or Direct Execution."""),

        code_cell("""# Step 2: Mode Evaluation Logic
@dataclass
class WorkflowStrategyDecision:
    mode: str  # 'plan_mode' | 'direct_execution'
    rationale: str
    recommended_tools: List[str]


def evaluate_execution_mode(
    file_count_affected: int,
    has_architectural_tradeoffs: bool,
    has_known_stack_trace: bool,
    is_single_function_fix: bool,
) -> WorkflowStrategyDecision:
    \"\"\"Determines whether to trigger Plan Mode vs Direct Execution.\"\"\"
    if has_architectural_tradeoffs or file_count_affected > 3 or (not has_known_stack_trace and not is_single_function_fix):
        return WorkflowStrategyDecision(
            mode=\"plan_mode\",
            rationale=\"Complex task involving multi-file impact or architectural trade-offs requires Plan Mode.\",
            recommended_tools=[\"Read\", \"Grep\", \"Glob\", \"Explore\"],
        )
    return WorkflowStrategyDecision(
        mode=\"direct_execution\",
        rationale=\"Isolated single-file fix with clear stack trace is suitable for Direct Execution.\",
        recommended_tools=[\"Read\", \"Edit\", \"Bash\"],
    )

def build_interview_pattern_prompt(task_description: str) -> str:
    \"\"\"Generates prompt instructing Claude to interview user before planning.\"\"\"
    return (
        f\"You are in Plan Mode for task: '{task_description}'. \"
        \"Do NOT write code or modify files yet. \"
        \"First, interview me by asking 2-3 clarifying questions with concrete trade-off options.\"
    )

print(\" Mode evaluation engine initialized.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Complex refactor -> Plan Mode.
2. Isolated bugfix -> Direct Execution."""),

        code_cell("""# Step 3: Simulation
# Scenario 1: Multi-file caching refactor
dec_plan = evaluate_execution_mode(
    file_count_affected=8,
    has_architectural_tradeoffs=True,
    has_known_stack_trace=False,
    is_single_function_fix=False,
)
print(\"Scenario 1 Mode:\", dec_plan.mode)
print(\"Scenario 1 Rationale:\", dec_plan.rationale)
print(\"Allowed Tools in Plan Mode:\", dec_plan.recommended_tools)

# Scenario 2: Isolated ZeroDivisionError bugfix
dec_direct = evaluate_execution_mode(
    file_count_affected=1,
    has_architectural_tradeoffs=False,
    has_known_stack_trace=True,
    is_single_function_fix=True,
)
print(\"\\nScenario 2 Mode:\", dec_direct.mode)
print(\"Scenario 2 Rationale:\", dec_direct.rationale)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Multi-file refactor strictly routes to Plan Mode with read-only tools.
2. Single-file fix routes to Direct Execution.
3. Interview prompt instructs Claude to interview the user."""),

        code_cell("""# Step 4: Verification Checks
assert dec_plan.mode == \"plan_mode\"
assert \"Explore\" in dec_plan.recommended_tools or \"Read\" in dec_plan.recommended_tools
assert \"Edit\" not in dec_plan.recommended_tools, \"Plan mode must use read-only exploration!\"

assert dec_direct.mode == \"direct_execution\"
assert \"Edit\" in dec_direct.recommended_tools

interview_prompt = build_interview_pattern_prompt(\"Cache layer\")
assert \"interview me\" in interview_prompt

print(\" All verification assertions passed! Mode evaluation verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Use **Plan Mode** for tasks touching >3 files, architectural redesigns, or ambiguous requirements.
- **Rule 2**: In Plan Mode, use **read-only tools** (`Read`, `Grep`, `Glob`) to explore; do not edit files without plan approval.
- **Rule 3**: Use **Direct Execution** only for single-file, low blast-radius bug fixes with clear stack traces."""),
    ]
    return save_notebook("domain3", "ts_3_4_plan_mode_and_refinement", cells)


def build_ts_3_5():
    cells = [
        markdown_cell("""# Domain 3: Claude Code Configuration & Workflows
## TS 3.5: Apply Iterative Refinement and the Interview Pattern
**Certification Focus**: CCAR-F Domain 3 (20% Exam Weight) | **Scenario Alignment**: Scenario 2 & 4

---

### 🎯 Key Architectural Principles
1. **The Interview Pattern**: When a user's prompt is ambiguous or underspecified, the agent must **not** guess or generate speculative code. Instead, it should interview the user with clarifying multiple-choice questions.
2. **Concrete Trade-Off Options**: Each clarifying question should present concrete engineering alternatives (e.g. JWT vs Session tokens, Postgres vs DynamoDB) along with trade-offs.
3. **Grounded Specifications**: After receiving answers, the coordinator compiles a grounded technical specification with explicit acceptance criteria and concrete examples before code generation begins."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 3.5 Iterative Refinement & Interview Pattern.")"""),

        markdown_cell("""### 📋 Step 2: Clarification & Grounded Spec Coordinator
We implement the ambiguity evaluator and specification compiler."""),

        code_cell("""# Step 2: Refinement Coordinator Implementation
@dataclass
class ClarificationQuestion:
    question_id: str
    prompt: str
    options: List[str]


@dataclass
class ArchitectureSpec:
    title: str
    decisions: Dict[str, str]
    concrete_examples: List[str] = field(default_factory=list)


class RefinementCoordinator:
    def evaluate_requirement_clarity(self, raw_requirement: str) -> Tuple[bool, List[ClarificationQuestion]]:
        \"\"\"Detects underspecified requirements and generates clarifying questions.\"\"\"
        questions = []
        lower = raw_requirement.lower()

        if \"auth\" in lower and not any(k in lower for k in [\"jwt\", \"session\", \"oauth\"]):
            questions.append(ClarificationQuestion(
                question_id=\"auth_type\",
                prompt=\"Which authentication mechanism is required?\",
                options=[\"JWT Bearer tokens\", \"Server-side cookie sessions\", \"OAuth2 / OIDC provider\"],
            ))

        if \"database\" in lower or \"store\" in lower:
            if not any(k in lower for k in [\"postgres\", \"sqlite\", \"mongo\", \"redis\"]):
                questions.append(ClarificationQuestion(
                    question_id=\"storage_backend\",
                    prompt=\"Which database storage backend should be configured?\",
                    options=[\"PostgreSQL (SQLAlchemy)\", \"SQLite (Local embedded)\", \"Redis (In-memory)\"],
                ))

        is_ambiguous = len(questions) > 0
        return is_ambiguous, questions

    def formulate_grounded_spec(self, title: str, user_answers: Dict[str, str]) -> ArchitectureSpec:
        \"\"\"Compiles grounded architectural specification with concrete examples.\"\"\"
        examples = [
            f\"API Request Example: Authorization: {user_answers.get('auth_type', 'Bearer <token>')}\",
            f\"Storage Model: Dialect configured for {user_answers.get('storage_backend', 'PostgreSQL')}\",
        ]
        return ArchitectureSpec(title=title, decisions=user_answers, concrete_examples=examples)

print(\" RefinementCoordinator initialized.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Evaluate an ambiguous prompt: "Build an auth service storing records in database".
2. Present clarifying questions.
3. Simulate user selecting options and generate grounded spec."""),

        code_cell("""# Step 3: Simulation
coordinator = RefinementCoordinator()

raw_prompt = \"Build an auth service storing records in database\"
is_ambiguous, questions = coordinator.evaluate_requirement_clarity(raw_prompt)

print(\"Is prompt ambiguous?\", is_ambiguous)
print(f\"Clarifying questions generated: {len(questions)}\")
for q in questions:
    print(f\"  [{q.question_id}]: {q.prompt}\")
    for opt in q.options:
        print(f\"      * {opt}\")

# User answers
user_selections = {
    \"auth_type\": \"JWT Bearer tokens\",
    \"storage_backend\": \"PostgreSQL (SQLAlchemy)\",
}
grounded_spec = coordinator.formulate_grounded_spec(\"Authentication Service Spec\", user_selections)
print(\"\\nGrounded Specification Title:\", grounded_spec.title)
print(\"Decisions:\", grounded_spec.decisions)
print(\"Concrete Examples:\", grounded_spec.concrete_examples)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Ambiguous requirements trigger at least 2 clarifying questions.
2. Grounded specification includes decisions and concrete examples."""),

        code_cell("""# Step 4: Verification Checks
assert is_ambiguous is True
assert len(questions) >= 2
q_ids = [q.question_id for q in questions]
assert \"auth_type\" in q_ids
assert \"storage_backend\" in q_ids

assert grounded_spec.decisions[\"auth_type\"] == \"JWT Bearer tokens\"
assert len(grounded_spec.concrete_examples) == 2

print(\" All verification assertions passed! Interview pattern verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: When requirements lack technical specifics, **interview the user**; do not guess or write speculative code.
- **Rule 2**: Provide multiple-choice options with architectural trade-offs.
- **Rule 3**: Formulate a grounded specification with concrete examples before implementation."""),
    ]
    return save_notebook("domain3", "ts_3_5_iterative_refinement_interview", cells)


def build_ts_3_6():
    cells = [
        markdown_cell("""# Domain 3: Claude Code Configuration & Workflows
## TS 3.6: Integrate Claude Code into CI/CD Pipelines
**Certification Focus**: CCAR-F Domain 3 (20% Exam Weight) | **Scenario Alignment**: Scenario 5 (CI/CD Pipelines)

---

### 🎯 Key Architectural Principles
1. **Headless Execution Contract**: CI/CD pipelines run in non-interactive environments without a human terminal. Claude Code must be invoked with `-p` / `--non-interactive`.
2. **Deterministic Exit Codes**:
   - `Exit Code 0`: PR review completed cleanly; no blocking violations detected.
   - `Exit Code 1`: Blocking violations or security flaws found (`CHANGES_REQUESTED`).
   - `Exit Code 2`: Infrastructure / invocation failure.
3. **Structured Machine-Readable Output**: Audit findings must be emitted as structured JSON for GitHub Actions / GitLab CI comment posting and step-summary reports."""),

        code_cell("""# Step 1: Environment & Setup
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 3.6 CI/CD Pipeline Automation.")"""),

        markdown_cell("""### 🤖 Step 2: Headless CI Runner Implementation
We implement the headless PR auditor that evaluates git patches against security rules and emits exit codes."""),

        code_cell("""# Step 2: Headless CI Auditor
@dataclass
class CIReviewFinding:
    rule_violated: str
    severity: str  # 'CRITICAL' | 'WARNING' | 'INFO'
    file_path: str
    line_snippet: str
    message: str


@dataclass
class CIReviewResult:
    status: str  # 'APPROVED' | 'CHANGES_REQUESTED'
    exit_code: int
    findings: List[CIReviewFinding]


class HeadlessCIRunner:
    def __init__(self, non_interactive: bool = True) -> None:
        self.non_interactive = non_interactive

    def run_pr_audit(self, git_diff_patch: str) -> CIReviewResult:
        if not self.non_interactive:
            raise RuntimeError("CI Runner must be executed with non-interactive=True (-p flag)!")

        findings = []
        for line in git_diff_patch.splitlines():
            clean = line.strip()
            if clean.startswith("+") and not clean.startswith("+++"):
                # Check for dynamic code execution
                if "eval(" in clean or "exec(" in clean:
                    findings.append(CIReviewFinding(
                        rule_violated="SEC001_NO_DYNAMIC_EXEC",
                        severity="CRITICAL",
                        file_path="src/executor.py",
                        line_snippet=clean,
                        message="Dynamic execution functions (eval/exec) are strictly prohibited.",
                    ))
                # Check for hardcoded credentials
                if "sk-ant-" in clean and not any(m in clean for m in ["mock", "test", "dummy"]):
                    findings.append(CIReviewFinding(
                        rule_violated="SEC002_NO_HARDCODED_SECRETS",
                        severity="CRITICAL",
                        file_path="src/config.py",
                        line_snippet=clean,
                        message="Hardcoded Anthropic API token detected in pull request patch.",
                    ))

        has_blocking = any(f.severity == "CRITICAL" for f in findings)
        return CIReviewResult(
            status="CHANGES_REQUESTED" if has_blocking else "APPROVED",
            exit_code=1 if has_blocking else 0,
            findings=findings,
        )

print(" HeadlessCIRunner initialized.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Audit PR patch containing dangerous `eval()`.
2. Audit clean PR patch.
3. Emit structured JSON report."""),

        code_cell("""# Step 3: Simulation
runner = HeadlessCIRunner(non_interactive=True)

# 1. Unsafe patch audit
unsafe_patch = \"\"\"
diff --git a/src/executor.py b/src/executor.py
+    result = eval(user_supplied_str)
\"\"\"
res_unsafe = runner.run_pr_audit(unsafe_patch)
print(\"Unsafe PR Status:\", res_unsafe.status)
print(\"Unsafe PR Exit Code:\", res_unsafe.exit_code)
print(\"Findings:\", [asdict(f) for f in res_unsafe.findings])

# 2. Clean patch audit
clean_patch = \"\"\"
diff --git a/src/math.py b/src/math.py
+    return int(a) + int(b)
\"\"\"
res_clean = runner.run_pr_audit(clean_patch)
print(\"\\nClean PR Status:\", res_clean.status)
print(\"Clean PR Exit Code:\", res_clean.exit_code)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Unsafe patch triggers `CHANGES_REQUESTED` and exit code 1.
2. Clean patch triggers `APPROVED` and exit code 0.
3. Non-interactive flag enforcement prevents terminal hanging."""),

        code_cell("""# Step 4: Verification Checks
assert res_unsafe.exit_code == 1
assert res_unsafe.status == \"CHANGES_REQUESTED\"
assert res_unsafe.findings[0].rule_violated == \"SEC001_NO_DYNAMIC_EXEC\"

assert res_clean.exit_code == 0
assert res_clean.status == \"APPROVED\"
assert len(res_clean.findings) == 0

print(\" All verification assertions passed! CI/CD pipeline automation verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: CI runners must invoke Claude Code with `-p` / `--non-interactive` to prevent hanging on interactive prompts.
- **Rule 2**: Return exit code 1 to fail the CI build when critical security violations are discovered.
- **Rule 3**: Emit findings as structured JSON for automated GitHub PR comment posting."""),
    ]
    return save_notebook("domain3", "ts_3_6_cicd_pipeline_automation", cells)


def main():
    print("=== Generating Domain 3 Notebooks (TS 3.1 - TS 3.6) ===")
    build_ts_3_1()
    build_ts_3_2()
    build_ts_3_3()
    build_ts_3_4()
    build_ts_3_5()
    build_ts_3_6()
    print(" Domain 3 notebooks generated successfully!\n")


if __name__ == "__main__":
    main()
