"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.6: Implement Multi-Instance and Multi-Pass Review Architectures
Exam Scenario 5: Claude Code for Continuous Integration

Key Architectural Concepts:
1. Eliminating author self-affirmation bias by deploying independent review instances.
2. Two-Pass review topology:
   - Pass 1: Local file-level unit review (syntax, edge cases, error boundaries).
   - Pass 2: System-level cross-file integration review (API contracts, data consistency).
3. Synthesis aggregator: Merging, deduplicating, and prioritizing actionable findings.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class ReviewFinding:
    pass_type: str  # "FILE_LOCAL" or "SYSTEM_INTEGRATION"
    severity: str
    target_component: str
    description: str
    suggested_remedy: str


class IndependentReviewerInstance:
    """Simulates an isolated Claude review instance with no generation bias."""

    def __init__(self, reviewer_id: str) -> None:
        self.reviewer_id = reviewer_id

    def review_local_file(self, filename: str, code: str) -> List[ReviewFinding]:
        findings = []
        if "except Exception: pass" in code or "except: pass" in code:
            findings.append(
                ReviewFinding(
                    pass_type="FILE_LOCAL",
                    severity="HIGH",
                    target_component=filename,
                    description="Silent exception swallowing detected",
                    suggested_remedy="Log exception and re-raise or return typed error."
                )
            )
        if "None." in code:
            findings.append(
                ReviewFinding(
                    pass_type="FILE_LOCAL",
                    severity="MEDIUM",
                    target_component=filename,
                    description="Potential NoneType dereference without null guard",
                    suggested_remedy="Add if x is not None check."
                )
            )
        return findings

    def review_system_contracts(self, files: Dict[str, str]) -> List[ReviewFinding]:
        findings = []
        # Check contract between caller and callee
        api_code = files.get("auth_api.py", "")
        client_code = files.get("auth_client.py", "")

        # Caller sends 'auth_token', but API expects 'bearer_token'
        if "auth_token=" in client_code and "bearer_token:" in api_code and "auth_token:" not in api_code:
            findings.append(
                ReviewFinding(
                    pass_type="SYSTEM_INTEGRATION",
                    severity="CRITICAL",
                    target_component="auth_api.py <-> auth_client.py",
                    description="Cross-file parameter name mismatch: client transmits 'auth_token', server expects 'bearer_token'",
                    suggested_remedy="Align parameter naming in OpenAPI / Pydantic schema."
                )
            )
        return findings


class MultiPassReviewPipeline:
    """Orchestrates independent review instances and compiles consensus audit."""

    def __init__(self) -> None:
        self.file_reviewer = IndependentReviewerInstance("reviewer_file_specialist")
        self.integration_reviewer = IndependentReviewerInstance("reviewer_arch_specialist")

    def run_review(self, codebase: Dict[str, str]) -> Dict[str, Any]:
        all_findings: List[ReviewFinding] = []

        # Pass 1: Local file-by-file pass
        for filename, content in codebase.items():
            local_issues = self.file_reviewer.review_local_file(filename, content)
            all_findings.extend(local_issues)

        # Pass 2: System-wide integration pass
        integration_issues = self.integration_reviewer.review_system_contracts(codebase)
        all_findings.extend(integration_issues)

        # Aggregation & deduplication
        criticals = [f for f in all_findings if f.severity == "CRITICAL"]
        highs = [f for f in all_findings if f.severity == "HIGH"]

        return {
            "total_findings": len(all_findings),
            "pass_1_local_count": len([f for f in all_findings if f.pass_type == "FILE_LOCAL"]),
            "pass_2_integration_count": len([f for f in all_findings if f.pass_type == "SYSTEM_INTEGRATION"]),
            "critical_count": len(criticals),
            "approved": len(criticals) == 0 and len(highs) == 0,
            "findings": [f.__dict__ for f in all_findings]
        }


def main() -> None:
    print("=" * 70)
    print("TS 4.6: Multi-Instance & Multi-Pass Review Demo")
    print("=" * 70)

    mock_codebase = {
        "auth_api.py": """
def verify_session(bearer_token: str):
    try:
        return decode(bearer_token)
    except Exception: pass
""",
        "auth_client.py": """
def login_and_fetch():
    return verify_session(auth_token="jwt_sample_value")
"""
    }

    pipeline = MultiPassReviewPipeline()
    report = pipeline.run_review(mock_codebase)

    print("\n[Two-Pass Review Audit Results]:")
    print(f"Total Findings: {report['total_findings']}")
    print(f"Pass 1 (Local): {report['pass_1_local_count']} issues")
    print(f"Pass 2 (Integration): {report['pass_2_integration_count']} issues")
    print(f"Merge Status: {'APPROVED' if report['approved'] else 'BLOCKED'}")
    print("\nDetailed Findings:")
    print(json.dumps(report["findings"], indent=2))


if __name__ == "__main__":
    main()
