"""
Domain 5: Context Management & Reliability
Task Statement 5.4: Manage context effectively in large codebase exploration
Task Statement 5.5: Design human review workflows and confidence calibration
Exam Scenario 4 & 6: Developer Productivity & Structured Data Extraction

Key Exam Concepts Demonstrated:
1. Codebase exploration context management:
   - Maintaining persistent scratchpad files (scratchpad.md) across context boundaries.
   - Using structured state manifests for crash recovery.
   - Explore subagent delegation to isolate verbose exploration output.
2. Human review & confidence calibration:
   - Why aggregate accuracy (e.g. 97%) masks catastrophic failure in rare segments.
   - Stratified random sampling for ongoing quality measurement.
   - Field-level confidence scores calibrated against labeled validation sets.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import random


@dataclass
class ExtractionRecord:
    doc_id: str
    doc_type: str  # "standard_invoice" | "customs_declaration" | "handwritten_receipt"
    confidence_score: float
    extracted_total: float
    requires_human_review: bool = False


class HumanReviewRoutingEngine:
    """Demonstrates calibrated human review routing and stratified sampling (TS 5.5)."""

    def __init__(self, confidence_threshold: float = 0.85) -> None:
        self.threshold = confidence_threshold

    def route_record(self, record: ExtractionRecord) -> ExtractionRecord:
        """Routes low confidence records to human reviewers."""
        if record.confidence_score < self.threshold:
            record.requires_human_review = True
        return record

    @staticmethod
    def stratified_random_sample(
        records: List[ExtractionRecord],
        sample_size_per_segment: int = 2,
    ) -> List[ExtractionRecord]:
        """
        Stratified random sampling across segments to detect novel error patterns
        even among high-confidence extractions.
        """
        segments: Dict[str, List[ExtractionRecord]] = {}
        for r in records:
            segments.setdefault(r.doc_type, []).append(r)

        sampled = []
        for segment_name, segment_records in segments.items():
            k = min(sample_size_per_segment, len(segment_records))
            sampled.extend(random.sample(segment_records, k))
        return sampled


class CodebaseScratchpadManager:
    """Manages scratchpad.md persistence to counteract context degradation (TS 5.4)."""

    def __init__(self) -> None:
        self.findings: List[str] = []

    def record_finding(self, finding: str) -> None:
        self.findings.append(finding)

    def render_scratchpad(self) -> str:
        lines = ["# CODEBASE EXPLORATION SCRATCHPAD (IMMUTABLE DISCOVERY)"]
        for idx, item in enumerate(self.findings, start=1):
            lines.append(f"{idx}. {item}")
        return "\n".join(lines)


def main() -> None:
    router = HumanReviewRoutingEngine(confidence_threshold=0.85)
    records = [
        ExtractionRecord("DOC-01", "standard_invoice", 0.96, 120.0),
        ExtractionRecord("DOC-02", "customs_declaration", 0.72, 8400.0),  # Low confidence
        ExtractionRecord("DOC-03", "handwritten_receipt", 0.65, 45.0),    # Low confidence
        ExtractionRecord("DOC-04", "standard_invoice", 0.99, 50.0),
    ]

    routed = [router.route_record(r) for r in records]
    human_needed = [r.doc_id for r in routed if r.requires_human_review]
    print(f"Records routed to human review: {human_needed}")

    samples = HumanReviewRoutingEngine.stratified_random_sample(routed, 1)
    print(f"Stratified sample count across segments: {len(samples)}")


if __name__ == "__main__":
    main()
