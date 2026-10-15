"""
Scenario 5: Claude Code for Continuous Integration (CI/CD)
End-to-End System Simulation

Weaves Together:
- TS 3.6: CI/CD Pipeline Automation (Non-interactive -p, --output-format json, --json-schema)
- TS 4.1: Explicit Criteria & False Positive Filtering (Negative boundaries)
- TS 4.5: Real-Time vs Message Batches API Decision Engine
- TS 4.6: Multi-Instance & Two-Pass Review Pipeline (Local pass + Integration pass)
"""

import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class WorkloadType(str, Enum):
    BLOCKING_PR_CHECK = "BLOCKING_PR_CHECK"      # Requires Real-Time API (Seconds)
    OVERNIGHT_REPO_AUDIT = "OVERNIGHT_AUDIT"      # Eligible for Message Batches API (24h, 50% discount)


@dataclass
class CIPipelineFinding:
    pass_number: int  # 1 = Local, 2 = Integration
    severity: str    # "CRITICAL", "HIGH", "WARNING", "INFO"
    file: str
    rule_id: str
    description: str


@dataclass
class CIPipelineReport:
    workload: WorkloadType
    api_chosen: str  # "REALTIME_MESSAGES" or "MESSAGE_BATCHES"
    exit_code: int   # 0 = Pass/Merge Approved, 1 = Blocked
    status: str      # "APPROVED", "CHANGES_REQUESTED"
    findings: List[CIPipelineFinding] = field(default_factory=list)


class ContinuousIntegrationEngine:
    """Simulates automated CI/CD code review with two-pass architecture."""

    def __init__(self, headless_flag_present: bool = True) -> None:
        self.headless = headless_flag_present

    def route_api_for_workload(self, workload: WorkloadType) -> str:
        """Enforces the critical exam rule: Never use Batch API for blocking PR checks."""
        if workload == WorkloadType.BLOCKING_PR_CHECK:
            return "REALTIME_MESSAGES"  # Fast synchronous response
        elif workload == WorkloadType.OVERNIGHT_REPO_AUDIT:
            return "MESSAGE_BATCHES"    # 50% discount, 24h window
        return "REALTIME_MESSAGES"

    def run_two_pass_review(
        self,
        pr_files: Dict[str, str],
        workload: WorkloadType = WorkloadType.BLOCKING_PR_CHECK
    ) -> CIPipelineReport:
        if not self.headless:
            raise RuntimeError(
                "Execution failed: Claude Code requires the '-p' / '--print' flag "
                "in automated CI environments to prevent interactive input blocking."
            )

        api_chosen = self.route_api_for_workload(workload)
        findings: List[CIPipelineFinding] = []

        # Pass 1: Local File-Level Review (Syntax, null checks, secrets outside test files)
        for filepath, content in pr_files.items():
            # Check for hardcoded secret outside test files (Negative boundary rule)
            is_test_file = "test" in filepath.lower()
            if "sk-ant-live" in content and not is_test_file:
                findings.append(
                    CIPipelineFinding(
                        pass_number=1,
                        severity="CRITICAL",
                        file=filepath,
                        rule_id="SEC_001_HARDCODED_KEY",
                        description="Plaintext production API key detected in source code."
                    )
                )

            # Check for silent exception swallowing
            if "except:" in content or "except Exception: pass" in content:
                findings.append(
                    CIPipelineFinding(
                        pass_number=1,
                        severity="HIGH",
                        file=filepath,
                        rule_id="ERR_002_SILENT_EXCEPTION",
                        description="Bare except clause silently swallows runtime errors."
                    )
                )

        # Pass 2: System-Level Cross-File Integration Review (API contract consistency)
        api_code = pr_files.get("api/routes.py", "")
        client_code = pr_files.get("client/sdk.py", "")
        if "auth_token=" in client_code and "bearer_token:" in api_code and "auth_token:" not in api_code:
            findings.append(
                CIPipelineFinding(
                    pass_number=2,
                    severity="CRITICAL",
                    file="client/sdk.py <-> api/routes.py",
                    rule_id="ARCH_003_CONTRACT_MISMATCH",
                    description="Cross-file parameter drift: client sends 'auth_token', route expects 'bearer_token'."
                )
            )

        # Generalized cross-file method deletion vs caller references with namespace awareness
        for provider_path, provider_content in pr_files.items():
            deleted_methods = re.findall(r"^-\s*def\s+([a-zA-Z_]\w*)\s*\(", provider_content, flags=re.MULTILINE)
            namespace_match = re.search(r"class\s+([a-zA-Z_]\w*)", provider_content)
            namespace = namespace_match.group(1) if namespace_match else Path(provider_path).stem

            for deleted_method in deleted_methods:
                for caller_path, caller_content in pr_files.items():
                    if caller_path == provider_path:
                        continue
                    call_patterns = [
                        rf"\b{namespace}\.{deleted_method}\s*\(",
                        rf"\b{deleted_method}\s*\("
                    ]
                    if any(re.search(pat, caller_content) for pat in call_patterns):
                        added_in_caller = re.search(rf"^\+\s*def\s+{deleted_method}\s*\(", caller_content, flags=re.MULTILINE)
                        if not added_in_caller:
                            findings.append(
                                CIPipelineFinding(
                                    pass_number=2,
                                    severity="HIGH",
                                    file=f"{provider_path} <-> {caller_path}",
                                    rule_id="ARCH_004_BREAKING_DELETION",
                                    description=(
                                        f"Breaking API change: Method '{deleted_method}' deleted from {provider_path} "
                                        f"({namespace}) while still invoked in {caller_path}."
                                    )
                                )
                            )

        # Evaluate Gatekeeper Outcome
        has_blocking_issues = any(f.severity in ("CRITICAL", "HIGH") for f in findings)
        exit_code = 1 if has_blocking_issues else 0
        status = "CHANGES_REQUESTED" if has_blocking_issues else "APPROVED"

        return CIPipelineReport(
            workload=workload,
            api_chosen=api_chosen,
            exit_code=exit_code,
            status=status,
            findings=findings
        )


def main() -> None:
    print("=" * 70)
    print("Scenario 5: Claude Code for Continuous Integration Simulation")
    print("=" * 70)

    engine = ContinuousIntegrationEngine(headless_flag_present=True)

    sample_pr = {
        "api/routes.py": "def handle_payment(bearer_token: str):\n    try: pass\n    except Exception: pass",
        "client/sdk.py": "def submit(): return handle_payment(auth_token='xyz')",
        "tests/test_api.py": "mock_key = 'sk-ant-live_fake_for_testing_only'"  # Negative boundary: shouldn't trigger
    }

    report = engine.run_two_pass_review(sample_pr, WorkloadType.BLOCKING_PR_CHECK)

    print(f"\nWorkload Type: {report.workload.value}")
    print(f"API Target Selected: {report.api_chosen}")
    print(f"Pipeline Merge Decision: {report.status} (Exit Code: {report.exit_code})")

    print("\nDetailed Two-Pass Findings:")
    for f in report.findings:
        print(f"  [Pass {f.pass_number}] [{f.severity}] {f.file} -> {f.rule_id}: {f.description}")

    # Verify Batch API rule for overnight workload
    overnight_api = engine.route_api_for_workload(WorkloadType.OVERNIGHT_REPO_AUDIT)
    print(f"\nOvernight Audit API Target: {overnight_api} (50% Cost Savings)")


if __name__ == "__main__":
    main()
