"""
Domain 5: Context Management & Reliability
Task Statement 5.3: Propagate Errors Across Multi-Agent Systems and Track Coverage
Exam Scenario 3: Multi-Agent Research System

Key Architectural Concepts:
1. Strict differentiation between VALID_EMPTY (query found 0 items) and UPSTREAM_FAILURE (timeout/500).
2. Subagent structured status propagation.
3. Synthesizer coverage calculation: COMPLETE vs PARTIAL_COVERAGE.
4. Transparent uncertainty disclosure in final executive summaries.
"""

import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class SubagentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    VALID_EMPTY = "VALID_EMPTY"          # Zero records found in functioning system
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"  # Network timeout, 503, database outage
    RATE_LIMITED = "RATE_LIMITED"


@dataclass
class SubagentResult:
    source_name: str
    status: SubagentStatus
    data: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class SynthesisReport:
    coverage_state: str  # "COMPLETE" or "PARTIAL"
    confidence_level: float
    synthesized_insights: List[str]
    source_omissions: List[str]
    degraded_sources: List[str]


class MultiAgentSynthesizer:
    """Aggregates subagent findings with explicit coverage and error tracking."""

    @staticmethod
    def synthesize(subagent_results: List[SubagentResult]) -> SynthesisReport:
        total_sources = len(subagent_results)
        succeeded = 0
        valid_empties = 0
        failures = []
        insights = []

        for res in subagent_results:
            if res.status == SubagentStatus.SUCCESS:
                succeeded += 1
                for item in res.data:
                    insights.append(f"[{res.source_name}] {item.get('title')}: {item.get('summary')}")
            elif res.status == SubagentStatus.VALID_EMPTY:
                valid_empties += 1
                insights.append(f"[{res.source_name}] Confirmed: No matching records found.")
            elif res.status in (SubagentStatus.UPSTREAM_FAILURE, SubagentStatus.RATE_LIMITED):
                failures.append(f"{res.source_name} ({res.status.value}: {res.error_message})")

        # Determine coverage state
        has_failure = len(failures) > 0
        coverage_state = "PARTIAL" if has_failure else "COMPLETE"
        
        # Calculate calibrated confidence: each failed source lowers coverage confidence
        confidence = round((succeeded + valid_empties) / max(1, total_sources), 2)

        return SynthesisReport(
            coverage_state=coverage_state,
            confidence_level=confidence,
            synthesized_insights=insights,
            source_omissions=[f.split()[0] for f in failures],
            degraded_sources=failures
        )


def main() -> None:
    print("=" * 70)
    print("TS 5.3: Error Propagation & Coverage Tracking Demo")
    print("=" * 70)

    # Simulated outputs from 3 research subagents
    subagent_outputs = [
        SubagentResult(
            source_name="SEC_Edgar_Filings",
            status=SubagentStatus.SUCCESS,
            data=[{"title": "10-K Risk Factors", "summary": "Identified supply chain reliance on single supplier."}]
        ),
        SubagentResult(
            source_name="Patent_Office_DB",
            status=SubagentStatus.VALID_EMPTY,  # Legitimate zero matches
            data=[]
        ),
        SubagentResult(
            source_name="Bloomberg_Market_Feed",
            status=SubagentStatus.UPSTREAM_FAILURE,  # Socket timeout!
            error_message="HTTP 504 Gateway Timeout while fetching Q3 earnings"
        )
    ]

    report = MultiAgentSynthesizer.synthesize(subagent_outputs)

    print(f"\nOverall System Coverage: {report.coverage_state}")
    print(f"Confidence Level: {report.confidence_level * 100}%")
    print("\nSynthesized Findings:")
    for insight in report.synthesized_insights:
        print(f"  • {insight}")

    if report.coverage_state == "PARTIAL":
        print("\n⚠️ Mandatory Disclosure of Omitted Sources:")
        for deg in report.degraded_sources:
            print(f"  [DEGRADED]: {deg}")
        print("\nExam Rule Verified: Upstream failure was NOT hallucinated as 'zero market data'!")


if __name__ == "__main__":
    main()
