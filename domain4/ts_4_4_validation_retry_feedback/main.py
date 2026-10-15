"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.4: Design Validation and Retry Feedback Loops
Exam Scenario 6: Structured Data Extraction

Key Architectural Concepts:
1. Closed-loop validation providing targeted constraint failure feedback.
2. Distinguishing retryable syntax/calculation errors from unrecoverable missing source facts.
3. Max retry limits (bounded retries).
4. Nullable fields to prevent model hallucination when source document lacks data.
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
class ValidationReport:
    is_valid: bool
    is_retryable: bool
    error_message: str
    failed_field: Optional[str] = None


class ExtractionValidator:
    """Validates financial invoices against schemas and business rules."""

    @staticmethod
    def validate_invoice(payload: Dict[str, Any], raw_document: str) -> ValidationReport:
        # Check required fields
        if "subtotal" not in payload or "total" not in payload:
            return ValidationReport(
                is_valid=False,
                is_retryable=True,
                error_message="Missing required keys: 'subtotal' and 'total' must be provided.",
                failed_field="subtotal/total"
            )

        # Business logic: Total >= Subtotal
        if payload.get("total", 0) < payload.get("subtotal", 0):
            return ValidationReport(
                is_valid=False,
                is_retryable=True,
                error_message=f"Constraint violation: 'total' ({payload['total']}) cannot be less than 'subtotal' ({payload['subtotal']}).",
                failed_field="total"
            )

        # Critical Exam Case: Required tax ID missing from raw source text!
        if payload.get("tax_id") is None:
            # Check if source text even mentions tax/VAT
            if "tax" not in raw_document.lower() and "vat" not in raw_document.lower():
                # Unrecoverable error if tax_id was marked mandatory without nullable support
                return ValidationReport(
                    is_valid=False,
                    is_retryable=False,  # DO NOT RETRY! It is impossible to extract what does not exist!
                    error_message="Unrecoverable: Document contains no Tax/VAT ID. Retrying would cause hallucinations.",
                    failed_field="tax_id"
                )

        return ValidationReport(is_valid=True, is_retryable=False, error_message="")


class ResilientExtractorLoop:
    """Manages closed-loop validation with targeted feedback and early exit."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    def run_validation_cycle(
        self,
        raw_document: str,
        simulated_model_outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        retries = 0
        conversation_feedback: List[str] = []

        for candidate_output in simulated_model_outputs:
            report = ExtractionValidator.validate_invoice(candidate_output, raw_document)

            if report.is_valid:
                return {
                    "status": "SUCCESS",
                    "retries_used": retries,
                    "final_payload": candidate_output,
                    "feedback_log": conversation_feedback
                }

            # If unrecoverable, abort immediately!
            if not report.is_retryable:
                conversation_feedback.append(f"[FATAL]: {report.error_message}")
                return {
                    "status": "ABORTED_UNRECOVERABLE",
                    "reason": report.error_message,
                    "retries_used": retries,
                    "feedback_log": conversation_feedback
                }

            # Retryable error
            retries += 1
            feedback = f"Validation Failed on '{report.failed_field}': {report.error_message}. Please adjust calculation."
            conversation_feedback.append(feedback)

            if retries >= self.max_retries:
                return {
                    "status": "MAX_RETRIES_EXCEEDED",
                    "retries_used": retries,
                    "feedback_log": conversation_feedback
                }

        return {"status": "UNKNOWN_FAILURE", "retries_used": retries, "feedback_log": conversation_feedback}


def main() -> None:
    print("=" * 70)
    print("TS 4.4: Validation & Retry Feedback Loops Demo")
    print("=" * 70)

    loop = ResilientExtractorLoop(max_retries=3)

    # Scenario 1: Retryable calculation error corrected on turn 2
    raw_doc_1 = "Invoice #101: Subtotal $100. Tax $10. Total $110. Tax ID: TX-999"
    candidate_turns_1 = [
        {"subtotal": 100, "total": 90, "tax_id": "TX-999"},   # Invalid total < subtotal
        {"subtotal": 100, "total": 110, "tax_id": "TX-999"},  # Corrected!
    ]
    res1 = loop.run_validation_cycle(raw_doc_1, candidate_turns_1)
    print("\n1. Retryable Calculation Error Recovery:")
    print(f"Status: {res1['status']} (Retries used: {res1['retries_used']})")
    print(f"Feedback sent to Claude: {res1['feedback_log']}")

    # Scenario 2: Unrecoverable missing tax ID (Abort early!)
    raw_doc_2 = "Receipt from Coffee Shop: Total $5. No receipt number or tax details."
    candidate_turns_2 = [
        {"subtotal": 5, "total": 5, "tax_id": None}
    ]
    res2 = loop.run_validation_cycle(raw_doc_2, candidate_turns_2)
    print("\n2. Unrecoverable Missing Source Data Detection:")
    print(f"Status: {res2['status']}")
    print(f"Reason: {res2['reason']}")
    print("✅ Aborted immediately without burning retry tokens or inducing hallucination!")


if __name__ == "__main__":
    main()
