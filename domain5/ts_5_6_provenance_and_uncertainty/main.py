"""
Domain 5: Context Management & Reliability
Task Statement 5.6: Preserve information provenance and handle uncertainty in multi-source
synthesis
Exam Scenario 3: Multi-Agent Research System

Key Architectural Concepts (all offline, no API calls):
1. Claim-source mappings survive summarisation and synthesis (claim, source, excerpt, date).
2. Conflicting statistics are annotated with their sources, never averaged or silently picked.
3. Publication/collection dates (and the period a number describes) stop temporal "contradictions"
   from being reported as conflicts.
4. Reports separate well-established findings from contested ones.
5. Render each content type appropriately: financial = table, news = prose, technical = list.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SourceCitation:
    source_id: str
    publication_date: str
    methodology: str  # e.g. "Preliminary Call", "Audited 10-Q"
    excerpt: str = ""  # verbatim supporting text
    period: Optional[str] = None  # the period the number describes, e.g. "2025-Q3"


@dataclass
class FactClaim:
    metric_name: str
    reported_value: str
    citation: SourceCitation


@dataclass
class ProvenanceSynthesisEntry:
    metric_name: str
    has_conflict: bool
    status: str  # CONSENSUS | PRESERVED_CONFLICT | TEMPORAL_DIFFERENCE
    claims: List[Dict[str, Any]]
    synthesized_guidance: str
    sources_by_value: Dict[str, List[str]] = field(default_factory=dict)


class ProvenanceSynthesizer:
    """Detects metric discrepancies and preserves every claim with its source mapping."""

    def __init__(self) -> None:
        self.claims: List[FactClaim] = []

    def add_claim(
        self,
        metric: str,
        value: str,
        source_id: str,
        date: str,
        methodology: str,
        excerpt: str = "",
        period: Optional[str] = None,
    ) -> None:
        """Record one claim together with its source, dates and methodology."""
        self.claims.append(
            FactClaim(
                metric_name=metric,
                reported_value=value,
                citation=SourceCitation(source_id, date, methodology, excerpt, period),
            )
        )

    def synthesize_metrics(self) -> List[ProvenanceSynthesisEntry]:
        """Group claims by metric and classify them without ever merging values."""
        grouped: Dict[str, List[FactClaim]] = {}
        for c in self.claims:
            grouped.setdefault(c.metric_name, []).append(c)

        synthesis: List[ProvenanceSynthesisEntry] = []
        for metric, claim_list in grouped.items():
            values = {c.reported_value for c in claim_list}
            periods = {c.citation.period for c in claim_list}
            has_conflict = len(values) > 1
            sources_by_value: Dict[str, List[str]] = {}
            for c in claim_list:
                sources_by_value.setdefault(c.reported_value, []).append(c.citation.source_id)

            claim_dicts = [
                {
                    "source": c.citation.source_id,
                    "date": c.citation.publication_date,
                    "period": c.citation.period,
                    "methodology": c.citation.methodology,
                    "excerpt": c.citation.excerpt,
                    "value": c.reported_value,
                }
                for c in claim_list
            ]

            if has_conflict and None not in periods and len(periods) > 1:
                status = "TEMPORAL_DIFFERENCE"
                guidance = (
                    f"Values for '{metric}' describe different periods, so this is a change over "
                    "time, not a contradiction. Present them as a dated timeline."
                )
            elif has_conflict:
                status = "PRESERVED_CONFLICT"
                guidance = (
                    f"Conflicting statistics identified for '{metric}'. "
                    f"Preserved all {len(claim_list)} values with timestamps. "
                    "Do NOT calculate an average."
                )
            else:
                status = "CONSENSUS"
                guidance = f"Consensus established across {len(claim_list)} sources."

            synthesis.append(
                ProvenanceSynthesisEntry(
                    metric_name=metric,
                    has_conflict=has_conflict and status == "PRESERVED_CONFLICT",
                    status=status,
                    claims=claim_dicts,
                    synthesized_guidance=guidance,
                    sources_by_value=sources_by_value,
                )
            )
        return synthesis


def render_claims(claims: List[Dict[str, Any]], content_type: str) -> str:
    """Render claims to suit the content: financial -> table, news -> prose, technical -> list."""
    if content_type == "financial":
        rows = ["| Value | Source | Date | Methodology |", "|---|---|---|---|"]
        rows += [f"| {c['value']} | {c['source']} | {c['date']} | {c['methodology']} |"
                 for c in claims]
        return "\n".join(rows)
    if content_type == "news":
        return " ".join(
            f"{c['source']} reported {c['value']} on {c['date']} ({c['methodology']})."
            for c in claims
        )
    return "\n".join(f"- {c['value']} [{c['source']}, {c['date']}]" for c in claims)


def render_report(
    entries: List[ProvenanceSynthesisEntry], content_types: Optional[Dict[str, str]] = None
) -> str:
    """Report with separate sections for well-established and contested findings."""
    types = content_types or {}
    established = [e for e in entries if e.status != "PRESERVED_CONFLICT"]
    contested = [e for e in entries if e.status == "PRESERVED_CONFLICT"]
    lines = ["## Well-established findings"]
    for e in established:
        lines.append(f"### {e.metric_name} ({e.status})")
        lines.append(render_claims(e.claims, types.get(e.metric_name, "technical")))
    lines.append("\n## Contested findings (sources disagree; both values kept)")
    for e in contested:
        lines.append(f"### {e.metric_name}")
        lines.append(render_claims(e.claims, types.get(e.metric_name, "technical")))
    return "\n".join(lines)


def main() -> None:
    """Offline demo: conflict preserved, temporal change recognised, report sections."""
    print("=" * 70)
    print("TS 5.6: Provenance & Uncertainty Synthesis Demo")
    print("=" * 70)

    synth = ProvenanceSynthesizer()
    synth.add_claim("Q3 Cloud Revenue", "$1.2 Billion", "Press_Release_Wire", "2024-10-01",
                    "Preliminary unaudited estimates", period="2024-Q3")
    synth.add_claim("Q3 Cloud Revenue", "$1.4 Billion", "SEC_10-Q_Filing", "2024-10-15",
                    "Audited quarterly balance sheet", period="2024-Q3")
    synth.add_claim("Headcount", "12,500 employees", "SEC_10-Q_Filing", "2024-10-15",
                    "Audited payroll count")
    synth.add_claim("Inventory", "50,000 units", "Report_A", "2025-06-30", "Warehouse count",
                    period="2025-06")
    synth.add_claim("Inventory", "12,000 units", "Report_B", "2026-09-30", "Warehouse count",
                    period="2026-09")

    entries = synth.synthesize_metrics()
    print(render_report(entries, {"Q3 Cloud Revenue": "financial", "Inventory": "news"}))
    for e in entries:
        print(f"\n{e.metric_name}: {e.status} - {e.synthesized_guidance}")


if __name__ == "__main__":
    main()
