"""
Domain 5: Context Management & Reliability
Task Statement 5.3: Implement error propagation strategies across multi-agent systems
Exam Scenario 3: Multi-Agent Research System

Key Architectural Concepts (all offline, no API calls):
1. Structured error context: failure type, attempted query, partial results, alternatives.
2. Access failure (UPSTREAM_FAILURE) is not a valid empty result (VALID_EMPTY).
3. A generic "search unavailable" hides context; silently returning empty-as-success and
   aborting the whole workflow are both anti-patterns.
4. Subagents recover transient errors locally and propagate only unresolved ones.
5. Synthesis carries coverage annotations so readers know what was not checked.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class SubagentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    VALID_EMPTY = "VALID_EMPTY"  # Zero records found in a functioning system
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"  # Network timeout, 503, database outage
    RATE_LIMITED = "RATE_LIMITED"


class TransientSourceError(Exception):
    """A failure that may succeed on retry (timeout, 503)."""


class PermanentSourceError(Exception):
    """A failure that retrying cannot fix (auth, missing resource)."""


@dataclass
class SubagentResult:
    """Subagent return value; error context is populated only when the status is a failure."""

    source_name: str
    status: SubagentStatus
    data: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    failure_type: Optional[str] = None
    attempted_query: Optional[str] = None
    partial_results: List[Dict[str, Any]] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    attempts: int = 1


@dataclass
class SynthesisReport:
    coverage_state: str  # "COMPLETE" or "PARTIAL"
    confidence_level: float  # share of sources that answered (coverage ratio, not statistics)
    synthesized_insights: List[str]
    source_omissions: List[str]
    degraded_sources: List[str]
    coverage_annotations: List[str] = field(default_factory=list)


def run_subagent_query(
    source_name: str,
    query: str,
    call: Callable[[], List[Dict[str, Any]]],
    max_attempts: int = 3,
    alternatives: Optional[List[str]] = None,
    partial_results: Optional[List[Dict[str, Any]]] = None,
) -> SubagentResult:
    """
    Run one source query with local recovery.

    Transient errors are retried inside the subagent. Only an unresolved failure is returned to
    the coordinator, with enough context (failure type, query, partial results, alternatives)
    to decide what to do next. An empty list from a working source is VALID_EMPTY, not a failure.
    """
    last_error = ""
    failure_type = "TRANSIENT"
    attempts = 0
    for attempts in range(1, max_attempts + 1):
        try:
            rows = call()
        except TransientSourceError as exc:
            last_error, failure_type = str(exc), "TRANSIENT"
            continue
        except PermanentSourceError as exc:
            last_error, failure_type = str(exc), "PERMANENT"
            break
        status = SubagentStatus.SUCCESS if rows else SubagentStatus.VALID_EMPTY
        return SubagentResult(source_name, status, rows, attempts=attempts)
    return SubagentResult(
        source_name=source_name,
        status=SubagentStatus.UPSTREAM_FAILURE,
        error_message=last_error,
        failure_type=failure_type,
        attempted_query=query,
        partial_results=list(partial_results or []),
        alternatives=list(alternatives or []),
        attempts=attempts,
    )


class MultiAgentSynthesizer:
    """Aggregates subagent findings with explicit coverage and error tracking."""

    @staticmethod
    def synthesize(subagent_results: List[SubagentResult]) -> SynthesisReport:
        total_sources = len(subagent_results)
        succeeded = 0
        valid_empties = 0
        failures: List[str] = []
        omitted: List[str] = []
        annotations: List[str] = []
        insights: List[str] = []

        for res in subagent_results:
            if res.status == SubagentStatus.SUCCESS:
                succeeded += 1
                for item in res.data:
                    title, summary = item.get("title"), item.get("summary")
                    insights.append(f"[{res.source_name}] {title}: {summary}")
            elif res.status == SubagentStatus.VALID_EMPTY:
                valid_empties += 1
                insights.append(f"[{res.source_name}] Confirmed: No matching records found.")
            else:
                failures.append(f"{res.source_name} ({res.status.value}: {res.error_message})")
                omitted.append(res.source_name)
                for item in res.partial_results:
                    insights.append(
                        f"[{res.source_name}] (partial) {item.get('title')}: {item.get('summary')}"
                    )
                note = f"NOT CHECKED: {res.source_name} ({res.failure_type or res.status.value})"
                if res.attempted_query:
                    note += f", query '{res.attempted_query}'"
                if res.alternatives:
                    note += f"; alternatives: {', '.join(res.alternatives)}"
                annotations.append(note)

        answered = succeeded + valid_empties
        coverage_state = "PARTIAL" if failures else "COMPLETE"
        if failures:
            annotations.insert(0, f"Coverage: {answered} of {total_sources} sources answered.")

        return SynthesisReport(
            coverage_state=coverage_state,
            confidence_level=round(answered / max(1, total_sources), 2),
            synthesized_insights=insights,
            source_omissions=omitted,
            degraded_sources=failures,
            coverage_annotations=annotations,
        )


def render_report(report: SynthesisReport) -> str:
    """Render findings followed by a coverage section so gaps are never silent."""
    lines = ["## Findings"]
    lines.extend(f"- {i}" for i in report.synthesized_insights)
    if report.coverage_annotations:
        lines.append("\n## Coverage Annotations")
        lines.extend(f"- {a}" for a in report.coverage_annotations)
    return "\n".join(lines)


def main() -> None:
    """Offline demo: one success, one valid empty result, one unrecoverable timeout."""
    print("=" * 70)
    print("TS 5.3: Error Propagation & Coverage Tracking Demo")
    print("=" * 70)

    def edgar() -> List[Dict[str, Any]]:
        return [{"title": "10-K Risk Factors", "summary": "Single-supplier reliance."}]

    def patents() -> List[Dict[str, Any]]:
        return []

    def bloomberg() -> List[Dict[str, Any]]:
        raise TransientSourceError("HTTP 504 Gateway Timeout")

    results = [
        run_subagent_query("SEC_Edgar_Filings", "10-K risk factors", edgar),
        run_subagent_query("Patent_Office_DB", "solid-state battery", patents),
        run_subagent_query(
            "Bloomberg_Market_Feed",
            "Q3 earnings",
            bloomberg,
            alternatives=["retry later", "use cached Q2 feed"],
        ),
    ]
    report = MultiAgentSynthesizer.synthesize(results)
    print(f"\nCoverage state: {report.coverage_state} ({report.confidence_level:.0%} of sources)")
    print(render_report(report))


if __name__ == "__main__":
    main()
