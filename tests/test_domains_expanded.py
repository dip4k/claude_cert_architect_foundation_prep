"""
Comprehensive Test Suite for Domain 2, 3, 4, and 5 Expanded Task Statements.
Runs 100% offline with zero token consumption.
"""

import pytest
from pathlib import Path

# Domain 2 imports
from domain2.ts_2_1_tool_interface_design.main import (
    dispatch_tool,
    get_customer_tool,
    lookup_order_tool,
    TOOLS as D2_TOOLS,
)
from domain2.ts_2_4_mcp_server_integration.main import (
    DeveloperMCPService,
    safe_edit_file,
)

# Domain 3 imports
from domain3.ts_3_1_claude_code_workflows.main import (
    resolve_active_rules_for_file,
    simulate_ci_review_execution,
)

# Domain 4 imports
from domain4.ts_4_5_message_batches_api.main import (
    MessageBatchesEngine,
    BatchRequest,
)

# Domain 5 imports
from domain5.ts_5_2_escalation_and_provenance.main import (
    evaluate_escalation_rules,
    SourceClaim,
    synthesize_conflicting_sources,
)


# ==============================================================================
# Domain 2 Tests: Tool Descriptions, MCP Resources & Fallbacks
# ==============================================================================

def test_d2_tool_description_boundaries():
    assert len(D2_TOOLS) == 2
    get_cust_desc = [t["description"] for t in D2_TOOLS if t["name"] == "get_customer"][0]
    assert "BOUNDARY" in get_cust_desc
    assert "lookup_order instead" in get_cust_desc

    cust_res = dispatch_tool("get_customer", {"identifier": "alice@example.com"})
    assert cust_res["found"] is True
    assert cust_res["customer"]["customer_id"] == "CUST-101"

    order_res = dispatch_tool("lookup_order", {"order_id": "ORD-9821"})
    assert order_res["found"] is True
    assert order_res["order"]["carrier"] == "FedEx"


def test_d2_mcp_resource_read():
    res = DeveloperMCPService.read_resource("catalog://schema/orders")
    assert res is not None
    assert "orders" in res["text"]


def test_d2_safe_edit_fallback(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("x = 1\nx = 1\n", encoding="utf-8")
    # Non-unique anchor -> triggers fallback to Read+Write
    success, msg = safe_edit_file(f, "x = 1", "x = 2")
    assert success is False
    assert "Triggering Read + Write fallback" in msg


# ==============================================================================
# Domain 3 Tests: Path Scoping & Headless CI
# ==============================================================================

def test_d3_path_scoped_rules():
    test_rules = resolve_active_rules_for_file("tests/unit/test_auth.py")
    assert len(test_rules) >= 1
    assert "pytest" in test_rules[0]

    api_rules = resolve_active_rules_for_file("src/api/v1/users.py")
    assert len(api_rules) >= 1
    assert "Pydantic" in api_rules[0]


def test_d3_ci_headless_execution():
    res = simulate_ci_review_execution("+ eval(cmd)", ["rule1"], is_non_interactive=True)
    assert res["status"] == "completed"
    assert res["total_findings"] == 1
    assert res["findings"][0]["severity"] == "CRITICAL"

    with pytest.raises(RuntimeError, match="Missing -p flag"):
        simulate_ci_review_execution("+ eval(cmd)", ["rule1"], is_non_interactive=False)


# ==============================================================================
# Domain 4 Tests: Message Batches Strategy
# ==============================================================================

def test_d4_message_batches_partial_resubmission():
    engine = MessageBatchesEngine()
    reqs = [
        BatchRequest(custom_id="c_1", params={"token_estimate": 1000}),
        BatchRequest(custom_id="c_2", params={"token_estimate": 150_000}),
    ]
    batch_id = engine.submit_batch(reqs)
    failed = engine.filter_failed_for_resubmission(batch_id)
    assert failed == ["c_2"]


# ==============================================================================
# Domain 5 Tests: Escalation Rules & Provenance Synthesis
# ==============================================================================

def test_d5_escalation_rules():
    # Immediate human demand
    dec_human = evaluate_escalation_rules("Please let me speak to a person", 1, True)
    assert dec_human.escalate is True
    assert dec_human.target == "human_supervisor"

    # Ambiguity tie -> prompt for clarification
    dec_tie = evaluate_escalation_rules("Where is my order?", 2, True)
    assert dec_tie.escalate is False
    assert dec_tie.target == "user_clarification"
    assert "Multiple accounts match" in (dec_tie.clarification_prompt or "")

    # Policy gap -> escalate
    dec_gap = evaluate_escalation_rules("Can you price-match a competitor?", 1, False)
    assert dec_gap.escalate is True
    assert dec_gap.target == "human_supervisor"


def test_d5_conflicting_sources_provenance():
    claims = [
        SourceClaim("Metric", "100M", "Source A", "2026-01-01", "Survey"),
        SourceClaim("Metric", "120M", "Source B", "2026-02-01", "Financials"),
    ]
    synth = synthesize_conflicting_sources(claims)
    assert synth["has_contested_findings"] is True
    assert len(synth["claims_with_provenance"]) == 2
    assert "Source A" in synth["synthesis_summary"]
    assert "Source B" in synth["synthesis_summary"]
