"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.1: Configure CLAUDE.md files with appropriate hierarchy and scoping
Task Statement 3.3: Apply path-specific rules for conditional convention loading
Task Statement 3.6: Integrate Claude Code into CI/CD pipelines
Exam Scenario 2 & 5: Code Generation & CI/CD Pipelines

Key Exam Concepts Demonstrated:
1. CLAUDE.md Hierarchy: Merging user-level (~/.claude/CLAUDE.md), project-level (.claude/CLAUDE.md),
   and directory-level configurations.
2. Path-scoped rules: Evaluating YAML frontmatter glob patterns (e.g. paths: ["**/*.test.*"])
   to conditionally activate rules only when matching files are edited.
3. CI/CD Non-Interactive Runner: Simulating the -p / --print headless execution with
   --output-format json and --json-schema validation.
"""

import fnmatch
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ==============================================================================
# 1. Path-Specific Rule Matcher Engine (TS 3.3)
# ==============================================================================

@dataclass
class PathScopedRule:
    rule_name: str
    globs: List[str]
    rule_content: str

    def matches(self, filepath: str) -> bool:
        """Evaluates whether this rule applies to a specific file path."""
        for pattern in self.globs:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False


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
    """Returns only the rules that apply to the given file, preventing context bloat."""
    return [r.rule_content for r in RULE_STORE if r.matches(filepath)]


# ==============================================================================
# 2. CI/CD Headless Output Formatter (TS 3.6)
# ==============================================================================

def simulate_ci_review_execution(
    git_diff: str,
    rules_applied: List[str],
    is_non_interactive: bool = True,
) -> Dict[str, Any]:
    """
    Simulates: claude -p --output-format json --json-schema review_schema.json
    - is_non_interactive: True mirrors the mandatory -p / --print flag in CI runners.
    """
    if not is_non_interactive:
        raise RuntimeError("CI runner hung waiting for interactive terminal input! Missing -p flag.")

    findings = []
    if "eval(" in git_diff or "os.system(" in git_diff:
        findings.append({
            "severity": "CRITICAL",
            "file": "main.py",
            "line": 42,
            "message": "Use of unsafe eval/system call detected in diff.",
        })

    return {
        "status": "completed",
        "non_interactive_mode": True,
        "rules_enforced_count": len(rules_applied),
        "total_findings": len(findings),
        "findings": findings,
    }


def main() -> None:
    print("Testing Path-Specific Rule Scoping:")
    test_file = "tests/test_api_auth.py"
    rules = resolve_active_rules_for_file(test_file)
    print(f"File: {test_file}")
    print(f"Active Rules Loaded: {rules}\n")

    print("Simulating CI Execution with -p flag:")
    ci_res = simulate_ci_review_execution("diff --git a/main.py\n+ eval(user_input)", rules)
    print(json.dumps(ci_res, indent=2))


if __name__ == "__main__":
    main()
