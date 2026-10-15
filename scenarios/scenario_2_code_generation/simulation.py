"""
Scenario 2: Code Generation with Claude Code
End-to-End System Simulation

Weaves Together:
- TS 3.1: CLAUDE.md Hierarchy & Scoping
- TS 3.2: Custom Slash Commands & Skills with 'context: fork'
- TS 3.3: Path-Specific Rules Evaluation
- TS 3.4: Plan Mode vs Direct Execution Decision Criteria
- TS 3.5: Iterative Refinement & The Interview Gatekeeper Pattern
"""

import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class ExecutionMode(str, Enum):
    PLAN_MODE = "PLAN_MODE"          # Architectural, multi-file, or ambiguous refactor
    DIRECT_EXECUTION = "DIRECT_EXEC"  # Single-file, localized, well-scoped bug fix


@dataclass
class CodeGenTask:
    task_id: str
    description: str
    target_files: List[str]
    is_architectural_shift: bool = False


@dataclass
class PlanBlueprint:
    task_id: str
    steps: List[str]
    affected_files: List[str]
    requires_approval: bool = True
    is_approved: bool = False


@dataclass
class CodeGenOutcome:
    mode_selected: ExecutionMode
    injected_path_rules: List[str]
    interview_required: bool
    clarification_options: List[str]
    forked_execution_used: bool
    summary: str
    blueprint: Optional[PlanBlueprint] = None


class ClaudeCodeGenerationEngine:
    """Simulates Claude Code's architectural workflow engine."""

    ENTERPRISE_POLICY = {
        "enforce_proxy": "All outbound requests must route through proxy.corp.internal:8080",
        "forbid_plaintext_secrets": "Strict prohibition of unencrypted keys in any configuration"
    }

    PATH_RULES = {
        "backend_auth": {
            "paths": ["backend/**", "api/**"],
            "instruction": "Enforce async def handlers and validated Pydantic models."
        },
        "frontend_react": {
            "paths": ["frontend/**", "ui/**"],
            "instruction": "Use TypeScript interfaces and React Server Components."
        }
    }

    def evaluate_task(self, task: CodeGenTask) -> CodeGenOutcome:
        # Step 1: Evaluate Path-Scoped Rules
        injected_rules = []
        for rule_id, rule_data in self.PATH_RULES.items():
            for touched in task.target_files:
                for pat in rule_data["paths"]:
                    prefix = pat.replace("/**", "")
                    if touched.startswith(prefix) or f"/{prefix}" in touched:
                        injected_rules.append(rule_id)
                        break

        # Step 2: Determine Execution Mode (Plan Mode vs Direct)
        is_multi_file = len(task.target_files) > 1
        if task.is_architectural_shift or is_multi_file:
            mode = ExecutionMode.PLAN_MODE
        else:
            mode = ExecutionMode.DIRECT_EXECUTION

        # Step 3: Evaluate Ambiguity & The Interview Pattern
        lower_desc = task.description.lower()
        interview_needed = False
        options = []

        if "auth" in lower_desc and not any(k in lower_desc for k in ["jwt", "session", "oauth"]):
            interview_needed = True
            options = ["Option A: JWT Bearer Tokens (Stateless)", "Option B: HttpOnly Session Cookies"]

        if "database" in lower_desc and not any(k in lower_desc for k in ["postgres", "sqlite", "redis"]):
            interview_needed = True
            options.append("Option C: PostgreSQL with SQLAlchemy")

        # Step 4: Forked Execution Simulation & Blueprint Generation
        # If running in plan mode or heavy multi-file migration, use context: fork
        forked = mode == ExecutionMode.PLAN_MODE
        blueprint = self.draft_plan_blueprint(task) if mode == ExecutionMode.PLAN_MODE else None

        summary = (
            f"Activated {mode.value}. Injected rules: {list(set(injected_rules))}. "
            f"Interview required: {interview_needed}."
        )

        return CodeGenOutcome(
            mode_selected=mode,
            injected_path_rules=list(set(injected_rules)),
            interview_required=interview_needed,
            clarification_options=options,
            forked_execution_used=forked,
            summary=summary,
            blueprint=blueprint
        )

    def draft_plan_blueprint(self, task: CodeGenTask) -> PlanBlueprint:
        """Generates a structured, read-only plan blueprint in Plan Mode."""
        steps = [f"Phase {i+1}: Inspect and refactor {f}" for i, f in enumerate(task.target_files)]
        steps.append("Phase Final: Execute test verification suite")
        return PlanBlueprint(
            task_id=task.task_id,
            steps=steps,
            affected_files=task.target_files,
            requires_approval=True,
            is_approved=False
        )

    def approve_plan_blueprint(self, blueprint: PlanBlueprint) -> bool:
        """Gating mechanism: File modifications blocked until blueprint approval."""
        blueprint.is_approved = True
        return blueprint.is_approved


def main() -> None:
    print("=" * 70)
    print("Scenario 2: Code Generation with Claude Code Simulation")
    print("=" * 70)

    engine = ClaudeCodeGenerationEngine()

    # Case 1: Complex Multi-File Migration (Requires Plan Mode + Interview)
    task1 = CodeGenTask(
        task_id="task_jwt_migration",
        description="Migrate user auth system to support token authentication with database persistence",
        target_files=["backend/api/auth.py", "backend/models/user.py", "backend/services/token.py"],
        is_architectural_shift=True
    )
    res1 = engine.evaluate_task(task1)
    print("\nCase 1 (Complex Migration):")
    print(f"Mode: {res1.mode_selected.value}")
    print(f"Injected Rules: {res1.injected_path_rules}")
    print(f"Interview Required: {res1.interview_required}")
    print(f"Clarifications: {res1.clarification_options}")
    print(f"Forked Context: {res1.forked_execution_used}")

    # Case 2: Localized Bug Fix (Direct Execution Mode)
    task2 = CodeGenTask(
        task_id="task_typo_fix",
        description="Fix off-by-one error in pagination loop",
        target_files=["frontend/components/Table.tsx"],
        is_architectural_shift=False
    )
    res2 = engine.evaluate_task(task2)
    print("\nCase 2 (Localized Single-File Fix):")
    print(f"Mode: {res2.mode_selected.value}")
    print(f"Injected Rules: {res2.injected_path_rules}")
    print(f"Interview Required: {res2.interview_required}")


if __name__ == "__main__":
    main()
