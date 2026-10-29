"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.2: Apply few-shot prompting to improve output consistency and quality
(Also hosts the small independent-reviewer payload helper that TS 4.6 builds on.)
Exam Scenarios 5 (CI review) and 6 (structured extraction)

Intent: show 2-4 targeted examples that explain WHY an action was chosen, fix the exact output
format, separate acceptable patterns from genuine issues, and cover varied document layouts
and empty/null fields. All offline; no API calls.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

MIN_EXAMPLES = 2
MAX_EXAMPLES = 4


@dataclass
class FewShotExample:
    scenario_input: str
    decision_reasoning: str
    target_output: Dict[str, Any]


# Extraction examples: arithmetic conflict and an empty/null case.
FEW_SHOT_EXTRACTION_EXAMPLES: List[FewShotExample] = [
    FewShotExample(
        scenario_input=(
            "Consulting invoice stating total $500, but line items only list 4 hrs @ $100 = $400."
        ),
        decision_reasoning=(
            "Line items total ($400) differs from stated total ($500). "
            "Report both numbers and set conflict_detected true instead of picking one."
        ),
        target_output={
            "stated_total": 500.0,
            "calculated_total": 400.0,
            "conflict_detected": True,
            "items": [{"desc": "Consulting", "total": 400.0}],
        },
    ),
    FewShotExample(
        scenario_input="Purchase order omitting tax number and payment due date.",
        decision_reasoning="The document has no due_date or tax_id. Return null, never invent.",
        target_output={
            "stated_total": 120.0,
            "due_date": None,
            "tax_id": None,
            "conflict_detected": False,
        },
    ),
]

# Varied structure: inline citations vs a bibliography at the end.
VARIED_STRUCTURE_EXAMPLES: List[FewShotExample] = [
    FewShotExample(
        scenario_input="Paper text: '... as shown by Lee (2021, p. 4) the effect is small.'",
        decision_reasoning="Citation is inline, so read author and year from the sentence.",
        target_output={"citations": [{"author": "Lee", "year": 2021, "page": 4}]},
    ),
    FewShotExample(
        scenario_input="Paper ends with 'References: [1] Kim, J. (2019). Deep Nets. Journal X.'",
        decision_reasoning="Citation is in a bibliography. Read the reference list, not the body.",
        target_output={"citations": [{"author": "Kim", "year": 2019, "page": None}]},
    ),
    FewShotExample(
        scenario_input="Short memo with no citations at all.",
        decision_reasoning="Nothing to extract. Return an empty list, not a made-up citation.",
        target_output={"citations": []},
    ),
]

# Review examples: show the exact format and WHY a pattern is acceptable or a genuine issue.
REVIEW_FORMAT = "location | issue | severity | suggested_fix"

REVIEW_FEW_SHOT_EXAMPLES: List[FewShotExample] = [
    FewShotExample(
        scenario_input="tests/test_auth.py:12  mock_key = 'sk-ant-test_dummy_000000000000'",
        decision_reasoning="ACCEPTABLE: mock key in a test file. It is not a live credential.",
        target_output={"report": False},
    ),
    FewShotExample(
        scenario_input="src/auth.py:30  user = db.get(uid); return user.orders",
        decision_reasoning="GENUINE: get() can return None, so .orders raises AttributeError.",
        target_output={
            "location": "src/auth.py:30",
            "issue": "possible None dereference",
            "severity": "MEDIUM",
            "suggested_fix": "if user is None: raise UserNotFound(uid)",
        },
    ),
]


def validate_example_count(examples: List[FewShotExample]) -> None:
    """Raise ValueError unless 2-4 examples are supplied (the targeted-few-shot rule)."""
    if not MIN_EXAMPLES <= len(examples) <= MAX_EXAMPLES:
        raise ValueError(f"Use {MIN_EXAMPLES}-{MAX_EXAMPLES} examples, got {len(examples)}.")


def render_few_shot_prompt_block(examples: List[FewShotExample]) -> str:
    """Render 2-4 targeted examples; each one states the reasoning behind the output."""
    validate_example_count(examples)
    lines = ["### FEW-SHOT REASONING EXAMPLES:"]
    for idx, ex in enumerate(examples, start=1):
        lines.append(f"\n--- Example {idx} ---")
        lines.append(f"Input: {ex.scenario_input}")
        lines.append(f"Architectural Reasoning: {ex.decision_reasoning}")
        lines.append(f"Output: {ex.target_output}")
    return "\n".join(lines)


class MultiInstanceReviewPipeline:
    """The reviewer instance never receives the generator's reasoning or draft history (TS 4.6)."""

    @staticmethod
    def prepare_reviewer_payload(generated_code: str, checklist: List[str]) -> Dict[str, Any]:
        return {
            "role": "user",
            "content": (
                "You are an independent Senior Security and Architecture Reviewer. "
                "You have NO prior context regarding how this code was generated. "
                "Review this implementation against the checklist:\n\n"
                f"Checklist: {checklist}\n\n"
                f"Code under review:\n```python\n{generated_code}\n```"
            ),
        }


def main() -> None:
    print(render_few_shot_prompt_block(FEW_SHOT_EXTRACTION_EXAMPLES))
    print()
    print(render_few_shot_prompt_block(REVIEW_FEW_SHOT_EXAMPLES))
    print(f"\nReview output format: {REVIEW_FORMAT}")


if __name__ == "__main__":
    main()
