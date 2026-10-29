"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.5: Apply iterative refinement techniques for progressive improvement
Exam Scenario 2: Code Generation with Claude Code

Offline simulation (no API calls). Key exam concepts:
1. Interview pattern: ask questions first so hidden considerations surface.
2. Concrete input/output examples (2-3) when prose is interpreted inconsistently.
3. Test-driven iteration: write tests first, then share the failures.
4. One message for interacting problems; sequential messages for independent ones.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class ClarificationQuestion:
    question_id: str
    prompt: str
    options: list[str]
    default_recommendation: str


@dataclass
class ArchitectureSpec:
    feature_name: str
    auth_mechanism: str
    storage_backend: str
    concrete_examples: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class Issue:
    """A problem to report. `touches` names the components the fix would change."""

    issue_id: str
    touches: frozenset[str]


def group_feedback(issues: list[Issue]) -> list[list[str]]:
    """
    Issues that share a component interact, so they go in ONE message.
    Independent issues get their own message, fixed one after another.
    """
    groups: list[tuple[set[str], list[str]]] = []
    for issue in issues:
        merged_parts = set(issue.touches)
        merged_ids = [issue.issue_id]
        remaining: list[tuple[set[str], list[str]]] = []
        for parts, ids in groups:
            if parts & merged_parts:
                merged_parts |= parts
                merged_ids = ids + merged_ids
            else:
                remaining.append((parts, ids))
        groups = remaining + [(merged_parts, merged_ids)]
    return [ids for _, ids in groups]


def format_test_failure_feedback(failures: list[str]) -> str:
    """Test-driven iteration: hand Claude the failing test output, not a vague complaint."""
    lines = ["These tests fail. Fix the code so they pass without editing the tests:"]
    lines.extend(f"- {failure}" for failure in failures)
    return "\n".join(lines)


class RefinementCoordinator:
    """Orchestrates requirement clarification and concrete I/O grounding."""

    def __init__(self) -> None:
        self.interview_active: bool = False

    def evaluate_requirement_clarity(
        self, prompt: str
    ) -> tuple[bool, list[ClarificationQuestion]]:
        """Returns (is_ambiguous, clarification_questions) for an underspecified prompt."""
        questions = []
        lower = prompt.lower()

        if "auth" in lower and not any(k in lower for k in ["jwt", "session", "oauth", "api_key"]):
            questions.append(
                ClarificationQuestion(
                    question_id="auth_type",
                    prompt="Which authentication mechanism should be implemented?",
                    options=["JWT Bearer tokens", "HttpOnly session cookies", "API key headers"],
                    default_recommendation="JWT Bearer tokens",
                )
            )

        mentions_storage = any(k in lower for k in ["store", "database", "persist"])
        names_backend = any(k in lower for k in ["postgres", "sqlite", "redis", "dynamo"])
        if mentions_storage and not names_backend:
            questions.append(
                ClarificationQuestion(
                    question_id="storage_backend",
                    prompt="Which persistence backend should be configured?",
                    options=["PostgreSQL (SQLAlchemy)", "SQLite (in-memory/file)", "Redis cache"],
                    default_recommendation="PostgreSQL (SQLAlchemy)",
                )
            )

        return len(questions) > 0, questions

    def formulate_grounded_spec(
        self, feature_name: str, user_selections: dict[str, str]
    ) -> ArchitectureSpec:
        """Grounds clarified requirements with concrete input/output examples."""
        examples = [
            {
                "scenario": "Valid login request",
                "input": {"username": "alice", "password": "secure_password_123"},
                "expected_output": {"status": 200, "token_type": "Bearer", "expires_in": 3600},
            },
            {
                "scenario": "Invalid credentials",
                "input": {"username": "alice", "password": "wrong_password"},
                "expected_output": {"status": 401, "error": "InvalidCredentials"},
            },
        ]
        return ArchitectureSpec(
            feature_name=feature_name,
            auth_mechanism=user_selections.get("auth_type", "JWT Bearer tokens"),
            storage_backend=user_selections.get("storage_backend", "PostgreSQL (SQLAlchemy)"),
            concrete_examples=examples,
        )


def main() -> None:
    print("=" * 70)
    print("TS 3.5: Iterative Refinement & Interview Pattern Demo")
    print("=" * 70)

    coordinator = RefinementCoordinator()
    vague_prompt = "Build a user authentication service with database persistence."
    print(f"\nUser input: {vague_prompt!r}")
    is_ambiguous, questions = coordinator.evaluate_requirement_clarity(vague_prompt)
    print(f"Ambiguous: {is_ambiguous}")

    answers: dict[str, str] = {}
    for q in questions:
        print(f"  ? {q.prompt}  options={q.options}")
        answers[q.question_id] = q.default_recommendation
    spec = coordinator.formulate_grounded_spec("AuthService", answers)
    print(f"Spec: auth={spec.auth_mechanism}, storage={spec.storage_backend}")
    print(json.dumps(spec.concrete_examples, indent=2))

    issues = [
        Issue("token-payload", frozenset({"auth", "router"})),
        Issue("router-order", frozenset({"router"})),
        Issue("css-padding", frozenset({"dashboard"})),
    ]
    print("\nFeedback messages to send:", group_feedback(issues))


if __name__ == "__main__":
    main()
