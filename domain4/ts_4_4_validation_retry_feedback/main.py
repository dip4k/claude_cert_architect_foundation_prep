"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.4: Validation, retry and feedback loops
Exam Scenario 6: Structured Data Extraction

Intent: decide WHEN a retry can help. A retry works for format or structure errors (and
arithmetic the model can redo) when the original document, the failed extraction and the
specific error are sent back. A retry is useless when the information is absent from the
source: route that to a human. Also track detected_pattern on findings so dismissed false
positives can be analysed later.

All offline: candidate model outputs are supplied by the caller.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

EXTRACTION_MODEL = "claude-haiku-4-5"
TOTAL_TOLERANCE = 0.01


class ErrorKind(str, Enum):
    FORMAT = "format"  # wrong shape, wrong date format, missing key the source does support
    SEMANTIC = "semantic"  # values valid JSON but inconsistent (total < subtotal)
    ABSENT_IN_SOURCE = "absent_in_source"  # the document never states it


class RetryAction(str, Enum):
    ACCEPT = "accept"
    RETRY_WITH_FEEDBACK = "retry_with_feedback"
    ROUTE_TO_HUMAN = "route_to_human"
    GIVE_UP = "give_up"


@dataclass
class ValidationReport:
    is_valid: bool
    is_retryable: bool
    error_message: str
    failed_field: Optional[str] = None
    error_kind: Optional[ErrorKind] = None


def detect_conflict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return calculated_total, stated_total and conflict_detected for a payload with line_items."""
    items = payload.get("line_items") or []
    calculated = round(sum(float(i.get("total", 0.0)) for i in items), 2)
    stated = payload.get("stated_total")
    conflict = stated is not None and abs(calculated - float(stated)) > TOTAL_TOLERANCE
    return {
        "calculated_total": calculated,
        "stated_total": stated,
        "conflict_detected": bool(conflict),
    }


class ExtractionValidator:
    """Validates invoices against structure, business rules and what the source really says."""

    @staticmethod
    def validate_invoice(payload: Dict[str, Any], raw_document: str) -> ValidationReport:
        if "subtotal" not in payload or "total" not in payload:
            return ValidationReport(
                is_valid=False,
                is_retryable=True,
                error_message="Missing required keys: 'subtotal' and 'total' must be provided.",
                failed_field="subtotal/total",
                error_kind=ErrorKind.FORMAT,
            )

        if payload["total"] < payload["subtotal"]:
            return ValidationReport(
                is_valid=False,
                is_retryable=True,
                error_message=(
                    f"Constraint violation: 'total' ({payload['total']}) cannot be less "
                    f"than 'subtotal' ({payload['subtotal']})."
                ),
                failed_field="total",
                error_kind=ErrorKind.SEMANTIC,
            )

        if "line_items" in payload and detect_conflict(payload)["conflict_detected"]:
            info = detect_conflict(payload)
            return ValidationReport(
                is_valid=False,
                is_retryable=True,
                error_message=(
                    f"calculated_total {info['calculated_total']} differs from "
                    f"stated_total {info['stated_total']}."
                ),
                failed_field="line_items",
                error_kind=ErrorKind.SEMANTIC,
            )

        if payload.get("tax_id") is None:
            mentions_tax = re.search(r"\b(tax|vat)", raw_document, re.IGNORECASE) is not None
            if not mentions_tax:
                return ValidationReport(
                    is_valid=False,
                    is_retryable=False,  # cannot extract what the document never says
                    error_message=(
                        "Unrecoverable: document contains no Tax/VAT ID. "
                        "Retrying would invite hallucination."
                    ),
                    failed_field="tax_id",
                    error_kind=ErrorKind.ABSENT_IN_SOURCE,
                )
            # The source mentions tax but the model returned null: a retry can help.
            return ValidationReport(
                is_valid=False,
                is_retryable=True,
                error_message="tax_id is null but the document mentions tax/VAT; re-read it.",
                failed_field="tax_id",
                error_kind=ErrorKind.FORMAT,
            )

        return ValidationReport(is_valid=True, is_retryable=False, error_message="")


def decide_retry(report: ValidationReport, retries_used: int, max_retries: int) -> RetryAction:
    """Retry-eligibility rule: absent info goes to a human, fixable errors retry (bounded)."""
    if report.is_valid:
        return RetryAction.ACCEPT
    if report.error_kind == ErrorKind.ABSENT_IN_SOURCE or not report.is_retryable:
        return RetryAction.ROUTE_TO_HUMAN
    if retries_used >= max_retries:
        return RetryAction.GIVE_UP
    return RetryAction.RETRY_WITH_FEEDBACK


def build_retry_prompt(
    original_document: str, failed_extraction: Dict[str, Any], errors: List[str]
) -> str:
    """A useful retry sends all three: the source, the failed attempt and the exact errors."""
    error_lines = "\n".join(f"- {e}" for e in errors)
    return (
        f"<document>\n{original_document}\n</document>\n"
        f"<failed_extraction>\n{json.dumps(failed_extraction)}\n</failed_extraction>\n"
        f"<validation_errors>\n{error_lines}\n</validation_errors>\n"
        "Re-extract from the document and fix only these errors. "
        "If the document does not state a value, return null."
    )


class ResilientExtractorLoop:
    """Closed-loop validation with targeted feedback and early exit."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    def run_validation_cycle(
        self, raw_document: str, simulated_model_outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        retries = 0
        feedback_log: List[str] = []

        for candidate in simulated_model_outputs:
            report = ExtractionValidator.validate_invoice(candidate, raw_document)
            action = decide_retry(report, retries, self.max_retries)

            if action == RetryAction.ACCEPT:
                return {
                    "status": "SUCCESS",
                    "retries_used": retries,
                    "final_payload": candidate,
                    "feedback_log": feedback_log,
                }
            if action == RetryAction.ROUTE_TO_HUMAN:
                feedback_log.append(f"[FATAL]: {report.error_message}")
                return {
                    "status": "ABORTED_UNRECOVERABLE",
                    "reason": report.error_message,
                    "route": "human_review",
                    "retries_used": retries,
                    "feedback_log": feedback_log,
                }

            retries += 1
            feedback_log.append(
                build_retry_prompt(raw_document, candidate, [report.error_message])
            )
            if action == RetryAction.GIVE_UP or retries >= self.max_retries:
                return {
                    "status": "MAX_RETRIES_EXCEEDED",
                    "retries_used": retries,
                    "feedback_log": feedback_log,
                }

        return {"status": "UNKNOWN_FAILURE", "retries_used": retries, "feedback_log": feedback_log}


