"""
Unit tests for Scenario 3: Multi-Agent Research System simulation.
Runs 100% offline with zero token costs.
"""

import pytest
from scenarios.scenario_3_multi_agent_research.simulation import (
    ResearchCoordinator,
    SubagentTaskStatus,
)


def test_research_coordinator_complete_coverage_and_consensus():
    coord = ResearchCoordinator()
    # All subagents succeed cleanly without conflict
    report = coord.run_parallel_investigation(
        "AI Chip Market",
        {"sec_agent": "success", "market_agent": "empty", "patent_agent": "success"}
    )
    assert report.coverage_status == "COMPLETE"
    assert report.confidence_score == 1.0
    assert len(report.source_omissions) == 0


def test_research_coordinator_handles_upstream_failure_and_partial_coverage():
    coord = ResearchCoordinator()
    report = coord.run_parallel_investigation(
        "Quantum Security",
        {"sec_agent": "success", "market_agent": "success", "patent_agent": "timeout"}
    )
    # Coverage must be flagged as PARTIAL
    assert report.coverage_status == "PARTIAL_COVERAGE"
    assert report.confidence_score < 1.0
    assert any("patent_agent" in o for o in report.source_omissions)


def test_research_coordinator_preserves_conflicting_statistics_without_averaging():
    coord = ResearchCoordinator()
    # Both SEC and Market succeed with different revenues ($1.2B vs $1.4B)
    report = coord.run_parallel_investigation(
        "Acme Corp Earnings",
        {"sec_agent": "success", "market_agent": "success", "patent_agent": "empty"}
    )
    assert len(report.conflicts_preserved) == 1
    conflict = report.conflicts_preserved[0]
    assert conflict["metric"] == "Q3 Cloud Revenue"
    assert conflict["resolution"] == "PRESERVED_BOTH_WITH_TIMESTAMPS"
    # Verify that both numbers exist in disclosure
    assert "$1.2B" in conflict["guidance"]
    assert "$1.4B" in conflict["guidance"]


def test_research_coordinator_valid_empty_counts_as_complete_coverage():
    coord = ResearchCoordinator()
    # When patent agent returns VALID_EMPTY and other agents succeed
    report = coord.run_parallel_investigation(
        "Startup Bio",
        {"sec_agent": "success", "market_agent": "success", "patent_agent": "empty"}
    )
    # VALID_EMPTY is NOT an error, so coverage remains COMPLETE
    assert report.coverage_status == "COMPLETE"
    assert report.confidence_score == 1.0
    assert len(report.source_omissions) == 0


def test_research_coordinator_all_upstreams_fail_produces_zero_confidence():
    coord = ResearchCoordinator()
    # All subagents timeout
    report = coord.run_parallel_investigation(
        "Unavailable Corp",
        {"sec_agent": "timeout", "market_agent": "timeout", "patent_agent": "timeout"}
    )
    assert report.coverage_status == "PARTIAL_COVERAGE"
    assert report.confidence_score == 0.0
    assert len(report.source_omissions) == 3


def test_research_coordinator_all_subagents_valid_empty():
    coord = ResearchCoordinator()
    # All subagents legitimately find 0 records
    report = coord.run_parallel_investigation(
        "Dormant Shell Corp",
        {"sec_agent": "empty", "market_agent": "empty", "patent_agent": "empty"}
    )
    assert report.coverage_status == "COMPLETE"
    assert report.confidence_score == 1.0
    assert len(report.source_omissions) == 0
    assert any("Zero active records detected" in f for f in report.key_findings)


