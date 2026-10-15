"""
Domain 5: Context Management & Reliability
Task Statement 5.6: Track Information Provenance and Synthesize Uncertainty
Exam Scenario 3: Multi-Agent Research System

Key Architectural Concepts:
1. Structured claim-source mapping with date and methodology attribution.
2. Conflict preservation: Never hallucinating an artificial average when sources disagree.
3. Provenance graph formatting for verifiable research reports.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class SourceCitation:
    source_id: str
    publication_date: str
    methodology: str  # e.g., "Preliminary Call", "Audited 10-Q"


@dataclass
class FactClaim:
    metric_name: str
    reported_value: str
    citation: SourceCitation


@dataclass
class ProvenanceSynthesisEntry:
    metric_name: str
    has_conflict: bool
    status: str
    claims: List[Dict[str, Any]]
    synthesized_guidance: str


class ProvenanceSynthesizer:
    """Detects metric discrepancies and preserves conflicting claims transparently."""

    def __init__(self) -> None:
        self.claims: List[FactClaim] = []

    def add_claim(self, metric: str, value: str, source_id: str, date: str, methodology: str) -> None:
        self.claims.append(
            FactClaim(
                metric_name=metric,
                reported_value=value,
                citation=SourceCitation(source_id=source_id, publication_date=date, methodology=methodology)
            )
        )

    def synthesize_metrics(self) -> List[ProvenanceSynthesisEntry]:
        # Group by metric
        grouped: Dict[str, List[FactClaim]] = {}
        for c in self.claims:
            grouped.setdefault(c.metric_name, []).append(c)

        synthesis: List[ProvenanceSynthesisEntry] = []
        for metric, claim_list in grouped.items():
            unique_values = {c.reported_value for c in claim_list}
            has_conflict = len(unique_values) > 1

            claim_dicts = [
                {
                    "source": c.citation.source_id,
                    "date": c.citation.publication_date,
                    "methodology": c.citation.methodology,
                    "value": c.reported_value
                }
                for c in claim_list
            ]

            if has_conflict:
                guidance = (
                    f"Conflicting statistics identified for '{metric}'. "
                    f"Preserved all {len(claim_list)} values with timestamps. Do NOT calculate an average."
                )
                status = "PRESERVED_CONFLICT"
            else:
                guidance = f"Consensus established across {len(claim_list)} sources."
                status = "CONSENSUS"

            synthesis.append(
                ProvenanceSynthesisEntry(
                    metric_name=metric,
                    has_conflict=has_conflict,
                    status=status,
                    claims=claim_dicts,
                    synthesized_guidance=guidance
                )
            )

        return synthesis


def main() -> None:
    print("=" * 70)
    print("TS 5.6: Provenance & Uncertainty Synthesis Demo")
    print("=" * 70)

    synthesizer = ProvenanceSynthesizer()

    # Ingest claims regarding Q3 Revenue
    synthesizer.add_claim(
        metric="Q3 Cloud Revenue",
        value="$1.2 Billion",
        source_id="Press_Release_Wire",
        date="2024-10-01",
        methodology="Preliminary unaudited estimates"
    )
    synthesizer.add_claim(
        metric="Q3 Cloud Revenue",
        value="$1.4 Billion",
        source_id="SEC_10-Q_Filing",
        date="2024-10-15",
        methodology="Audited quarterly balance sheet"
    )

    # Ingest consensus claim
    synthesizer.add_claim(
        metric="Headcount",
        value="12,500 employees",
        source_id="SEC_10-Q_Filing",
        date="2024-10-15",
        methodology="Audited payroll count"
    )

    results = synthesizer.synthesize_metrics()

    print("\n[Synthesized Provenance Report]:")
    for r in results:
        print(f"\nMetric: {r.metric_name}")
        print(f"Status: {r.status} (Conflict: {r.has_conflict})")
        print(f"Guidance: {r.synthesized_guidance}")
        print("Attributed Sources:")
        for c in r.claims:
            print(f"  - {c['source']} ({c['date']} | {c['methodology']}): {c['value']}")

    print("\n" + "=" * 70)
    print("Exam Principle Verified: Conflict was preserved rather than averaged!")


if __name__ == "__main__":
    main()
