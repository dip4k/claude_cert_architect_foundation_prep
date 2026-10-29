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


EXTRACTION_TOOL_NAME = "extract_invoice"
EXPENSE_CATEGORIES = ["travel", "software", "office", "other", "unclear"]

# Nullable optional fields stop the model from inventing values the document lacks.
EXTRACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string"},
        "total": {"type": "number"},
        "tax_id": {"type": ["string", "null"]},
        "expense_category": {"type": "string", "enum": EXPENSE_CATEGORIES},
        "other_category_detail": {"type": ["string", "null"]},
    },
    "required": ["vendor", "total", "tax_id", "expense_category"],
}

_JSON_TYPES: Dict[str, Any] = {
    "string": str, "number": (int, float), "null": type(None), "boolean": bool,
}


def build_extraction_request(doc_text: str) -> Dict[str, Any]:
    """Forced-tool extraction request. No thinking and no temperature: forced tool_choice
    is incompatible with extended thinking (HTTP 400). Returns a dict only; no API call."""
    return {
        "model": "claude-haiku-4-5",
        "max_tokens": 1024,
        "tools": [
            {
                "name": EXTRACTION_TOOL_NAME,
                "description": "Extract invoice fields; use null when the document lacks a field.",
                "input_schema": EXTRACTION_SCHEMA,
            }
        ],
        "tool_choice": {"type": "tool", "name": EXTRACTION_TOOL_NAME},
        "messages": [{"role": "user", "content": doc_text}],
    }


def validate_against_schema(candidate: Dict[str, Any]) -> List[str]:
    """Minimal schema check (required keys, types incl. null, enum). Returns error strings."""
    errors: List[str] = []
    props = EXTRACTION_SCHEMA["properties"]
    for key in EXTRACTION_SCHEMA["required"]:
        if key not in candidate:
            errors.append(f"missing required field: {key}")
    for key, value in candidate.items():
        spec = props.get(key)
        if spec is None:
            continue
        types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
        if not any(isinstance(value, _JSON_TYPES[t]) for t in types):
            errors.append(f"wrong type for {key}")
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{key} not in enum")
    return errors


def is_retry_eligible(
    is_valid: bool, is_recoverable: bool, retries: int, max_retries: int = 3
) -> bool:
    """Retry only fixable errors (format, math). Absent source data never improves on retry."""
    return (not is_valid) and is_recoverable and retries < max_retries


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

    def route_by_confidence(self, confidence: float) -> Tuple[ExtractionRoutingTier, str]:
        """Map calibrated confidence to a routing tier; high confidence is still sampled."""
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            if random.random() < self.AUDIT_RATE:
                return ExtractionRoutingTier.STRATIFIED_AUDIT, "High confidence drift audit sample"
            return (
                ExtractionRoutingTier.STRAIGHT_THROUGH,
                "High confidence straight-through processing",
            )
        if confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return ExtractionRoutingTier.SECONDARY_SPOT_CHECK, "Medium confidence spot check"
        return ExtractionRoutingTier.HUMAN_TRIAGE, "Low confidence triage"

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
                tier, reason = self.route_by_confidence(confidence_score)

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
