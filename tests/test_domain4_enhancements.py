"""
Offline tests for the Domain 4 enhancements (TS 4.1 - 4.6).

Runs 100% offline with lib.mock_claude. No Anthropic API calls, no tokens.
"""

from typing import Any, Dict, List

import pytest

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse
from lib.response_logger import ResponseTrail

from domain4.ts_4_1_explicit_criteria_classification.main import (
    SKIP_CATEGORIES,
    VAGUE_PROMPT,
    ExplicitCriteriaClassifier,
    build_explicit_prompt,
    vague_prompt_flags,
)
from domain4.ts_4_2_few_shot_and_multi_instance.main import (
    FEW_SHOT_EXTRACTION_EXAMPLES,
    REVIEW_FEW_SHOT_EXAMPLES,
    VARIED_STRUCTURE_EXAMPLES,
    FewShotExample,
    render_few_shot_prompt_block,
    validate_example_count,
)
from domain4.ts_4_3_structured_output_tool_use.main import (
    CATEGORIES,
    EXTRACTION_MODEL,
    EXTRACTION_TOOL,
    build_extraction_request,
    extract_with_validation_retry,
    validate_extraction_detailed,
)
from domain4.ts_4_4_validation_retry_feedback.main import (
    DismissalAnalyzer,
    ErrorKind,
    ExtractionValidator,
    ResilientExtractorLoop,
    RetryAction,
    TrackedFinding,
    build_retry_prompt,
    decide_retry,
)
from domain4.ts_4_5_message_batches_api.main import (
    BatchRequest,
    MessageBatchesEngine,
    batch_cost,
    chunk_failed_requests,
    is_batch_appropriate,
    max_submit_interval_hours,
    original_id,
    requests_needing_followup,
    select_sample,
    submissions_per_day,
    worst_case_turnaround_hours,
)
from domain4.ts_4_6_multi_pass_review.main import (
    FINDING_TOOL_NAME,
    REVIEW_MODEL,
    WORKER_MODEL,
    GeneratorSession,
    LLMMultiPassPipeline,
    ReviewFinding,
    build_independent_review_messages,
    build_review_request,
    build_self_review_messages,
    extract_call_sites,
    route_by_confidence,
    run_review_conversation,
    shares_generator_context,
)


def _tool_response(name: str, data: Dict[str, Any], stop: str = "tool_use") -> MockMessageResponse:
    block = MockContentBlock(block_type="tool_use", name=name, tool_id="toolu_t", input_data=data)
    return MockMessageResponse(content=[block], stop_reason=stop)


def _end(stop: str = "end_turn") -> MockMessageResponse:
    return MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="done")], stop_reason=stop
    )


# ------------------------------------------------------------------ TS 4.1


def test_ts41_disabled_category_is_skipped():
    code = 'cursor.execute(f"SELECT * FROM users WHERE id = {uid}")'
    assert len(ExplicitCriteriaClassifier().evaluate_snippet("src/db.py", code)) == 1
    quiet = ExplicitCriteriaClassifier(disabled_categories={"SQL_INJECTION"})
    assert quiet.evaluate_snippet("src/db.py", code) == []


def test_ts41_explicit_prompt_has_report_skip_and_severity_examples():
    prompt = build_explicit_prompt()
    assert "Report ONLY" in prompt and "Do NOT report" in prompt
    assert SKIP_CATEGORIES[0] in prompt
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        assert f"{level}:" in prompt and "Example:" in prompt
    assert "conservative" in VAGUE_PROMPT.lower()


def test_ts41_vague_flags_mock_but_explicit_does_not():
    test_code = 'mock_key = "sk-ant-test_mock_dummy_0123456789"'
    assert vague_prompt_flags(test_code)
    assert ExplicitCriteriaClassifier().evaluate_snippet("tests/test_auth.py", test_code) == []


def test_ts41_negative_boundary_is_scoped_to_the_matching_line():
    code = 'mock_key = "x"\nreal = "sk-ant-live0123456789abcdef0123456789"'
    findings = ExplicitCriteriaClassifier().evaluate_snippet("tests/test_auth.py", code)
    assert [f.category for f in findings] == ["HARDCODED_SECRET"]
    assert findings[0].detected_pattern


