"""
Offline Unit Tests for Domain Certification Practice Exercises.

Runs 100% offline using lib.mock_claude. Zero Anthropic API tokens or costs.
"""

import json
import pytest
from lib.mock_claude import (
    MockClaudeClient,
    MockMessageResponse,
    MockContentBlock,
)
from lib.response_logger import ResponseTrail

# Domain 1 imports
from domain1.ts_1_4_prerequisite_enforcement.main import (
    WorkflowState,
    get_customer,
    lookup_order,
    process_refund,
    escalate_to_human,
    run_prerequisite_agent,
)

# Domain 2 imports
from domain2.ts_2_2_mcp_structured_errors.main import (
    query_inventory,
    issue_refund,
    create_mcp_error,
)

# Domain 4 imports
from domain4.ts_4_3_structured_output_tool_use.main import (
    validate_extraction,
    extract_with_validation_retry,
)

# Domain 5 imports
from domain5.ts_5_1_context_preservation.main import (
    CaseFacts,
    trim_order_output,
    RAW_ORDER_PAYLOAD,
    lookup_order_tool,
)


# ==============================================================================
# Domain 1 Tests: Prerequisite Enforcement & Programmatic Gates
# ==============================================================================

def test_prerequisite_gate_blocks_unverified_refund():
    state = WorkflowState()
    # Before verification, gate must block refund
    allowed, err = state.check_gate("process_refund", {"order_id": "ORD-991", "amount": 50.0})
    assert allowed is False
    assert err is not None
    assert err["isError"] is True
    assert err["errorCategory"] == "permission"
    assert err["isRetryable"] is False


def test_prerequisite_gate_allows_after_verification():
    state = WorkflowState()
    # Verify customer
    res = get_customer("alice@example.com", state)
    assert res["found"] is True
    assert state.verified_customer_id == "CUST-101"

    # Now refund gate must allow execution
    allowed, err = state.check_gate("process_refund", {"order_id": "ORD-991", "amount": 85.0})
    assert allowed is True
    assert err is None


def test_escalate_to_human_structured_summary():
    state = WorkflowState()
    state.verify_customer("CUST-999", "Charlie")
    res = escalate_to_human("Customer dissatisfied with return policy", "Issue courtesy credit", state)
    assert res["escalated"] is True
    summary = res["summary"]
    assert summary["customer_id"] == "CUST-999"
    assert summary["root_cause"] == "Customer dissatisfied with return policy"
    assert "recommended_action" in summary


def test_run_prerequisite_agent_offline(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts14_trail.jsonl"))

    # Turn 1: get_customer
    resp_t1 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="get_customer",
                tool_id="call_c1",
                input_data={"email": "alice@example.com"},
            )
        ],
        stop_reason="tool_use",
    )

    # Turn 2: process_refund
    resp_t2 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="process_refund",
                tool_id="call_r1",
                input_data={"order_id": "ORD-991", "amount": 85.0},
            )
        ],
        stop_reason="tool_use",
    )

    # Turn 3: final answer
    resp_t3 = MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="Your refund for ORD-991 has been processed.")],
        stop_reason="end_turn",
    )

    client = MockClaudeClient([resp_t1, resp_t2, resp_t3])
    text, state = run_prerequisite_agent(
        prompt="Hi, refund order ORD-991 for alice@example.com",
        client=client,
        trail=trail,
    )
    assert "refund for ORD-991 has been processed" in text
    assert state.verified_customer_id == "CUST-101"


# ==============================================================================
# Domain 2 Tests: MCP Structured Error Responses
# ==============================================================================

def test_mcp_transient_error():
    res = query_inventory("SKU-101", simulate_mode="timeout")
    assert res["isError"] is True
    assert res["errorCategory"] == "transient"
    assert res["isRetryable"] is True


def test_mcp_validation_error():
    res = query_inventory("INVALID_SKU")
    assert res["isError"] is True
    assert res["errorCategory"] == "validation"
    assert res["isRetryable"] is False


def test_mcp_valid_empty_result_is_not_error():
    res = query_inventory("SKU-99999")
    # Must distinguish access failure from valid empty result
    assert res["isError"] is False
    assert res["stock_count"] == 0
    assert res["is_empty_result"] is True


def test_mcp_business_rule_error():
    res = issue_refund("CUST-100", 650.00)
    assert res["isError"] is True
    assert res["errorCategory"] == "business"
    assert res["isRetryable"] is False
    assert "exceeds automated policy threshold" in res["message"]


# ==============================================================================
# Domain 4 Tests: Structured Output & Validation Retry
# ==============================================================================

def test_validation_arithmetic_mismatch():
    invalid_data = {
        "invoice_number": "INV-001",
        "vendor_name": "Acme",
        "issue_date": "2026-10-06",
        "purchase_category": "hardware",
        "line_items": [{"description": "Item A", "quantity": 1, "unit_price": 50.0, "total": 50.0}],
        "stated_total": 99.0,  # Mismatch!
    }
    valid, errors = validate_extraction(invalid_data)
    assert valid is False
    assert any("does not match stated invoice total" in err for err in errors)


def test_validation_missing_other_category_detail():
    data = {
        "invoice_number": "INV-002",
        "vendor_name": "Beta",
        "issue_date": "2026-10-06",
        "purchase_category": "other",
        "other_category_detail": None,  # Missing!
        "line_items": [{"description": "Custom", "quantity": 1, "unit_price": 10.0, "total": 10.0}],
        "stated_total": 10.0,
    }
    valid, errors = validate_extraction(data)
    assert valid is False
    assert any("other_category_detail" in err and "must be provided" in err for err in errors)


def test_extract_with_validation_retry_offline(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "extract_trail.jsonl"))

    valid_invoice = {
        "invoice_number": "INV-2026-001",
        "vendor_name": "ACME Cloud",
        "issue_date": "2026-10-06",
        "due_date": None,  # Nullable field
        "purchase_category": "software_subscription",
        "other_category_detail": None,
        "line_items": [
            {"description": "Cloud Instance", "quantity": 1, "unit_price": 100.0, "total": 100.0}
        ],
        "stated_total": 100.0,
    }

    mock_resp = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="extract_invoice",
                tool_id="call_inv1",
                input_data=valid_invoice,
            )
        ],
        stop_reason="tool_use",
    )

    client = MockClaudeClient([mock_resp])
    result = extract_with_validation_retry("Some document text", client, trail)
    assert result is not None
    assert result["invoice_number"] == "INV-2026-001"
    assert result["stated_total"] == 100.0


# ==============================================================================
# Domain 5 Tests: Context Preservation & Trimming
# ==============================================================================

def test_trim_order_output():
    trimmed = trim_order_output(RAW_ORDER_PAYLOAD)
    assert "warehouse_rack_id" not in trimmed
    assert "carrier_tracking_code" not in trimmed
    assert "payment_gateway_auth_token" not in trimmed
    assert trimmed["order_id"] == "ORD-2026-9921"
    assert trimmed["amount"] == 149.99


def test_case_facts_immutability():
    facts = CaseFacts(customer_id="CUST-441", customer_email="alice@test.com")
    prompt_block = facts.render_prompt_block()
    assert "### PERSISTENT CASE FACTS" in prompt_block
    assert "CUST-441" in prompt_block

    # Tool execution updates facts
    lookup_order_tool("ORD-2026-9921", facts)
    updated_block = facts.render_prompt_block()
    assert "ORD-2026-9921" in updated_block
    assert "$149.99" in updated_block
