"""
Unit tests for Scenario 6: Structured Data Extraction simulation.
Runs 100% offline with zero token costs.
"""

import pytest
from scenarios.scenario_6_structured_data_extraction.simulation import (
    ExtractionRoutingTier,
    StructuredExtractionPipeline,
)


def test_extraction_pipeline_recovers_math_error_via_retry():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Subtotal: $50, Tax: $5, Total: $55, Tax ID: TX-1"
    turns = [
        {"subtotal": 50.0, "tax": 5.0, "total": 50.0, "tax_id": "TX-1"},  # Math mismatch
        {"subtotal": 50.0, "tax": 5.0, "total": 55.0, "tax_id": "TX-1"}   # Corrected
    ]
    outcome = pipeline.process_extraction("d1", doc_text, turns, confidence_score=0.96)
    assert outcome.status == "SUCCESS"
    assert outcome.retries_used == 1
    assert outcome.routing_tier in (
        ExtractionRoutingTier.STRAIGHT_THROUGH,
        ExtractionRoutingTier.STRATIFIED_AUDIT,
    )


def test_extraction_pipeline_aborts_unrecoverable_missing_source_facts():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Simple receipt: Total $10. Paid in cash at diner counter."
    turns = [{"subtotal": 10.0, "tax": 0.0, "total": 10.0, "tax_id": None}]
    outcome = pipeline.process_extraction("d2", doc_text, turns, confidence_score=0.95)
    assert outcome.status == "FAILED_UNRECOVERABLE"
    assert outcome.retries_used == 0  # Did not burn retries!
    assert outcome.routing_tier == ExtractionRoutingTier.HUMAN_TRIAGE
    assert "Aborting retry" in outcome.rationale


def test_extraction_pipeline_low_confidence_routes_to_human_triage():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Blurry scan: Total $100, Tax $10, Subtotal $90, Tax ID: 99"
    turns = [{"subtotal": 90.0, "tax": 10.0, "total": 100.0, "tax_id": "99"}]
    outcome = pipeline.process_extraction("d3", doc_text, turns, confidence_score=0.55)
    assert outcome.status == "SUCCESS"
    assert outcome.routing_tier == ExtractionRoutingTier.HUMAN_TRIAGE


def test_extraction_pipeline_medium_confidence_routes_to_spot_check():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Subtotal: $100, Tax: $10, Total: $110, Tax ID: TX-1"
    turns = [{"subtotal": 100.0, "tax": 10.0, "total": 110.0, "tax_id": "TX-1"}]
    outcome = pipeline.process_extraction("d4", doc_text, turns, confidence_score=0.85)
    assert outcome.status == "SUCCESS"
    assert outcome.routing_tier == ExtractionRoutingTier.SECONDARY_SPOT_CHECK


def test_extraction_pipeline_max_retries_exhausted_routes_to_human_triage():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Subtotal: $100, Tax: $10, Total: $110, Tax ID: TX-1"
    # 3 turns all with persistent math error
    turns = [
        {"subtotal": 100.0, "tax": 10.0, "total": 999.0, "tax_id": "TX-1"},
        {"subtotal": 100.0, "tax": 10.0, "total": 888.0, "tax_id": "TX-1"},
        {"subtotal": 100.0, "tax": 10.0, "total": 777.0, "tax_id": "TX-1"},
    ]
    outcome = pipeline.process_extraction("d5", doc_text, turns, confidence_score=0.95)
    assert outcome.status == "MAX_RETRIES_EXCEEDED"
    assert outcome.routing_tier == ExtractionRoutingTier.HUMAN_TRIAGE
    assert outcome.retries_used == 3


def test_extraction_pipeline_line_items_mismatch_recovers():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Items: Widget ($20), Gadget ($30). Subtotal: $50. Tax: $5. Total: $55. Tax ID: TX-99"
    turns = [
        {
            "subtotal": 50.0, "tax": 5.0, "total": 55.0, "tax_id": "TX-99",
            "line_items": [{"description": "Widget", "total_price": 20.0}, {"description": "Gadget", "total_price": 99.0}]  # 119 != 50
        },
        {
            "subtotal": 50.0, "tax": 5.0, "total": 55.0, "tax_id": "TX-99",
            "line_items": [{"description": "Widget", "total_price": 20.0}, {"description": "Gadget", "total_price": 30.0}]  # 50 == 50
        }
    ]
    outcome = pipeline.process_extraction("d6", doc_text, turns, confidence_score=0.95)
    assert outcome.status == "SUCCESS"
    assert outcome.retries_used == 1


def test_extraction_pipeline_enum_other_requires_detail():
    pipeline = StructuredExtractionPipeline(random_seed=42)
    doc_text = "Special drone inspection service. Total: $500, Tax: $0, Subtotal: $500, Tax ID: TX-5"
    turns = [
        # Turn 1: other category without detail
        {
            "subtotal": 500.0, "tax": 0.0, "total": 500.0, "tax_id": "TX-5",
            "expense_category": "other", "other_category_detail": None
        },
        # Turn 2: corrected with detail
        {
            "subtotal": 500.0, "tax": 0.0, "total": 500.0, "tax_id": "TX-5",
            "expense_category": "other", "other_category_detail": "Aerial drone facility inspection"
        }
    ]
    outcome = pipeline.process_extraction("d7", doc_text, turns, confidence_score=0.95)
    assert outcome.status == "SUCCESS"
    assert outcome.retries_used == 1
    assert outcome.extracted_record["other_category_detail"] == "Aerial drone facility inspection"