# ------------------------------------------------------------------ TS 4.2


def test_ts42_example_count_is_limited_to_2_to_4():
    one = FEW_SHOT_EXTRACTION_EXAMPLES[:1]
    with pytest.raises(ValueError):
        validate_example_count(one)
    five = [FewShotExample("i", "r", {})] * 5
    with pytest.raises(ValueError):
        render_few_shot_prompt_block(five)
    assert "Example 3" in render_few_shot_prompt_block(VARIED_STRUCTURE_EXAMPLES)


def test_ts42_examples_cover_null_empty_and_acceptable_pattern():
    outputs = [e.target_output for e in FEW_SHOT_EXTRACTION_EXAMPLES]
    assert any(o.get("due_date", 1) is None for o in outputs)
    assert any(e.target_output == {"citations": []} for e in VARIED_STRUCTURE_EXAMPLES)
    reasons = " ".join(e.decision_reasoning for e in REVIEW_FEW_SHOT_EXAMPLES)
    assert "ACCEPTABLE" in reasons and "GENUINE" in reasons
    genuine = REVIEW_FEW_SHOT_EXAMPLES[1].target_output
    assert set(genuine) == {"location", "issue", "severity", "suggested_fix"}


# ------------------------------------------------------------------ TS 4.3


def test_ts43_schema_is_nullable_and_has_unclear_and_other():
    props = EXTRACTION_TOOL["input_schema"]["properties"]
    required = EXTRACTION_TOOL["input_schema"]["required"]
    for name in ("invoice_number", "vendor_name", "issue_date", "due_date", "stated_total"):
        assert "null" in props[name]["type"]
        assert name not in required
    assert "unclear" in CATEGORIES and "other" in CATEGORIES
    assert props["purchase_category"]["enum"] == CATEGORIES
    assert "conflict_detected" in props and "calculated_total" in props


def test_ts43_forced_tool_cannot_be_combined_with_thinking():
    with pytest.raises(ValueError):
        build_extraction_request("doc", tool_choice_mode="tool", thinking_budget=2048)
    with pytest.raises(ValueError):
        build_extraction_request("doc", tool_choice_mode="any", thinking_budget=2048)


def test_ts43_thinking_with_auto_has_no_temperature():
    req = build_extraction_request("doc", tool_choice_mode="auto", thinking_budget=2048)
    assert req["tool_choice"] == {"type": "auto"}
    assert req["thinking"]["budget_tokens"] == 2048
    assert "temperature" not in req and "top_k" not in req and "top_p" not in req
    forced = build_extraction_request("doc")
    assert forced["tool_choice"] == {"type": "tool", "name": "extract_invoice"}
    assert "thinking" not in forced and forced["model"] == EXTRACTION_MODEL


def test_ts43_null_fields_are_absent_not_errors():
    data = {
        "invoice_number": None,
        "vendor_name": None,
        "issue_date": None,
        "purchase_category": "unclear",
        "line_items": [{"description": "x", "quantity": 1, "unit_price": 5.0, "total": 5.0}],
        "stated_total": None,
    }
    result = validate_extraction_detailed(data)
    assert result.is_valid
    assert {"invoice_number", "vendor_name", "issue_date", "stated_total"} <= set(
        result.absent_fields
    )
    assert result.conflict_detected is False


def test_ts43_bad_date_format_is_a_retryable_error_and_conflict_is_flagged():
    data = {
        "issue_date": "October 6, 2026",
        "purchase_category": "hardware",
        "line_items": [{"description": "x", "quantity": 1, "unit_price": 50.0, "total": 50.0}],
        "stated_total": 99.0,
    }
    result = validate_extraction_detailed(data)
    assert not result.is_valid and result.conflict_detected
    assert any("YYYY-MM-DD" in e for e in result.errors)
    assert result.calculated_total == 50.0


def _invoice(total: float) -> Dict[str, Any]:
    return {
        "invoice_number": "INV-1",
        "vendor_name": "ACME",
        "issue_date": "2026-10-06",
        "due_date": None,
        "purchase_category": "consulting",
        "line_items": [{"description": "x", "quantity": 1, "unit_price": 100.0, "total": 100.0}],
        "stated_total": total,
    }


