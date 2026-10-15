"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.6: Integrate Claude Code into CI/CD Pipelines
Exam Scenario 5: Claude Code for Continuous Integration

Key Architectural Concepts:
1. Non-interactive headless execution (-p / --print).
2. Machine-readable output formats (--output-format json, --json-schema).
3. Ephemeral execution environments without cross-run session contamination.
4. Deterministic exit codes (0 for pass, 1 for block) for pipeline gatekeeping.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class CIReviewFinding:
    severity: str  # "CRITICAL", "WARNING", "INFO"
    file: str
    line: int
    rule_violated: str
    description: str
    suggested_fix: str


@dataclass
class CIReviewResult:
    status: str  # "APPROVED", "CHANGES_REQUESTED"
    exit_code: int
    summary: str
    findings: List[CIReviewFinding] = field(default_factory=list)


class HeadlessCIRunner:
    """Simulates headless non-interactive Claude Code execution in CI."""

    CI_SCHEMA = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["APPROVED", "CHANGES_REQUESTED"]},
            "summary": {"type": "string"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["CRITICAL", "WARNING", "INFO"]},
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "rule_violated": {"type": "string"},
                        "description": {"type": "string"},
                        "suggested_fix": {"type": "string"}
                    },
                    "required": ["severity", "file", "line", "rule_violated", "description", "suggested_fix"]
                }
            }
        },
        "required": ["status", "summary", "findings"]
    }

    def __init__(self, non_interactive: bool = True, output_format: str = "json") -> None:
        self.non_interactive = non_interactive
        self.output_format = output_format

    def run_pr_audit(self, pr_diff: str) -> CIReviewResult:
        """
        Executes headless audit on PR diff and produces structured outcome.
        Enforces exit code 1 if any CRITICAL finding is detected.
        """
        if not self.non_interactive:
            raise RuntimeError("Interactive mode (-p omitted) is not allowed in CI runners!")

        findings: List[CIReviewFinding] = []

        # Simulated lint / security scanning logic
        if "eval(" in pr_diff or "os.system(" in pr_diff:
            findings.append(
                CIReviewFinding(
                    severity="CRITICAL",
                    file="auth/eval_handler.py",
                    line=42,
                    rule_violated="SEC001_NO_DYNAMIC_EXEC",
                    description="Detected unsafe dynamic evaluation via eval()",
                    suggested_fix="Use ast.literal_eval() or a strict JSON parser."
                )
            )

        if "print(" in pr_diff:
            findings.append(
                CIReviewFinding(
                    severity="WARNING",
                    file="auth/eval_handler.py",
                    line=15,
                    rule_violated="LOG002_NO_RAW_PRINTS",
                    description="Direct print() statement found in production code",
                    suggested_fix="Use logger.info() or logger.debug()."
                )
            )

        has_critical = any(f.severity == "CRITICAL" for f in findings)
        status = "CHANGES_REQUESTED" if has_critical else "APPROVED"
        exit_code = 1 if has_critical else 0
        summary = (
            f"CI Audit failed with {len(findings)} issues ({len([f for f in findings if f.severity == 'CRITICAL'])} critical)."
            if has_critical else "CI Audit passed cleanly."
        )

        return CIReviewResult(status=status, exit_code=exit_code, summary=summary, findings=findings)


def main() -> None:
    print("=" * 70)
    print("TS 3.6: CI/CD Pipeline Automation & Headless Execution Demo")
    print("=" * 70)

    # Invocation flags: claude -p "Audit PR" --output-format json
    runner = HeadlessCIRunner(non_interactive=True, output_format="json")

    mock_pr_diff = """
    @@ -10,3 +10,6 @@ def process_user_input(payload):
    +    print("Processing payload...")
    +    result = eval(payload.get("expression"))
    +    return result
    """

    print("\nRunning simulated non-interactive CI audit (flag: -p, format: json)...")
    res = runner.run_pr_audit(mock_pr_diff)

    # Format output as JSON for pipeline artifact
    json_output = {
        "status": res.status,
        "exit_code": res.exit_code,
        "summary": res.summary,
        "findings": [f.__dict__ for f in res.findings]
    }

    print(json.dumps(json_output, indent=2))
    print(f"\nPipeline Process Exit Code: {res.exit_code}")
    if res.exit_code != 0:
        print("[CI Pipeline Blocked]: Merging prevented until critical findings are resolved.")
    else:
        print("[CI Pipeline Passed]: Pull request approved for merge.")


if __name__ == "__main__":
    main()
