"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.5: Apply Iterative Refinement and the Interview Pattern
Exam Scenario 2: Code Generation with Claude Code

Key Architectural Concepts:
1. Ambiguity Detection: Identifying underspecified architectural decisions.
2. Interview Gatekeeper: Halting code generation to present concrete trade-offs to the user.
3. Concrete Input/Output grounding before code writing.
4. Test-driven iteration: Writing verification assertions before code generation.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class ClarificationQuestion:
    question_id: str
    prompt: str
    options: List[str]
    default_recommendation: str


@dataclass
class ArchitectureSpec:
    feature_name: str
    auth_mechanism: str
    storage_backend: str
    concrete_examples: List[Dict[str, Any]] = field(default_factory=list)


class RefinementCoordinator:
    """Orchestrates requirement clarification, concrete I/O grounding, and verification."""

    def __init__(self) -> None:
        self.interview_active: bool = False

    def evaluate_requirement_clarity(self, prompt: str) -> Tuple[bool, List[ClarificationQuestion]]:
        """
        Determines if a user prompt is underspecified.
        Returns (is_ambiguous, clarification_questions).
        """
        questions = []
        lower = prompt.lower()

        # Check for ambiguous auth
        if "auth" in lower and not any(k in lower for k in ["jwt", "session", "oauth", "api_key"]):
            questions.append(
                ClarificationQuestion(
                    question_id="auth_type",
                    prompt="Which authentication mechanism should be implemented?",
                    options=["JWT Bearer tokens", "HttpOnly session cookies", "API key headers"],
                    default_recommendation="JWT Bearer tokens"
                )
            )

        # Check for ambiguous storage
        if ("store" in lower or "database" in lower or "persist" in lower) and not any(k in lower for k in ["postgres", "sqlite", "redis", "dynamo"]):
            questions.append(
                ClarificationQuestion(
                    question_id="storage_backend",
                    prompt="Which persistence backend should be configured?",
                    options=["PostgreSQL (SQLAlchemy)", "SQLite (in-memory/file)", "Redis cache"],
                    default_recommendation="PostgreSQL (SQLAlchemy)"
                )
            )

        is_ambiguous = len(questions) > 0
        return is_ambiguous, questions

    def formulate_grounded_spec(
        self,
        feature_name: str,
        user_selections: Dict[str, str]
    ) -> ArchitectureSpec:
        """Grounds clarified requirements with concrete input/output examples."""
        auth_choice = user_selections.get("auth_type", "JWT Bearer tokens")
        storage_choice = user_selections.get("storage_backend", "PostgreSQL (SQLAlchemy)")

        examples = [
            {
                "scenario": "Valid login request",
                "input": {"username": "alice", "password": "secure_password_123"},
                "expected_output": {"status": 200, "token_type": "Bearer", "expires_in": 3600}
            },
            {
                "scenario": "Invalid credentials",
                "input": {"username": "alice", "password": "wrong_password"},
                "expected_output": {"status": 401, "error": "InvalidCredentials", "retry_allowed": True}
            }
        ]

        return ArchitectureSpec(
            feature_name=feature_name,
            auth_mechanism=auth_choice,
            storage_backend=storage_choice,
            concrete_examples=examples
        )


def main() -> None:
    print("=" * 70)
    print("TS 3.5: Iterative Refinement & Interview Pattern Demo")
    print("=" * 70)

    coordinator = RefinementCoordinator()

    # Step 1: Vague user request
    vague_prompt = "Build a user authentication service with database persistence."
    print(f"\nUser Input: '{vague_prompt}'")

    # Step 2: Ambiguity detection
    is_ambiguous, questions = coordinator.evaluate_requirement_clarity(vague_prompt)
    print(f"Ambiguity Detected: {is_ambiguous}")

    if is_ambiguous:
        print("\n[Interview Pattern Activated] Halting code generation to clarify decisions:")
        user_responses = {}
        for q in questions:
            print(f"  ? {q.prompt}")
            for opt in q.options:
                flag = " (Default)" if opt == q.default_recommendation else ""
                print(f"     - {opt}{flag}")
            user_responses[q.question_id] = q.default_recommendation
        
        # Step 3: Grounded Specification with 2-3 concrete I/O examples
        spec = coordinator.formulate_grounded_spec("AuthService", user_responses)
        print("\n[Grounded Specification Established]:")
        print(f"Auth: {spec.auth_mechanism}")
        print(f"Storage: {spec.storage_backend}")
        print(f"Concrete Examples Provided: {len(spec.concrete_examples)}")
        print(json.dumps(spec.concrete_examples, indent=2))
        print("\nSafe to proceed with Test-Driven Generation!")


if __name__ == "__main__":
    main()
