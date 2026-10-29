"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.6: Integrate Claude Code into CI/CD Pipelines
Exam Scenario 5: Claude Code for Continuous Integration

Offline simulation (no API calls, no `claude` process is started). Key exam concepts:
1. `-p` / `--print` runs Claude Code non-interactively; without it a CI job hangs.
   (`CLAUDE_HEADLESS` and `--batch` do not exist.)
2. `--output-format json` with `--json-schema` gives machine-parseable findings that a script
   can post as inline PR comments. Exit codes come from YOUR gate script reading that JSON.
3. CLAUDE.md supplies testing standards and review criteria to the CI instance.
4. Use an independent review instance; on re-runs pass prior findings and ask for new issues only.
5. Message Batches API suits overnight jobs, not blocking pre-merge checks (see domain4 TS 4.5).
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SEVERITIES = ("CRITICAL", "WARNING", "INFO")
BLOCKING_SEVERITIES = ("CRITICAL",)


# ==============================================================================
# 1. CI command builder (always non-interactive, always machine-readable)
# ==============================================================================


def build_ci_command(prompt: str, json_schema: str, output_format: str = "json") -> list[str]:
    """
    Builds the argv for a CI review: always `-p`, always `--output-format`, and
    `--json-schema` whenever the format is json. `json_schema` is the schema as an inline JSON
    string (the flag takes inline JSON, not a file path); it must parse as a JSON object.
    """
    if output_format != "json":
        raise ValueError("CI reviews must use --output-format json for parseable findings")
    if not json_schema:
        raise ValueError("--json-schema value is required with --output-format json")
    try:
        parsed = json.loads(json_schema)
    except json.JSONDecodeError as exc:
        raise ValueError("--json-schema takes inline JSON, not a file path") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--json-schema must be a JSON object")
    return ["claude", "-p", prompt, "--output-format", output_format, "--json-schema", json_schema]


def validate_ci_command(argv: list[str]) -> list[str]:
    """Returns the problems found in a CI command (empty list means OK)."""
    problems: list[str] = []
    if "-p" not in argv and "--print" not in argv:
        problems.append("missing -p/--print: the job will hang waiting for interactive input")
    if "--output-format" not in argv:
        problems.append("missing --output-format json: output is not machine-parseable")
    if "--output-format" in argv and "--json-schema" not in argv:
        problems.append("missing --json-schema: findings may not match the expected shape")
    return problems


def build_rerun_prompt(base_prompt: str, prior_findings: list[dict[str, Any]]) -> str:
    """Re-runs include earlier findings and ask only for new or unaddressed issues."""
    if not prior_findings:
        return base_prompt
    listed = "\n".join(
        f"- {f['file']}:{f['line']} {f['rule_violated']}: {f['description']}"
        for f in prior_findings
    )
    return (
        f"{base_prompt}\n\nPrior findings from earlier runs:\n{listed}\n"
        "Report only NEW issues or prior findings that are still unaddressed."
    )


def build_test_generation_prompt(task: str, existing_test_files: list[str]) -> str:
    """Give the CI instance the existing tests so it does not generate duplicates."""
    files = "\n".join(f"- {name}" for name in existing_test_files)
    return f"{task}\n\nExisting test files (do not duplicate their coverage):\n{files}"


# ==============================================================================
# 2. Findings: schema, validation, inline comments, gating
# ==============================================================================


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
    findings: list[CIReviewFinding] = field(default_factory=list)


CI_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["APPROVED", "CHANGES_REQUESTED"]},
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "rule_violated": {"type": "string"},
                    "description": {"type": "string"},
                    "suggested_fix": {"type": "string"},
                },
                "required": [
                    "severity",
                    "file",
                    "line",
                    "rule_violated",
                    "description",
                    "suggested_fix",
                ],
            },
        },
    },
    "required": ["status", "summary", "findings"],
}


