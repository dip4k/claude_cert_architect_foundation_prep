"""
Unit tests for Scenario 1: Customer Support Resolution Agent simulation.
Runs 100% offline with zero token costs.
"""

import pytest
from scenarios.scenario_1_customer_support.simulation import CustomerSupportPipeline


def test_customer_support_auth_gate_blocks_unauthenticated_order_lookup():
    pipeline = CustomerSupportPipeline()
    res = pipeline.process_customer_turn("Please check ord_9901")
    assert res["action_taken"] == "GATE_BLOCKED_UNAUTHENTICATED"
    assert pipeline.case_facts.is_authenticated is False


def test_customer_support_happy_path_with_context_trimming():
    pipeline = CustomerSupportPipeline()
    # 1. Auth
    pipeline.process_customer_turn("My email is alice@example.com")
    assert pipeline.case_facts.is_authenticated is True
    assert pipeline.case_facts.customer_id == "cust_101"

    # 2. Lookup order
    res = pipeline.process_customer_turn("Look up ord_9901")
    assert res["action_taken"] == "ORDER_FOUND_TRIMMED"
    order_data = res["order_data"]
    # Check that bloat fields were eliminated:
    assert "_internal_warehouse_id" not in order_data
    assert "_carrier_internal_audit_log" not in order_data
    assert order_data["status"] == "DELIVERED"

    # 3. Process refund within 30 days
    refund_res = pipeline.process_customer_turn("Please issue the refund.")
    assert refund_res["action_taken"] == "REFUND_SUCCESS"
    assert refund_res["amount_refunded"] == 79.99


def test_customer_support_immediate_human_escalation():
    pipeline = CustomerSupportPipeline()
    res = pipeline.process_customer_turn("I want to speak to a human right now.")
    assert res["action_taken"] == "ESCALATED_TO_HUMAN"
    assert pipeline.escalated is True
    assert "Customer explicit demand" in pipeline.escalation_data.reason


def test_customer_support_policy_exception_escalates():
    pipeline = CustomerSupportPipeline()
    pipeline.process_customer_turn("Email is alice@example.com")
    # ord_9902 was delivered 45 days ago (> 30 days window)
    pipeline.process_customer_turn("Lookup ord_9902")
    refund_res = pipeline.process_customer_turn("Process refund for ord_9902")
    assert refund_res["action_taken"] == "ESCALATED_TO_HUMAN"
    assert "Policy exception" in pipeline.escalation_data.reason


def test_customer_support_blocks_unauthorized_order_access():
    pipeline = CustomerSupportPipeline()
    # Log in as Bob (cust_102)
    pipeline.process_customer_turn("My email is bob@example.com")
    assert pipeline.case_facts.customer_id == "cust_102"
    # Try to access Alice's order (cust_101)
    res = pipeline.process_customer_turn("Look up ord_9901")
    assert res["action_taken"] == "SECURITY_VIOLATION_BLOCKED"
    assert "not belong to your verified account" in res["agent_reply"]


def test_customer_support_handles_unknown_account():
    pipeline = CustomerSupportPipeline()
    res = pipeline.process_customer_turn("My email is unknown_user@domain.com")
    assert res["action_taken"] == "AUTH_FAILED"
    assert pipeline.case_facts.is_authenticated is False


def test_customer_support_multi_order_pivot_and_prompt_when_missing():
    pipeline = CustomerSupportPipeline()
    pipeline.process_customer_turn("My email is alice@example.com")

    # Ask for refund without any active order
    res_no_order = pipeline.process_customer_turn("I need a refund please.")
    assert res_no_order["action_taken"] == "PROMPT_ORDER_ID"

    # Lookup first order
    pipeline.process_customer_turn("Look up ord_9901")
    assert pipeline.case_facts.active_order_id == "ord_9901"

    # Pivot to second order
    pipeline.process_customer_turn("Actually check ord_9902")
    assert pipeline.case_facts.active_order_id == "ord_9902"