def test_ts43_loop_retries_with_feedback_then_succeeds(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "t.jsonl"))
    client = MockClaudeClient(
        [_tool_response("extract_invoice", _invoice(90.0)), _tool_response("extract_invoice", _invoice(100.0))]
    )
    result = extract_with_validation_retry("doc text", client, trail)
    assert result is not None and result["conflict_detected"] is False
    assert result["due_date"] is None
    second = client.messages.call_history[1]
    assert "does not match" in str(second["messages"][-1]["content"])
    assert second["tool_choice"]["type"] == "tool" and "thinking" not in second
    assert "doc text" in str(second["messages"][0]["content"])


@pytest.mark.parametrize("stop", ["max_tokens", "refusal", "end_turn"])
def test_ts43_loop_stops_on_non_tool_stop_reasons(tmp_path, stop):
    trail = ResponseTrail(path=str(tmp_path / "t.jsonl"))
    client = MockClaudeClient([_end(stop)])
    assert extract_with_validation_retry("doc", client, trail) is None
    assert len(client.messages.call_history) == 1


def test_ts43_pause_turn_continues_without_using_a_retry(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "t.jsonl"))
    client = MockClaudeClient([_end("pause_turn"), _tool_response("extract_invoice", _invoice(100.0))])
    assert extract_with_validation_retry("doc", client, trail, max_retries=0) is not None


# ------------------------------------------------------------------ TS 4.4


def test_ts44_retry_eligibility():
    absent = ExtractionValidator.validate_invoice(
        {"subtotal": 5, "total": 5, "tax_id": None}, "Coffee receipt $5"
    )
    assert absent.error_kind == ErrorKind.ABSENT_IN_SOURCE
    assert decide_retry(absent, 0, 3) == RetryAction.ROUTE_TO_HUMAN

    missed = ExtractionValidator.validate_invoice(
        {"subtotal": 5, "total": 5, "tax_id": None}, "Receipt. VAT ID: GB123"
    )
    assert missed.is_retryable and decide_retry(missed, 0, 3) == RetryAction.RETRY_WITH_FEEDBACK
    assert decide_retry(missed, 3, 3) == RetryAction.GIVE_UP

    ok = ExtractionValidator.validate_invoice(
        {"subtotal": 5, "total": 5, "tax_id": "X"}, "Receipt tax X"
    )
    assert decide_retry(ok, 0, 3) == RetryAction.ACCEPT


def test_ts44_absent_data_is_routed_to_human_without_retry():
    res = ResilientExtractorLoop(3).run_validation_cycle(
        "Lunch receipt $12", [{"subtotal": 12, "total": 12, "tax_id": None}] * 3
    )
    assert res["status"] == "ABORTED_UNRECOVERABLE"
    assert res["route"] == "human_review" and res["retries_used"] == 0


def test_ts44_retry_prompt_has_document_failed_extraction_and_error():
    prompt = build_retry_prompt("ORIGINAL TEXT", {"total": 90}, ["total < subtotal"])
    assert "ORIGINAL TEXT" in prompt and '"total": 90' in prompt and "total < subtotal" in prompt


def test_ts44_conflict_detected_triggers_retry_then_success():
    doc = "Invoice. Tax ID: T1"
    bad = {"subtotal": 100, "total": 100, "tax_id": "T1", "stated_total": 120,
           "line_items": [{"total": 100.0}]}
    good = dict(bad, stated_total=100)
    res = ResilientExtractorLoop(3).run_validation_cycle(doc, [bad, good])
    assert res["status"] == "SUCCESS" and res["retries_used"] == 1
    assert "calculated_total" in res["feedback_log"][0] or "differs" in res["feedback_log"][0]


def test_ts44_detected_pattern_dismissal_analysis():
    analyzer = DismissalAnalyzer()
    for i in range(4):
        analyzer.record(TrackedFinding(f"a{i}", "style", "print_in_cli", dismissed=i < 3))
    for i in range(3):
        analyzer.record(TrackedFinding(f"b{i}", "bug", "none_deref", dismissed=False))
    assert analyzer.dismissal_rates()["print_in_cli"] == 0.75
    assert analyzer.noisy_patterns() == ["print_in_cli"]


# ------------------------------------------------------------------ TS 4.5