def validate_findings_payload(payload: dict[str, Any]) -> list[str]:
    """Minimal stdlib check of a review payload against CI_SCHEMA. Empty list means valid."""
    problems = [f"missing key: {k}" for k in CI_SCHEMA["required"] if k not in payload]
    if payload.get("status") not in CI_SCHEMA["properties"]["status"]["enum"]:
        problems.append("status must be APPROVED or CHANGES_REQUESTED")
    item_schema = CI_SCHEMA["properties"]["findings"]["items"]
    for i, finding in enumerate(payload.get("findings", [])):
        problems.extend(
            f"findings[{i}] missing key: {k}" for k in item_schema["required"] if k not in finding
        )
        if finding.get("severity") not in SEVERITIES:
            problems.append(f"findings[{i}] severity must be one of {SEVERITIES}")
        if not isinstance(finding.get("line"), int):
            problems.append(f"findings[{i}] line must be an integer")
    return problems


def findings_to_inline_comments(findings: list[CIReviewFinding]) -> list[dict[str, Any]]:
    """Maps findings to inline PR comments (file, line, body) for a CI script to post."""
    return [
        {
            "path": f.file,
            "line": f.line,
            "body": f"[{f.severity}] {f.rule_violated}: {f.description} Fix: {f.suggested_fix}",
        }
        for f in findings
    ]


def gate_exit_code(findings: list[CIReviewFinding]) -> int:
    """The gate script returns 1 when any blocking finding exists, else 0."""
    return 1 if any(f.severity in BLOCKING_SEVERITIES for f in findings) else 0


class HeadlessCIRunner:
    """Simulates the review step of a non-interactive CI job (no real model call)."""

    CI_SCHEMA = CI_SCHEMA

    def __init__(self, non_interactive: bool = True, output_format: str = "json") -> None:
        self.non_interactive = non_interactive
        self.output_format = output_format

    def run_pr_audit(self, pr_diff: str) -> CIReviewResult:
        """Scans a diff with simple string checks and applies the gate."""
        if not self.non_interactive:
            raise RuntimeError("Interactive mode (-p omitted) is not allowed in CI runners!")

        findings: list[CIReviewFinding] = []
        if "eval(" in pr_diff or "os.system(" in pr_diff:
            findings.append(
                CIReviewFinding(
                    severity="CRITICAL",
                    file="auth/eval_handler.py",
                    line=42,
                    rule_violated="SEC001_NO_DYNAMIC_EXEC",
                    description="Detected unsafe dynamic evaluation via eval()",
                    suggested_fix="Use ast.literal_eval() or a strict JSON parser.",
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
                    suggested_fix="Use logger.info() or logger.debug().",
                )
            )

        exit_code = gate_exit_code(findings)
        critical = sum(1 for f in findings if f.severity == "CRITICAL")
        summary = (
            f"CI Audit failed with {len(findings)} issues ({critical} critical)."
            if exit_code
            else "CI Audit passed cleanly."
        )
        status = "CHANGES_REQUESTED" if exit_code else "APPROVED"
        return CIReviewResult(status, exit_code, summary, findings)


def main() -> None:
    print("=" * 70)
    print("TS 3.6: CI/CD Pipeline Demo (offline simulation)")
    print("=" * 70)

    argv = build_ci_command("Review this PR diff against CLAUDE.md criteria", ".ci/review.json")
    print("\nCommand:", " ".join(argv))
    print("Problems:", validate_ci_command(argv))
    print("Bad command problems:", validate_ci_command(["claude", "Review PR"]))

    diff = '+    print("Processing payload...")\n+    result = eval(payload.get("expression"))'
    result = HeadlessCIRunner().run_pr_audit(diff)
    payload = {
        "status": result.status,
        "summary": result.summary,
        "findings": [f.__dict__ for f in result.findings],
    }
    print("\nPayload problems:", validate_findings_payload(payload))
    print(json.dumps(payload, indent=2))
    print("\nInline comments:", json.dumps(findings_to_inline_comments(result.findings), indent=2))
    print(f"\nGate exit code: {result.exit_code}")
    print("\nRe-run prompt:\n" + build_rerun_prompt("Review the diff.", payload["findings"]))


if __name__ == "__main__":
    main()
