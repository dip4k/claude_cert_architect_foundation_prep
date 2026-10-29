"""
Scenario 3: Multi-Agent Research System
End-to-End System Simulation

Weaves Together:
- TS 1.2: Multi-Agent Coordinator-Subagent Patterns (Hub-and-Spoke)
- TS 1.3: Subagent Invocation, Parallel Spawning, and Context Isolation
- TS 2.4: MCP Server Integration
- TS 5.3: Error Propagation Across Multi-Agent Systems & Coverage Tracking
- TS 5.6: Information Provenance & Preserving Conflicting Claims
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


class SubagentTaskStatus(str, Enum):
    SUCCESS = "SUCCESS"
    VALID_EMPTY = "VALID_EMPTY"          # Zero records found in a functioning system
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"  # 503 / Timeout / Network disconnect


@dataclass
class SubagentTaskResult:
    agent_name: str
    status: SubagentTaskStatus
    extracted_data: List[Dict[str, Any]] = field(default_factory=list)
    error_detail: Optional[str] = None
    structured_error: Optional[Dict[str, Any]] = None  # Context the coordinator needs to recover


@dataclass
class FinalResearchReport:
    topic: str
    coverage_status: str  # "COMPLETE" or "PARTIAL_COVERAGE"
    confidence_score: float
    key_findings: List[str]
    conflicts_preserved: List[Dict[str, Any]]
    source_omissions: List[str]


class SpecializedSubagent:
    """Simulates an isolated subagent with independent context and specific domain focus."""

    def __init__(self, name: str, domain: str) -> None:
        self.name = name
        self.domain = domain

    def execute_isolated_task(self, query: str, mock_backend_behavior: str = "success") -> SubagentTaskResult:
        """Executes a task in a clean context sandbox."""
        if mock_backend_behavior == "timeout":
            return SubagentTaskResult(
                agent_name=self.name,
                status=SubagentTaskStatus.UPSTREAM_FAILURE,
                error_detail="HTTP 504 Gateway Timeout while querying upstream database",
                structured_error={
                    "failure_type": "timeout",
                    "attempted_query": query,
                    "partial_results": [],
                    "is_retryable": True,
                    "alternatives": ["retry with narrower query", "use a different source"],
                },
            )
        elif mock_backend_behavior == "empty":
            return SubagentTaskResult(
                agent_name=self.name,
                status=SubagentTaskStatus.VALID_EMPTY,
                extracted_data=[]
            )
        else:
            # Success with simulated facts
            if self.domain == "SEC_FILINGS":
                return SubagentTaskResult(
                    agent_name=self.name,
                    status=SubagentTaskStatus.SUCCESS,
                    extracted_data=[
                        {"metric": "Q3 Cloud Revenue", "value": "$1.2B", "date": "2024-10-01", "source": "10-Q Preliminary"},
                        {"metric": "Risk Factor", "value": "Single-supplier dependence", "date": "2024-10-01", "source": "Item 1A"}
                    ]
                )
            elif self.domain == "MARKET_INTELLIGENCE":
                return SubagentTaskResult(
                    agent_name=self.name,
                    status=SubagentTaskStatus.SUCCESS,
                    extracted_data=[
                        {"metric": "Q3 Cloud Revenue", "value": "$1.4B", "date": "2024-10-15", "source": "Audited Earnings Release"}
                    ]
                )
            else:
                return SubagentTaskResult(
                    agent_name=self.name,
                    status=SubagentTaskStatus.SUCCESS,
                    extracted_data=[{"metric": "Patents Active", "value": "42", "date": "2024-09-01", "source": "USPTO"}]
                )


class ResearchCoordinator:
    """Hub-and-spoke coordinator managing parallel spawning and synthesis."""

    def __init__(self) -> None:
        self.subagents = {
            "sec_agent": SpecializedSubagent("sec_agent", "SEC_FILINGS"),
            "patent_agent": SpecializedSubagent("patent_agent", "PATENTS"),
            "market_agent": SpecializedSubagent("market_agent", "MARKET_INTELLIGENCE")
        }

    def run_parallel_investigation(
        self,
        topic: str,
        backend_scenarios: Optional[Dict[str, str]] = None
    ) -> FinalResearchReport:
        """
        Spawns subagent tasks in parallel, aggregates findings,
        detects metric conflicts, and evaluates coverage.
        """
        scenarios = backend_scenarios or {}
        task_results: List[SubagentTaskResult] = []

        # Step 1: Parallel Spawning (Emitting multiple Task calls in one turn)
        for agent_key, agent in self.subagents.items():
            behavior = scenarios.get(agent_key, "success")
            # In production, these execute asynchronously; here we simulate parallel dispatch
            res = agent.execute_isolated_task(query=topic, mock_backend_behavior=behavior)
            task_results.append(res)

        # Step 2: Error & Coverage Tracking
        total_subagents = len(task_results)
        successful_subagents = 0
        valid_empty_subagents = 0
        failed_sources = []
        all_datapoints = []

        for r in task_results:
            if r.status == SubagentTaskStatus.SUCCESS:
                successful_subagents += 1
                all_datapoints.extend(r.extracted_data)
            elif r.status == SubagentTaskStatus.VALID_EMPTY:
                valid_empty_subagents += 1
            elif r.status == SubagentTaskStatus.UPSTREAM_FAILURE:
                failed_sources.append(f"{r.agent_name} ({r.error_detail})")

        coverage_status = "PARTIAL_COVERAGE" if failed_sources else "COMPLETE"
        confidence_score = round((successful_subagents + valid_empty_subagents) / total_subagents, 2)

        # Step 3: Provenance Synthesis & Metric Conflict Detection
        metrics_map: Dict[str, List[Dict[str, Any]]] = {}
        for dp in all_datapoints:
            metric = dp.get("metric", "unknown")
            metrics_map.setdefault(metric, []).append(dp)

        findings = []
        conflicts = []

        for metric, points in metrics_map.items():
            distinct_values = {p["value"] for p in points}
            if len(distinct_values) > 1:
                # CONFLICT IDENTIFIED! Never average them!
                conflicts.append({
                    "metric": metric,
                    "resolution": "PRESERVED_BOTH_WITH_TIMESTAMPS",
                    "sources": points,
                    "guidance": f"Disclosed variance: {', '.join([p['source'] + ' reported ' + p['value'] for p in points])}"
                })
                findings.append(f"⚠️ Contested Metric [{metric}]: Multiple authoritative values reported.")
            else:
                findings.append(f"[{metric}]: {points[0]['value']} (Attributed to {points[0]['source']})")

        if valid_empty_subagents > 0:
            findings.append("Verified Finding: Zero active records detected in functioning catalog.")

        return FinalResearchReport(
            topic=topic,
            coverage_status=coverage_status,
            confidence_score=confidence_score,
            key_findings=findings,
            conflicts_preserved=conflicts,
            source_omissions=failed_sources
        )

    @staticmethod
    def check_decomposition_coverage(
        required_topics: List[str], subtasks: List[str]
    ) -> Dict[str, Any]:
        """Flag topics no subtask covers: a narrow decomposition is the coordinator's fault."""
        lowered = [s.lower() for s in subtasks]
        missing = [t for t in required_topics if not any(t.lower() in s for s in lowered)]
        return {
            "is_complete": not missing,
            "missing_topics": missing,
            "covered_topics": [t for t in required_topics if t not in missing],
        }

    @staticmethod
    def route_verification(is_simple_fact_check: bool) -> str:
        """Simple checks use a scoped verify_fact tool; complex ones go via the coordinator."""
        return "verify_fact" if is_simple_fact_check else "coordinator"

    @staticmethod
    def error_context_for_coordinator(result: SubagentTaskResult) -> Optional[Dict[str, Any]]:
        """Return the structured error, or None: valid-empty is not a failure."""
        if result.status == SubagentTaskStatus.UPSTREAM_FAILURE:
            return result.structured_error
        return None


