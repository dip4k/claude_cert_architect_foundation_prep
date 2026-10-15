"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.1: Establish Explicit Criteria to Reduce False Positives
Exam Scenario 6: Structured Data Extraction & Auditing

Key Architectural Concepts:
1. Avoiding vague heuristics ("be conservative", "flag anything suspicious").
2. Defining explicit categorical inclusion criteria.
3. Supplying negative boundary conditions to filter out benign test fixtures or mocks.
4. Two-pass deterministic classification logic.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class VulnerabilityFinding:
    category: str
    severity: str
    target: str
    evidence: str
    reasoning: str


class ExplicitCriteriaClassifier:
    """
    Evaluates code snippets against explicit rubrics,
    distinguishing true risks from test fixtures and benign patterns.
    """

    CATEGORIES = {
        "HARDCODED_SECRET": {
            "severity": "CRITICAL",
            "regex": r"(sk-ant-[a-zA-Z0-9_\-]{20,}|AKIA[0-9A-Z]{16})",
            "negative_boundaries": [r"mock_", r"test_", r"dummy", r"placeholder"]
        },
        "SQL_INJECTION": {
            "severity": "HIGH",
            "regex": r"execute\s*\(\s*f[\"'].*?SELECT.*?\{",
            "negative_boundaries": [r"param", r":val", r"\?"]
        }
    }

    def evaluate_snippet(self, file_path: str, code_content: str) -> List[VulnerabilityFinding]:
        findings = []
        is_test_file = "test" in file_path.lower() or "fixture" in file_path.lower()

        for category_name, rule in self.CATEGORIES.items():
            pattern = rule["regex"]
            matches = list(re.finditer(pattern, code_content))

            for m in matches:
                matched_text = m.group(0)
                
                # Check negative boundary criteria
                is_negative_boundary = False
                if is_test_file and category_name == "HARDCODED_SECRET":
                    # Explicit rule: Test files using dummy/mock patterns are excluded
                    for neg in rule["negative_boundaries"]:
                        if re.search(neg, code_content, re.IGNORECASE):
                            is_negative_boundary = True
                            break

                if is_negative_boundary:
                    continue  # Filtered by explicit negative boundary!

                findings.append(
                    VulnerabilityFinding(
                        category=category_name,
                        severity=rule["severity"],
                        target=file_path,
                        evidence=matched_text[:40] + ("..." if len(matched_text) > 40 else ""),
                        reasoning=f"Matched explicit rule for {category_name} outside negative boundary conditions."
                    )
                )

        return findings


def main() -> None:
    print("=" * 70)
    print("TS 4.1: Explicit Criteria & False Positive Reduction Demo")
    print("=" * 70)

    classifier = ExplicitCriteriaClassifier()

    # Case A: Production file with actual secret
    prod_code = 'API_KEY = "sk-ant-live0123456789abcdef0123456789"\nquery = "SELECT * FROM users"'
    findings_prod = classifier.evaluate_snippet("src/auth/provider.py", prod_code)

    print("\n1. Production Code Evaluation:")
    print(f"File: src/auth/provider.py -> Findings: {len(findings_prod)}")
    for f in findings_prod:
        print(f"   [{f.severity}] {f.category} -> {f.evidence}")

    # Case B: Test file with mock secret (should NOT be flagged!)
    test_code = 'mock_key = "sk-ant-test_mock_dummy_0123456789"\ndef test_login(): pass'
    findings_test = classifier.evaluate_snippet("tests/test_auth.py", test_code)

    print("\n2. Test Code Evaluation (Negative Boundary):")
    print(f"File: tests/test_auth.py -> Findings: {len(findings_test)}")
    if len(findings_test) == 0:
        print("   ✅ Explicit negative boundary correctly prevented false positive on test mock!")


if __name__ == "__main__":
    main()
