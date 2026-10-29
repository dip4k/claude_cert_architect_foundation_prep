"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.1: Establish explicit criteria to reduce false positives
Exam Scenarios 5 (CI review) and 6 (structured extraction)

Intent: show that explicit report/skip categories, concrete severity levels and negative
boundaries beat vague guidance ("be conservative", "only high-confidence"). Everything here is
deterministic and offline. The rule engine is a stand-in for the behaviour a well-written
prompt asks Claude to follow.

Key ideas:
1. VAGUE_PROMPT vs EXPLICIT_PROMPT (before / after).
2. Report categories (bugs, security) vs skip categories (minor style, local patterns).
3. Severity levels grounded in concrete code examples.
4. Negative boundaries: test fixtures and mock keys are not secrets.
5. Temporarily disable a noisy category to restore trust (do not filter by confidence).
6. detected_pattern on every finding so dismissals can be analysed later (see TS 4.4).
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set

REVIEW_MODEL = "claude-sonnet-4-5"

# ------------------------------------------------------------------------------
# 1. Prompt before / after
# ------------------------------------------------------------------------------

VAGUE_PROMPT = "You are a conservative reviewer. Only report high-confidence issues. Be careful."

SEVERITY_RUBRIC: Dict[str, Dict[str, str]] = {
    "CRITICAL": {
        "rule": "Live secret or remote code execution reachable from production code.",
        "example": 'API_KEY = "sk-ant-live..."  /  eval(request.args["cmd"])',
    },
    "HIGH": {
        "rule": "User input reaches a SQL query or shell command without parameterisation.",
        "example": 'cursor.execute(f"SELECT * FROM users WHERE id = {uid}")',
    },
    "MEDIUM": {
        "rule": "Bug that fails on bad input but is not security relevant.",
        "example": "return user.orders  # user may be None",
    },
    "LOW": {
        "rule": "Report only when asked; never block a merge.",
        "example": "missing docstring",
    },
}

REPORT_CATEGORIES: List[str] = [
    "Bugs that change behaviour (null dereference, wrong comparison, swallowed exception)",
    "Security issues (hardcoded live secrets, SQL or command injection)",
]
SKIP_CATEGORIES: List[str] = [
    "Minor style (naming, line length, import order)",
    "Local patterns the team already uses on purpose (e.g. print() in CLI scripts)",
    "Secrets that are obvious mocks in tests/ or fixtures/ (mock_, test_, dummy_ prefixes)",
]


def build_explicit_prompt(
    report: Optional[List[str]] = None,
    skip: Optional[List[str]] = None,
    rubric: Optional[Dict[str, Dict[str, str]]] = None,
) -> str:
    """Render the explicit-criteria review prompt (report list, skip list, severity examples)."""
    report = report if report is not None else REPORT_CATEGORIES
    skip = skip if skip is not None else SKIP_CATEGORIES
    rubric = rubric if rubric is not None else SEVERITY_RUBRIC
    lines = ["Review the diff. Report ONLY these categories:"]
    lines += [f"- {item}" for item in report]
    lines.append("Do NOT report:")
    lines += [f"- {item}" for item in skip]
    lines.append("Severity levels (use exactly these):")
    for level, spec in rubric.items():
        lines.append(f"- {level}: {spec['rule']} Example: {spec['example']}")
    lines.append("For each finding give: location, evidence_quote, rationale, severity.")
    return "\n".join(lines)


# ------------------------------------------------------------------------------
# 2. Rule engine
# ------------------------------------------------------------------------------


@dataclass
class VulnerabilityFinding:
    """One reported issue. detected_pattern lets reviewers analyse dismissed findings later."""

    category: str
    severity: str
    target: str
    evidence: str
    reasoning: str
    detected_pattern: str = ""


class ExplicitCriteriaClassifier:
    """Evaluate code against explicit rules, negative boundaries and a disable list."""

    CATEGORIES: Dict[str, Dict[str, Any]] = {
        "HARDCODED_SECRET": {
            "severity": "CRITICAL",
            "regex": r"(sk-ant-[a-zA-Z0-9_\-]{20,}|AKIA[0-9A-Z]{16})",
            "negative_boundaries": [r"mock_", r"test_", r"dummy", r"placeholder"],
        },
        "SQL_INJECTION": {
            "severity": "HIGH",
            "regex": r"execute\s*\(\s*f[\"'].*?SELECT.*?\{",
            "negative_boundaries": [r"param", r":val", r"\?"],
        },
    }

    def __init__(self, disabled_categories: Optional[Set[str]] = None) -> None:
        # Temporarily disabling a noisy category restores trust while criteria are rewritten.
        self.disabled_categories: FrozenSet[str] = frozenset(disabled_categories or ())

    @staticmethod
    def _is_test_path(file_path: str) -> bool:
        lowered = file_path.lower()
        return "test" in lowered or "fixture" in lowered

    @staticmethod
    def _line_of(code: str, start: int) -> str:
        begin = code.rfind("\n", 0, start) + 1
        end = code.find("\n", start)
        return code[begin : end if end != -1 else len(code)]

    def evaluate_snippet(self, file_path: str, code_content: str) -> List[VulnerabilityFinding]:
        """Return findings; a match is skipped when its own line hits a negative boundary."""
        findings: List[VulnerabilityFinding] = []
        is_test_file = self._is_test_path(file_path)

        for name, rule in self.CATEGORIES.items():
            if name in self.disabled_categories:
                continue
            for match in re.finditer(rule["regex"], code_content):
                line = self._line_of(code_content, match.start())
                negatives: List[str] = rule["negative_boundaries"]
                is_mock = any(re.search(neg, line, re.IGNORECASE) for neg in negatives)
                if is_test_file and name == "HARDCODED_SECRET" and is_mock:
                    continue
                text = match.group(0)
                findings.append(
                    VulnerabilityFinding(
                        category=name,
                        severity=rule["severity"],
                        target=file_path,
                        evidence=text[:40] + ("..." if len(text) > 40 else ""),
                        reasoning=f"Matched explicit rule {name}; no negative boundary applies.",
                        detected_pattern=rule["regex"],
                    )
                )
        return findings


def vague_prompt_flags(code_content: str) -> List[str]:
    """Simulate a vague prompt: anything that looks like a key is flagged, tests included."""
    return re.findall(r"sk-[a-zA-Z0-9_\-]{6,}", code_content)


def main() -> None:
    print("=" * 70)
    print("TS 4.1: Explicit Criteria & False Positive Reduction Demo")
    print("=" * 70)
    print("\nBefore:", VAGUE_PROMPT)
    print("\nAfter:\n" + build_explicit_prompt())

    classifier = ExplicitCriteriaClassifier()
    prod = 'API_KEY = "sk-ant-live0123456789abcdef0123456789"'
    test = 'mock_key = "sk-ant-test_mock_dummy_0123456789"'
    print("\nVague prompt on test file:", len(vague_prompt_flags(test)), "flag(s)")
    print("Explicit on test file:", len(classifier.evaluate_snippet("tests/test_auth.py", test)))
    print("Explicit on prod file:", len(classifier.evaluate_snippet("src/auth/provider.py", prod)))


if __name__ == "__main__":
    main()