# ------------------------------------------------------------------------------
# detected_pattern tracking for dismissal analysis
# ------------------------------------------------------------------------------


@dataclass
class TrackedFinding:
    finding_id: str
    category: str
    detected_pattern: str  # the code construct or text pattern that triggered the finding
    dismissed: bool = False


@dataclass
class DismissalAnalyzer:
    """Aggregate dismissals by detected_pattern to find systematic false positives."""

    findings: List[TrackedFinding] = field(default_factory=list)

    def record(self, finding: TrackedFinding) -> None:
        self.findings.append(finding)

    def dismissal_rates(self) -> Dict[str, float]:
        totals: Dict[str, int] = defaultdict(int)
        dismissed: Dict[str, int] = defaultdict(int)
        for f in self.findings:
            totals[f.detected_pattern] += 1
            dismissed[f.detected_pattern] += int(f.dismissed)
        return {p: dismissed[p] / totals[p] for p in totals}

    def noisy_patterns(self, threshold: float = 0.5, min_samples: int = 3) -> List[str]:
        """Patterns developers keep dismissing: candidates for rewriting or disabling."""
        counts: Dict[str, int] = defaultdict(int)
        for f in self.findings:
            counts[f.detected_pattern] += 1
        rates = self.dismissal_rates()
        return sorted(p for p, r in rates.items() if r >= threshold and counts[p] >= min_samples)


def main() -> None:
    loop = ResilientExtractorLoop(max_retries=3)

    doc1 = "Invoice #101: Subtotal $100. Tax $10. Total $110. Tax ID: TX-999"
    res1 = loop.run_validation_cycle(
        doc1,
        [
            {"subtotal": 100, "total": 90, "tax_id": "TX-999"},
            {"subtotal": 100, "total": 110, "tax_id": "TX-999"},
        ],
    )
    print("1. Retryable error:", res1["status"], "retries:", res1["retries_used"])

    doc2 = "Receipt from Coffee Shop: Total $5. No receipt number."
    res2 = loop.run_validation_cycle(doc2, [{"subtotal": 5, "total": 5, "tax_id": None}])
    print("2. Absent in source:", res2["status"], "->", res2["route"])


if __name__ == "__main__":
    main()