def test_ts45_api_shapes_and_lifecycle():
    engine = MessageBatchesEngine()
    reqs = [
        BatchRequest("a-1", {"model": "claude-haiku-4-5", "token_estimate": 10}),
        BatchRequest("b-2", {"simulate": "expired"}),
        BatchRequest("c-3", {"token_estimate": 200_000}),
        BatchRequest("d-4", {"simulate": "canceled"}),
    ]
    batch = engine.create_batch(reqs)
    assert batch["processing_status"] == "in_progress"
    assert batch["request_counts"]["processing"] == 4
    with pytest.raises(RuntimeError):
        engine.results(batch["id"])
    engine.complete(batch["id"])
    ended = engine.retrieve(batch["id"])
    assert ended["processing_status"] == "ended"
    assert ended["request_counts"] == {
        "processing": 0, "succeeded": 1, "errored": 1, "canceled": 1, "expired": 1
    }
    assert {r.type for r in engine.results(batch["id"])} == {
        "succeeded", "errored", "canceled", "expired"
    }
    assert engine.filter_failed_for_resubmission(batch["id"]) == ["b-2", "c-3"]
    assert reqs[0].to_api_dict() == {"custom_id": "a-1", "params": {"model": "claude-haiku-4-5"}}


def test_ts45_custom_id_must_be_valid_and_unique():
    with pytest.raises(ValueError):
        BatchRequest("bad id!", {})
    with pytest.raises(ValueError):
        MessageBatchesEngine().create_batch([BatchRequest("x", {}), BatchRequest("x", {})])


def test_ts45_tools_do_not_execute_mid_batch():
    engine = MessageBatchesEngine()
    tools = [{"name": "lookup_order"}]
    bid = engine.submit_batch([BatchRequest("t-1", {"tools": tools}), BatchRequest("t-2", {})])
    results = engine.results(bid)
    assert requests_needing_followup(results) == ["t-1"]
    msg = results[0].result["message"]
    assert msg["stop_reason"] == "tool_use"
    assert all(b["type"] != "tool_result" for b in msg["content"])


def test_ts45_sla_helpers():
    assert max_submit_interval_hours(30, 24, 0) == 6
    assert max_submit_interval_hours(30, 24, 2) == 4
    assert worst_case_turnaround_hours(4, 24, 2) == 30
    assert submissions_per_day(4) == 6
    with pytest.raises(ValueError):
        max_submit_interval_hours(24, 24, 0)


def test_ts45_resubmit_only_failed_ids_and_chunk_oversized_docs():
    engine = MessageBatchesEngine()
    reqs = [
        BatchRequest("doc-1", {"token_estimate": 1_000}),
        BatchRequest("doc-2", {"token_estimate": 150_000}),
        BatchRequest("doc-3", {"simulate": "expired", "token_estimate": 500}),
    ]
    bid = engine.submit_batch(reqs)
    retry = chunk_failed_requests(reqs, engine.filter_failed_for_resubmission(bid))
    ids = [r.custom_id for r in retry]
    assert "doc-1" not in ids and "doc-3" in ids
    chunks = [i for i in ids if i.startswith("doc-2-chunk")]
    assert chunks == ["doc-2-chunk1of3", "doc-2-chunk2of3", "doc-2-chunk3of3"]
    assert {original_id(i) for i in ids} == {"doc-2", "doc-3"}
    assert all(r.params["token_estimate"] <= 50_000 for r in retry)
    retry_engine = MessageBatchesEngine()
    rid = retry_engine.submit_batch(retry)
    assert retry_engine.filter_failed_for_resubmission(rid) == []  # all retries now succeed


def test_ts45_workload_fit_sample_and_cost():
    assert is_batch_appropriate(blocking=False, max_wait_hours=24) is True
    assert is_batch_appropriate(blocking=True, max_wait_hours=24) is False  # pre-merge check
    assert is_batch_appropriate(blocking=False, max_wait_hours=1) is False
    reqs = [BatchRequest(f"r{i}", {}) for i in range(100)]
    sample = select_sample(reqs, 10)
    assert len(sample) == 10 and sample[0].custom_id == "r0"
    assert batch_cost(100.0) == 50.0


# ------------------------------------------------------------------ TS 4.6


