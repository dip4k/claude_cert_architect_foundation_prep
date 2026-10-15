"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.2: Apply few-shot prompting to improve output consistency and quality
Task Statement 4.6: Design multi-instance and multi-pass review architectures
Exam Scenario 5 & 6: Code Generation & Structured Data Extraction

Key Exam Concepts Demonstrated:
1. Targeted Few-Shot Prompting (2-4 examples with reasoning):
   - Demonstrating ambiguous-case handling and edge cases.
   - Reducing hallucination across varied document formats (tables vs prose).
2. Multi-Instance Review Architecture:
   - Why self-review in the generator's session fails (author confirmation bias).
   - Using an independent Claude instance (zero generator reasoning context) to review code.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FewShotExample:
    scenario_input: str
    decision_reasoning: str
    target_output: Dict[str, Any]


FEW_SHOT_EXTRACTION_EXAMPLES: List[FewShotExample] = [
    FewShotExample(
        scenario_input="Consulting invoice stating total $500, but line items only list 4 hrs @ $100 = $400.",
        decision_reasoning=(
            "Flagged arithmetic discrepancy: line items total ($400) differs from stated total ($500). "
            "Extracted conflict_detected: True with explicit breakdown rather than guessing."
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
        decision_reasoning="Document lacks due_date and tax_id. Return null instead of fabricating values.",
        target_output={
            "stated_total": 120.0,
            "due_date": None,
            "tax_id": None,
            "conflict_detected": False,
        },
    ),
]


def render_few_shot_prompt_block(examples: List[FewShotExample]) -> str:
    """Renders 2-4 targeted few-shot examples with explicit reasoning."""
    lines = ["### FEW-SHOT REASONING EXAMPLES:"]
    for idx, ex in enumerate(examples, start=1):
        lines.append(f"\n--- Example {idx} ---")
        lines.append(f"Input: {ex.scenario_input}")
        lines.append(f"Architectural Reasoning: {ex.decision_reasoning}")
        lines.append(f"Output: {ex.target_output}")
    return "\n".join(lines)


class MultiInstanceReviewPipeline:
    """
    Demonstrates independent review instance architecture (TS 4.6).
    The reviewer instance NEVER receives the generator's internal reasoning or draft history.
    """

    @staticmethod
    def prepare_reviewer_payload(generated_code: str, checklist: List[str]) -> Dict[str, Any]:
        return {
            "role": "user",
            "content": (
                "You are an independent Senior Security and Architecture Reviewer. "
                "You have NO prior context regarding how this code was generated. "
                f"Review this implementation against the checklist:\n\n"
                f"Checklist: {checklist}\n\n"
                f"Code under review:\n```python\n{generated_code}\n```"
            ),
        }


def main() -> None:
    print("Rendered Few-Shot Examples Block:")
    print(render_few_shot_prompt_block(FEW_SHOT_EXTRACTION_EXAMPLES)[:300], "...\n")

    print("Multi-Instance Independent Review Payload Created:")
    payload = MultiInstanceReviewPipeline.prepare_reviewer_payload(
        generated_code="def process(): pass",
        checklist=["No raw SQL concatenation", "Handles timeouts"],
    )
    print(payload["content"][:200], "...")


if __name__ == "__main__":
    main()
