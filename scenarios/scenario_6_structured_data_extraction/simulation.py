"""
Scenario 6: Structured Data Extraction
End-to-End System Simulation

Weaves Together:
- TS 4.3: Structured Output Enforcement via Tool Use & JSON Schemas
- TS 4.4: Validation & Retry Feedback Loops (Recoverable vs Unrecoverable errors)
- TS 4.5: Batch Processing Strategies (50% discount with custom_id)
- TS 5.5: Human Review Workflows & Confidence Calibration with Stratified Auditing
"""

import json
import random
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class ExtractionRoutingTier(str, Enum):
    STRAIGHT_THROUGH = "STP_AUTO_COMMIT"        # Direct database write
    STRATIFIED_AUDIT = "STRATIFIED_AUDIT"        # High confidence, but sampled for drift monitoring
    SECONDARY_SPOT_CHECK = "SPOT_CHECK"          # Medium confidence
    HUMAN_TRIAGE = "MANDATORY_HUMAN_TRIAGE"      # Low confidence or unrecoverable error


@dataclass
class ExtractionOutcome:
    doc_id: str
    status: str
    routing_tier: ExtractionRoutingTier
    extracted_record: Optional[Dict[str, Any]]
    retries_used: int
    rationale: str


class StructuredExtractionPipeline:
    """Production data extraction pipeline with schema validation, bounded retries, and drift auditing."""

    HIGH_CONFIDENCE_THRESHOLD = 0.90
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    AUDIT_RATE = 0.10  # 10% stratified sample of high-confidence extractions

    def __init__(self, random_seed: Optional[int] = 42) -> None:
        if random_seed is not None:
            random.seed(random_seed)

    def validate_payload(self, raw_text: str, candidate_json: Dict[str, Any]) -> Tuple[bool, bool, str]:
        """
        Validates extracted payload.
        Returns (is_valid, is_recoverable_retry, error_message).
        """
        # Math check: subtotal + tax == total
        subtotal = candidate_json.get("subtotal", 0.0)
        tax = candidate_json.get("tax", 0.0)
        total = candidate_json.get("total", 0.0)

        if round(subtotal + tax, 2) != round(total, 2):
            return False, True, f"Calculation mismatch: subtotal ({subtotal}) + tax ({tax}) != total ({total})"

        # Line items sum check
        line_items = candidate_json.get("line_items", [])
        if line_items:
            items_sum = sum(item.get("total_price", 0.0) for item in line_items)
            if abs(round(items_sum, 2) - round(subtotal, 2)) > 0.02:
                return False, True, f"Calculation mismatch: sum of line items ({items_sum:.2f}) does not equal subtotal ({subtotal:.2f})"

        # Check enum + 'other' + detail string contract
        if candidate_json.get("expense_category") == "other" and not candidate_json.get("other_category_detail"):
            return False, True, "Validation error: 'other_category_detail' is mandatory when 'expense_category' is 'other'."

        # Unrecoverable Fact Check: if required field is null, check if source doc even mentions it
        if candidate_json.get("tax_id") is None:
            if "tax" not in raw_text.lower() and "vat" not in raw_text.lower():
                # Document genuinely lacks this data!
                # Do NOT retry: retrying causes hallucination!
                return False, False, "Unrecoverable: Document lacks Tax/VAT ID. Aborting retry to avoid hallucination."

        return True, False, ""

    def process_extraction(
        self,
        doc_id: str,
        raw_text: str,
        simulated_model_turns: List[Dict[str, Any]],
        confidence_score: float
    ) -> ExtractionOutcome:
        """Runs the validation retry loop and calibrated confidence routing."""
        retries = 0

        for candidate in simulated_model_turns:
            is_valid, is_recoverable, err_msg = self.validate_payload(raw_text, candidate)

            if is_valid:
                # Routed based on calibrated confidence
                if confidence_score >= self.HIGH_CONFIDENCE_THRESHOLD:
                    # Stratified audit check
                    is_sampled = random.random() < self.AUDIT_RATE
                    tier = ExtractionRoutingTier.STRATIFIED_AUDIT if is_sampled else ExtractionRoutingTier.STRAIGHT_THROUGH
                    reason = "High confidence drift audit sample" if is_sampled else "High confidence straight-through processing"
                elif confidence_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                    tier = ExtractionRoutingTier.SECONDARY_SPOT_CHECK
                    reason = "Medium confidence spot check"
                else:
                    tier = ExtractionRoutingTier.HUMAN_TRIAGE
                    reason = "Low confidence triage"

                return ExtractionOutcome(
                    doc_id=doc_id,
                    status="SUCCESS",
                    routing_tier=tier,
                    extracted_record=candidate,
                    retries_used=retries,
                    rationale=reason
                )

            # Invalid case: check if recoverable
            if not is_recoverable:
                # Fast fail: unrecoverable missing source facts
                return ExtractionOutcome(
                    doc_id=doc_id,
                    status="FAILED_UNRECOVERABLE",
                    routing_tier=ExtractionRoutingTier.HUMAN_TRIAGE,
                    extracted_record=candidate,
                    retries_used=retries,
                    rationale=err_msg
                )

            # Recoverable: retry if within limit
            retries += 1
            if retries >= 3:
                return ExtractionOutcome(
                    doc_id=doc_id,
                    status="MAX_RETRIES_EXCEEDED",
                    routing_tier=ExtractionRoutingTier.HUMAN_TRIAGE,
                    extracted_record=candidate,
                    retries_used=retries,
                    rationale="Exceeded maximum 3 retry attempts."
                )

        return ExtractionOutcome(
            doc_id=doc_id,
            status="EMPTY_TURNS",
            routing_tier=ExtractionRoutingTier.HUMAN_TRIAGE,
            extracted_record=None,
            retries_used=retries,
            rationale="No turns provided."
        )


def main() -> None:
    print("=" * 70)
    print("Scenario 6: Structured Data Extraction Simulation")
    print("=" * 70)

    pipeline = StructuredExtractionPipeline(random_seed=42)

    # 1. Recoverable calculation error corrected on turn 2
    doc1_text = "Invoice #101: Subtotal $100, Tax $10, Total $110, Tax ID: TX-88"
    doc1_turns = [
        {"subtotal": 100.0, "tax": 10.0, "total": 100.0, "tax_id": "TX-88"},  # Bad math (100+10!=100)
        {"subtotal": 100.0, "tax": 10.0, "total": 110.0, "tax_id": "TX-88"}   # Corrected!
    ]
    res1 = pipeline.process_extraction("inv_101", doc1_text, doc1_turns, confidence_score=0.98)
    print("\nCase 1 (Recoverable Retry & High Confidence):")
    print(f"Status: {res1.status} (Retries: {res1.retries_used})")
    print(f"Routing Tier: {res1.routing_tier.value}")
    print(f"Payload: {res1.extracted_record}")

    # 2. Unrecoverable missing fact (Abort immediately!)
    doc2_text = "Coffee Shop Receipt: Total $4.50. Paid cash."
    doc2_turns = [
        {"subtotal": 4.50, "tax": 0.0, "total": 4.50, "tax_id": None}
    ]
    res2 = pipeline.process_extraction("rcpt_99", doc2_text, doc2_turns, confidence_score=0.60)
    print("\nCase 2 (Unrecoverable Missing Fact Fast-Fail):")
    print(f"Status: {res2.status}")
    print(f"Routing Tier: {res2.routing_tier.value}")
    print(f"Rationale: {res2.rationale}")


if __name__ == "__main__":
    main()