def test_ts46_self_review_sees_author_reasoning_independent_does_not():
    session = GeneratorSession("Write auth", "I chose a 60 minute cache because it is fast.", "code")
    own = build_self_review_messages(session)
    fresh = build_independent_review_messages(session.code, ["bugs"])
    assert shares_generator_context(own, session) is True
    assert shares_generator_context(fresh, session) is False
    assert len(fresh) == 1 and len(own) == 3


def _finding(file: str, sev: str, conf: float, line: int = 3) -> Dict[str, Any]:
    return {
        "file": file, "line": line, "severity": sev, "description": "d",
        "remediation": "r", "confidence": conf,
    }


def test_ts46_pipeline_passes_use_fresh_context_and_route_by_confidence():
    client = MockClaudeClient(
        [
            _tool_response(FINDING_TOOL_NAME, _finding("auth_api.py", "HIGH", 0.9)),
            _end(),
            _end(),
            _tool_response(FINDING_TOOL_NAME, _finding("auth_client.py", "CRITICAL", 0.5)),
            _end(),
        ]
    )
    codebase = {
        "auth_api.py": "def verify_session(bearer_token):\n    pass\n",
        "auth_client.py": "def login():\n    return verify_session(auth_token='x')\n",
    }
    report = LLMMultiPassPipeline(client).run_review(codebase)
    assert report["pass_1_local_count"] == 1 and report["pass_2_integration_count"] == 1
    assert report["approved"] is False
    assert report["auto_report_count"] == 1 and report["human_review_count"] == 1
    assert report["total_findings"] == 2  # low confidence is routed, never dropped

    history = client.messages.call_history
    assert [h["model"] for h in history[:3]] == [WORKER_MODEL] * 3
    assert history[3]["model"] == REVIEW_MODEL
    file2_call = history[2]["messages"]
    assert len(file2_call) == 1 and "auth_api" not in str(file2_call)  # no cross-file leakage
    integration = str(history[3]["messages"])
    assert "verify_session(auth_token" in integration and "interfaces" in integration
    assert extract_call_sites(codebase) == ["auth_client.py: return verify_session(auth_token='x')"]


def test_ts46_stop_reasons_are_handled_explicitly():
    msgs = build_independent_review_messages("code", ["bugs"])
    cut = run_review_conversation(MockClaudeClient([_end("max_tokens")]), WORKER_MODEL, "s", msgs, "FILE_LOCAL")
    assert cut.truncated and not cut.findings
    ref = run_review_conversation(MockClaudeClient([_end("refusal")]), WORKER_MODEL, "s", msgs, "FILE_LOCAL")
    assert ref.refused
    paused = MockClaudeClient(
        [_end("pause_turn"), _tool_response(FINDING_TOOL_NAME, _finding("a.py", "LOW", 0.9)), _end()]
    )
    out = run_review_conversation(paused, WORKER_MODEL, "s", msgs, "FILE_LOCAL")
    assert len(out.findings) == 1 and out.findings[0].target_component == "a.py:3"


def test_ts46_thinking_requires_auto_tool_choice_and_no_temperature():
    msgs = build_independent_review_messages("code", ["bugs"])
    plain = build_review_request(WORKER_MODEL, "s", msgs, use_thinking=False)
    assert plain["tool_choice"] == {"type": "any"} and "thinking" not in plain
    thinking = build_review_request(REVIEW_MODEL, "s", msgs, use_thinking=True)
    assert thinking["tool_choice"] == {"type": "auto"}
    assert thinking["thinking"]["budget_tokens"] < thinking["max_tokens"]
    assert "temperature" not in thinking and "temperature" not in plain


def test_ts46_route_by_confidence_keeps_missing_confidence_for_humans():
    findings: List[ReviewFinding] = [
        ReviewFinding("FILE_LOCAL", "HIGH", "a", "d", "r", 0.95),
        ReviewFinding("FILE_LOCAL", "HIGH", "b", "d", "r", 0.4),
        ReviewFinding("FILE_LOCAL", "HIGH", "c", "d", "r", None),
    ]
    routed = route_by_confidence(findings, threshold=0.7)
    assert [f.target_component for f in routed["auto_report"]] == ["a"]
    assert [f.target_component for f in routed["human_review"]] == ["b", "c"]
