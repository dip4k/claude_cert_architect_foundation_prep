"""Offline tests for scenario simulation enhancements (no API calls, no network)."""

from scenarios.scenario_1_customer_support.simulation import (
    REFUND_APPROVAL_LIMIT_USD,
    CustomerSupportPipeline,
)
from scenarios.scenario_3_multi_agent_research.simulation import (
    ResearchCoordinator,
    SpecializedSubagent,
    SubagentTaskStatus,
    merge_claims,
)
from scenarios.scenario_5_continuous_integration.simulation import (
    CIPipelineFinding,
    ContinuousIntegrationEngine,
    build_ci_command,
)
from scenarios.scenario_6_structured_data_extraction.simulation import (
    ExtractionRoutingTier,
    StructuredExtractionPipeline,
    build_extraction_request,
    is_retry_eligible,
    validate_against_schema,
)


def test_s1_gate_blocks_gated_tools_with_structured_error() -> None:
    pipe = CustomerSupportPipeline()
    res = pipe.execute_tool("process_refund", order_id="ord_9901")
    assert res["isError"] is True
    assert res["errorCategory"] == "permission"
    assert res["isRetryable"] is False
    assert pipe.execute_tool("get_customer", email="alice@example.com")["action_taken"] == (
        "AUTH_SUCCESS"
    )


def test_s1_refund_over_limit_escalates_in_code() -> None:
    assert REFUND_APPROVAL_LIMIT_USD == 500.0
    pipe = CustomerSupportPipeline()
    pipe.process_customer_turn("My email is bob@example.com")
    res = pipe.process_customer_turn("Refund ord_9903")
    assert res["action_taken"] == "ESCALATED_TO_HUMAN"
    assert pipe.escalation_data is not None
    assert pipe.escalation_data.escalation_type == "THRESHOLD"
    assert pipe.escalation_data.actions_taken == ["get_customer", "process_refund"]


def test_s1_multiple_matches_ask_for_identifier_not_guess() -> None:
    pipe = CustomerSupportPipeline()
    res = pipe.resolve_customer_by_name("Alex Kim")
    assert res["action_taken"] == "ASK_DISAMBIGUATING_IDENTIFIER"
    assert pipe.case_facts.is_authenticated is False
    res = pipe.resolve_customer_by_name("Alex Kim", disambiguator="555-0202")
    assert res["action_taken"] == "AUTH_SUCCESS"
    assert pipe.case_facts.customer_id == "cust_202"


def test_s1_policy_gap_escalates_with_type() -> None:
    pipe = CustomerSupportPipeline()
    res = pipe.process_customer_turn("Can you price match this competitor?")
    assert res["action_taken"] == "ESCALATED_TO_HUMAN"
    assert pipe.escalation_data is not None
    assert pipe.escalation_data.escalation_type == "POLICY_GAP"


def test_s3_decomposition_gap_detected() -> None:
    check = ResearchCoordinator.check_decomposition_coverage(
        ["visual arts", "music", "film"], ["survey visual arts trends", "film AI tools"]
    )
    assert check["is_complete"] is False
    assert check["missing_topics"] == ["music"]


def test_s3_structured_error_and_valid_empty() -> None:
    agent = SpecializedSubagent("patent_agent", "PATENTS")
    failed = agent.execute_isolated_task("q", "timeout")
    err = ResearchCoordinator.error_context_for_coordinator(failed)
    assert err is not None and err["is_retryable"] is True and err["attempted_query"] == "q"
    empty = agent.execute_isolated_task("q", "empty")
    assert empty.status == SubagentTaskStatus.VALID_EMPTY
    assert ResearchCoordinator.error_context_for_coordinator(empty) is None


def test_s3_merge_claims_unions_sources_and_flags_conflicts() -> None:
    def claim(value: str, name: str) -> dict:
        return {"claim": "revenue", "value": value, "source_name": name,
                "source_url": f"https://example.com/{name}", "date": "2024-10-01"}

    merged = merge_claims([claim("$1.2B", "a"), claim("$1.2B", "b"), claim("$1.4B", "c")])
    assert merged[0]["status"] == "CONFLICT"
    by_value = {v["value"]: v for v in merged[0]["values"]}
    assert len(by_value["$1.2B"]["sources"]) == 2
    agreed = merge_claims([claim("$1.2B", "a"), claim("$1.2B", "b")])
    assert agreed[0]["status"] == "AGREED"
    assert ResearchCoordinator.route_verification(True) == "verify_fact"
    assert ResearchCoordinator.route_verification(False) == "coordinator"


def test_s5_ci_command_is_non_interactive_with_schema() -> None:
    cmd = build_ci_command("Review this PR")
    assert cmd[:3] == ["claude", "-p", "Review this PR"]
    assert cmd[cmd.index("--output-format") + 1] == "json"
    assert "--json-schema" in cmd


def test_s5_prior_findings_are_deduped_but_still_block() -> None:
    engine = ContinuousIntegrationEngine()
    files = {"src/a.py": "try:\n    x()\nexcept:\n    pass\n"}
    first = engine.run_two_pass_review(files)
    assert len(first.new_findings) == len(first.findings) == 1
    prior: list[CIPipelineFinding] = list(first.findings)
    second = engine.run_two_pass_review(files, prior_findings=prior)
    assert second.new_findings == []
    assert second.exit_code == 1


def test_s6_request_forces_tool_without_thinking_or_temperature() -> None:
    req = build_extraction_request("Invoice text")
    assert req["model"] == "claude-haiku-4-5"
    assert req["tool_choice"]["type"] == "tool"
    assert "thinking" not in req and "temperature" not in req


def test_s6_nullable_schema_and_validation() -> None:
    ok = {"vendor": "A", "total": 10.0, "tax_id": None, "expense_category": "unclear"}
    assert validate_against_schema(ok) == []
    bad = {"total": "10", "tax_id": None, "expense_category": "gadgets"}
    errors = validate_against_schema(bad)
    assert "missing required field: vendor" in errors
    assert "wrong type for total" in errors
    assert "expense_category not in enum" in errors


def test_s6_retry_eligibility_and_confidence_routing() -> None:
    assert is_retry_eligible(False, True, 0) is True
    assert is_retry_eligible(False, False, 0) is False
    assert is_retry_eligible(False, True, 3) is False
    pipe = StructuredExtractionPipeline(random_seed=1)
    assert pipe.route_by_confidence(0.5)[0] == ExtractionRoutingTier.HUMAN_TRIAGE
    assert pipe.route_by_confidence(0.8)[0] == ExtractionRoutingTier.SECONDARY_SPOT_CHECK
    assert pipe.route_by_confidence(0.95)[0] in (
        ExtractionRoutingTier.STRAIGHT_THROUGH,
        ExtractionRoutingTier.STRATIFIED_AUDIT,
    )
