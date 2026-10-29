"""
Domain 5: Context Management & Reliability
Task Statement 5.5: Design human review workflows and confidence calibration
Exam Scenario 6: Structured Data Extraction (also relevant to Scenario 1)

Key Architectural Concepts (all offline, no API calls):
1. Aggregate accuracy (e.g. 97%) can hide weak segments (document type x field).
2. Stratified random sampling of HIGH-confidence outputs, by (document_type, field).
3. Field-level confidence checked against a labelled validation set (calibration: reliability
   bins and Expected Calibration Error, ECE).
4. Validate accuracy per segment before reducing human review for that segment.
5. Route low-confidence, ambiguous or contradictory-source items to humans.
"""

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

Segment = Tuple[str, str]  # (document_type, field_name)


class RoutingTier(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"  # Straight-Through Processing (STP)
    STRATIFIED_AUDIT = "STRATIFIED_AUDIT"  # High confidence, sampled for drift monitoring
    SPOT_CHECK = "SPOT_CHECK"  # Medium confidence review
    MANDATORY_ESCALATION = "MANDATORY_ESCALATION"  # Low confidence, ambiguous or conflicting


@dataclass
class TriageDecision:
    item_id: str
    confidence_score: float
    routing_tier: RoutingTier
    reason: str


@dataclass
class FieldExtraction:
    """One extracted field with its confidence and (when known) whether it was correct."""

    doc_id: str
    document_type: str
    field_name: str
    confidence: float
    correct: Optional[bool] = None

    @property
    def segment(self) -> Segment:
        return (self.document_type, self.field_name)


@dataclass
class SegmentStats:
    n: int
    correct: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.n if self.n else 0.0


@dataclass
class CalibrationBin:
    low: float
    high: float
    count: int
    mean_confidence: float
    accuracy: float


# ==============================================================================
# 1. Routing (confidence + ambiguity/conflict signals)
# ==============================================================================


class ConfidenceRouter:
    """Routes items to automation or human review queues based on thresholds and signals."""

    HIGH_THRESHOLD = 0.90
    MEDIUM_THRESHOLD = 0.70
    AUDIT_SAMPLING_RATE = 0.10  # share of high-confidence items sent to the audit queue

    def __init__(self, random_seed: Optional[int] = 42) -> None:
        # Local generator: never touch the global random state.
        self._rng = random.Random(random_seed)

    def route_item(
        self,
        item_id: str,
        confidence: float,
        category: str,
        ambiguous: bool = False,
        sources_conflict: bool = False,
    ) -> TriageDecision:
        """Route one item; ambiguous or contradictory inputs always go to a human."""
        if ambiguous or sources_conflict:
            why = "ambiguous input" if ambiguous else "contradictory sources"
            return TriageDecision(
                item_id, confidence, RoutingTier.MANDATORY_ESCALATION,
                f"[{category}] {why}: routed to human regardless of confidence ({confidence}).",
            )
        if confidence >= self.HIGH_THRESHOLD:
            if self._rng.random() < self.AUDIT_SAMPLING_RATE:
                return TriageDecision(
                    item_id, confidence, RoutingTier.STRATIFIED_AUDIT,
                    f"[{category}] High confidence ({confidence}), sampled for drift audit.",
                )
            return TriageDecision(
                item_id, confidence, RoutingTier.AUTO_APPROVE,
                f"[{category}] Straight-through ({confidence} >= {self.HIGH_THRESHOLD}).",
            )
        if confidence >= self.MEDIUM_THRESHOLD:
            return TriageDecision(
                item_id, confidence, RoutingTier.SPOT_CHECK,
                f"[{category}] Medium confidence ({confidence}) queued for secondary review.",
            )
        return TriageDecision(
            item_id, confidence, RoutingTier.MANDATORY_ESCALATION,
            f"[{category}] Low confidence ({confidence} < {self.MEDIUM_THRESHOLD}) to a human.",
        )


# ==============================================================================
# 2. Stratified sampling by (document_type, field)
# ==============================================================================


def stratified_audit_sample(
    items: Sequence[FieldExtraction],
    rate: float = 0.10,
    seed: Optional[int] = 42,
    min_per_stratum: int = 1,
    min_confidence: Optional[float] = None,
) -> List[FieldExtraction]:
    """
    Sample the same share from every (document_type, field) stratum.

    A flat random sample over-represents common segments and can miss a rare one entirely, so
    each stratum gets at least `min_per_stratum` items. Pass `min_confidence` to sample only
    from high-confidence output (the items automation would otherwise approve unseen).
    """
    pool = [i for i in items if min_confidence is None or i.confidence >= min_confidence]
    strata: Dict[Segment, List[FieldExtraction]] = defaultdict(list)
    for item in pool:
        strata[item.segment].append(item)
    rng = random.Random(seed)
    sample: List[FieldExtraction] = []
    for segment in sorted(strata):
        members = strata[segment]
        k = min(len(members), max(min_per_stratum, math.ceil(rate * len(members))))
        sample.extend(rng.sample(members, k))
    return sample


# ==============================================================================
# 3. Accuracy by segment (aggregate numbers can hide weak segments)
# ==============================================================================


def aggregate_accuracy(items: Sequence[FieldExtraction]) -> float:
    """Overall accuracy across labelled items."""
    labelled = [i for i in items if i.correct is not None]
    return sum(1 for i in labelled if i.correct) / len(labelled) if labelled else 0.0


def segment_accuracy(items: Sequence[FieldExtraction]) -> Dict[Segment, SegmentStats]:
    """Accuracy per (document_type, field) on labelled items."""
    stats: Dict[Segment, SegmentStats] = {}
    for item in items:
        if item.correct is None:
            continue
        current = stats.setdefault(item.segment, SegmentStats(0, 0))
        current.n += 1
        current.correct += 1 if item.correct else 0
    return stats


def weak_segments(
    items: Sequence[FieldExtraction], min_accuracy: float = 0.95
) -> List[Segment]:
    """Segments whose accuracy is below the bar, even if the aggregate looks healthy."""
    return sorted(s for s, st in segment_accuracy(items).items() if st.accuracy < min_accuracy)


def safe_to_reduce_review(
    items: Sequence[FieldExtraction],
    segment: Segment,
    min_accuracy: float = 0.95,
    min_samples: int = 20,
) -> bool:
    """Only reduce human review for a segment with enough labelled data and enough accuracy."""
    stats = segment_accuracy(items).get(segment)
    return bool(stats and stats.n >= min_samples and stats.accuracy >= min_accuracy)


# ==============================================================================
# 4. Calibration check on a labelled validation set
# ==============================================================================


def reliability_bins(items: Sequence[FieldExtraction], n_bins: int = 5) -> List[CalibrationBin]:
    """Group labelled items by stated confidence and compare confidence with real accuracy."""
    grouped: Dict[int, List[FieldExtraction]] = defaultdict(list)
    for item in items:
        if item.correct is None:
            continue
        index = min(int(item.confidence * n_bins), n_bins - 1)
        grouped[index].append(item)
    bins: List[CalibrationBin] = []
    for index in sorted(grouped):
        members = grouped[index]
        bins.append(
            CalibrationBin(
                low=index / n_bins,
                high=(index + 1) / n_bins,
                count=len(members),
                mean_confidence=sum(m.confidence for m in members) / len(members),
                accuracy=sum(1 for m in members if m.correct) / len(members),
            )
        )
    return bins


def expected_calibration_error(items: Sequence[FieldExtraction], n_bins: int = 5) -> float:
    """ECE: size-weighted average gap between confidence and accuracy across bins."""
    bins = reliability_bins(items, n_bins)
    total = sum(b.count for b in bins)
    if not total:
        return 0.0
    return sum(b.count / total * abs(b.accuracy - b.mean_confidence) for b in bins)


def segment_calibration(
    items: Sequence[FieldExtraction], n_bins: int = 5
) -> Dict[Segment, float]:
    """ECE per segment: a well-calibrated aggregate can still hide a badly calibrated segment."""
    by_segment: Dict[Segment, List[FieldExtraction]] = defaultdict(list)
    for item in items:
        by_segment[item.segment].append(item)
    return {s: expected_calibration_error(v, n_bins) for s, v in sorted(by_segment.items())}


def demo_validation_set() -> List[FieldExtraction]:
    """100 labelled fields: 97% overall accuracy, but customs HS codes are only 70% correct."""
    items = [
        FieldExtraction(f"INV-{i}", "standard_invoice", "total", 0.97, True) for i in range(90)
    ]
    items += [
        FieldExtraction(f"CUS-{i}", "customs_form", "hs_code", 0.95, i < 7) for i in range(10)
    ]
    return items


def main() -> None:
    """Offline demo: aggregate accuracy hides a weak segment; sampling and ECE expose it."""
    data = demo_validation_set()
    print(f"Aggregate accuracy: {aggregate_accuracy(data):.0%}")
    for segment, st in segment_accuracy(data).items():
        print(f"  {segment}: {st.accuracy:.0%} on {st.n} items")
    print("Weak segments:", weak_segments(data))
    print(f"Overall ECE: {expected_calibration_error(data):.3f}")
    for segment, ece in segment_calibration(data).items():
        print(f"  ECE {segment}: {ece:.3f}")
    sample = stratified_audit_sample(data, rate=0.10, min_confidence=0.90)
    print(f"Audit sample size: {len(sample)} (every segment represented)")

    router = ConfidenceRouter(random_seed=42)
    for item_id, conf, cat in [("doc_001", 0.98, "TaxForm"), ("doc_004", 0.54, "Handwritten")]:
        dec = router.route_item(item_id, conf, cat)
        print(f"{dec.item_id}: {dec.routing_tier.value} - {dec.reason}")


if __name__ == "__main__":
    main()