def merge_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge claims by (claim, value): union sources; same claim, new value => conflict.

    Each input needs claim, value, source_url, source_name and date. Values are never averaged.
    """
    by_claim: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for c in claims:
        values = by_claim.setdefault(c["claim"], {})
        entry = values.setdefault(c["value"], {"value": c["value"], "sources": []})
        source = {k: c.get(k) for k in ("source_name", "source_url", "date")}
        if source not in entry["sources"]:
            entry["sources"].append(source)
    return [
        {"claim": claim, "status": "CONFLICT" if len(vals) > 1 else "AGREED",
         "values": list(vals.values())}
        for claim, vals in by_claim.items()
    ]


def main() -> None:
    print("=" * 70)
    print("Scenario 3: Multi-Agent Research System Simulation")
    print("=" * 70)

    coordinator = ResearchCoordinator()

    # Scenario Execution: SEC succeeds, Market succeeds (with conflicting revenue!), Patent experiences 504 timeout
    backend_sim = {
        "sec_agent": "success",
        "market_agent": "success",
        "patent_agent": "timeout"  # Simulated upstream failure
    }

    report = coordinator.run_parallel_investigation("Acme Corp Cloud Competitiveness", backend_sim)

    print(f"\nReport Topic: {report.topic}")
    print(f"Coverage Status: {report.coverage_status}")
    print(f"Confidence Level: {report.confidence_score * 100}%")

    print("\nKey Findings:")
    for f in report.key_findings:
        print(f"  • {f}")

    print("\nPreserved Metric Discrepancies (No Artificial Averaging):")
    for c in report.conflicts_preserved:
        print(f"  Metric: {c['metric']}")
        print(f"  Guidance: {c['guidance']}")

    if report.source_omissions:
        print("\nMandatory Source Outage Disclosures:")
        for o in report.source_omissions:
            print(f"  ❌ {o}")


if __name__ == "__main__":
    main()
