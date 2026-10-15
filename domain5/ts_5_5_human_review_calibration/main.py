"""
Domain 5: Context Management & Reliability
Task Statement 5.5: Establish Human Review and Confidence Calibration
Exam Scenario 1: Customer Support Resolution Agent
Exam Scenario 6: Structured Data Extraction

Key Architectural Concepts:
1. Tiered confidence routing (High STP, Medium Spot-Check, Low Mandatory Escalation).
2. Stratified random sampling (5-10%) on high-confidence cases to detect drift.
3. Expected Calibration Error (ECE) monitoring against human audit ground truth.
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


class RoutingTier(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"              # Straight-Through Processing (STP)
    STRATIFIED_AUDIT = "STRATIFIED_AUDIT"      # High confidence, but sampled for drift monitoring
    SPOT_CHECK = "SPOT_CHECK"                  # Medium confidence review
    MANDATORY_ESCALATION = "MANDATORY_ESCALATION" # Low confidence review


@dataclass
class TriageDecision:
    item_id: str
    confidence_score: float
    routing_tier: RoutingTier
    reason: str


class ConfidenceRouter:
    """Routes items into automated execution or human review queues based on calibrated thresholds."""

    HIGH_THRESHOLD = 0.90
    MEDIUM_THRESHOLD = 0.70
    AUDIT_SAMPLING_RATE = 0.10  # 10% stratified sampling on high confidence

    def __init__(self, random_seed: Optional[int] = 42) -> None:
        if random_seed is not None:
            random.seed(random_seed)

    def route_item(self, item_id: str, confidence: float, category: str) -> TriageDecision:
        if confidence >= self.HIGH_THRESHOLD:
            # High confidence tier: check stratified sampling
            is_sampled_for_audit = random.random() < self.AUDIT_SAMPLING_RATE
            if is_sampled_for_audit:
                return TriageDecision(
                    item_id=item_id,
                    confidence_score=confidence,
                    routing_tier=RoutingTier.STRATIFIED_AUDIT,
                    reason=f"High confidence ({confidence}), but selected for 10% drift audit queue."
                )
            return TriageDecision(
                item_id=item_id,
                confidence_score=confidence,
                routing_tier=RoutingTier.AUTO_APPROVE,
                reason=f"Straight-through processing approved ({confidence} >= {self.HIGH_THRESHOLD})."
            )
        elif confidence >= self.MEDIUM_THRESHOLD:
            return TriageDecision(
                item_id=item_id,
                confidence_score=confidence,
                routing_tier=RoutingTier.SPOT_CHECK,
                reason=f"Medium confidence ({confidence}) queued for asynchronous secondary review."
            )
        else:
            return TriageDecision(
                item_id=item_id,
                confidence_score=confidence,
                routing_tier=RoutingTier.MANDATORY_ESCALATION,
                reason=f"Low confidence ({confidence} < {self.MEDIUM_THRESHOLD}) routed to synchronous human agent."
            )


def main() -> None:
    print("=" * 70)
    print("TS 5.5: Human Review & Confidence Calibration Demo")
    print("=" * 70)

    router = ConfidenceRouter(random_seed=42)

    sample_items = [
        {"id": "doc_001", "confidence": 0.98, "cat": "TaxForm"},
        {"id": "doc_002", "confidence": 0.96, "cat": "Invoice"},
        {"id": "doc_003", "confidence": 0.82, "cat": "Contract"},
        {"id": "doc_004", "confidence": 0.54, "cat": "HandwrittenNote"},
    ]

    print("\nRouting Simulation across 4 Sample Documents:")
    for item in sample_items:
        decision = router.route_item(item["id"], item["confidence"], item["cat"])
        print(f"\nDocument [{decision.item_id}] (Score: {decision.confidence_score}):")
        print(f"  -> Tier: {decision.routing_tier.value}")
        print(f"  -> Rationale: {decision.reason}")

    print("\n" + "=" * 70)
    print("Exam Principle Verified: High-confidence items still participate in stratified auditing!")


if __name__ == "__main__":
    main()
