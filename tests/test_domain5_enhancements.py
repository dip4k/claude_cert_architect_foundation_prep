"""
Offline tests for the Domain 5 enhancements (TS 5.1 - 5.6). No Claude API calls.
"""

import json
import random
from pathlib import Path

from domain5.ts_5_1_context_preservation.main import (
    RAW_ORDER_PAYLOAD,
    CaseFacts,
    SubagentFinding,
    approx_tokens,
    assemble_context,
    extract_case_facts,
    facts_survive,
    lossy_summary,
    render_aggregated_findings,
    trim_order_output,
)
from domain5.ts_5_2_escalation_and_provenance.main import (
    build_escalation_prompt,
    evaluate_escalation_rules,
    resolve_customer,
)
from domain5.ts_5_3_error_propagation_coverage.main import (
    MultiAgentSynthesizer,
    PermanentSourceError,
    SubagentStatus,
    TransientSourceError,
    render_report,
    run_subagent_query,
)
from domain5.ts_5_4_scratchpads_and_human_review.main import (
    CodebaseScratchpadManager,
    CrashRecoveryManifest,
    explore_subagent,
)
from domain5.ts_5_5_human_review_calibration.main import (
    ConfidenceRouter,
    FieldExtraction,
    RoutingTier,
    aggregate_accuracy,
    demo_validation_set,
    expected_calibration_error,
    safe_to_reduce_review,
    segment_calibration,
    stratified_audit_sample,
    weak_segments,
)
from domain5.ts_5_6_provenance_and_uncertainty.main import (
    ProvenanceSynthesizer,
    render_claims,
    render_report as render_provenance_report,
)

# ==============================================================================
# TS 5.1: case facts, trimming, layout
# ==============================================================================


def test_case_facts_survive_summary_drift() -> None:
    facts = CaseFacts()
    msg = "Refund ORD-2026-9921, I paid $149.99 on 2026-09-28."
    extract_case_facts(msg, facts)
    summary = lossy_summary(msg)
    assert not facts_survive(summary, facts)
    ctx = assemble_context(facts, summary, [], "Where is my refund?")
    assert facts_survive(ctx["system"], facts)
    assert ctx["messages"][-1]["content"] == "Where is my refund?"


def test_extract_case_facts_keeps_conflicting_amount_as_note() -> None:
    facts = CaseFacts()
    extract_case_facts("I paid $100.00", facts)
    extract_case_facts("Actually it was $120.00", facts)
    assert facts.refund_requested == 100.0
    assert any("120.00" in note for note in facts.custom_notes)


def test_trimming_reduces_forty_plus_fields_to_five() -> None:
    assert len(RAW_ORDER_PAYLOAD) >= 40
    trimmed = trim_order_output(RAW_ORDER_PAYLOAD)
    assert len(trimmed) == 5
    assert approx_tokens(trimmed) < approx_tokens(RAW_ORDER_PAYLOAD) / 4


def test_aggregated_findings_put_key_findings_first_with_headers() -> None:
    findings = [
        SubagentFinding("Minor note", "SrcB", "2026-01-01", 0.2),
        SubagentFinding("Major result", "SrcA", "2026-02-01", 0.9),
    ]
    text = render_aggregated_findings(findings, top_n=1)
    assert text.startswith("## KEY FINDINGS")
    assert text.index("Major result") < text.index("## DETAIL: SrcA")
    assert "## DETAIL: SrcB" in text


# ==============================================================================
# TS 5.2: escalation criteria
# ==============================================================================


def test_frustration_alone_is_acknowledged_not_escalated() -> None:
    dec = evaluate_escalation_rules("This is so frustrating, refund is late", 1, True)
    assert dec.escalate is False
    assert dec.acknowledge_frustration is True
    assert dec.target == "autonomous_resolution"


def test_human_request_beats_investigation_and_no_progress_escalates() -> None:
    assert evaluate_escalation_rules("Get me a supervisor", 2, True).escalate is True
    stuck = evaluate_escalation_rules("Please help", 1, True, within_capability=False)
    assert stuck.escalate is True


def test_resolve_customer_never_guesses() -> None:
    matches = [{"id": "A1", "email": "a@x.com"}, {"id": "A2", "email": "b@x.com"}]
    assert resolve_customer(matches)["status"] == "needs_identifier"
    assert resolve_customer(matches, "b@x.com")["customer"]["id"] == "A2"
    assert resolve_customer(matches, "zzz")["status"] == "not_found"


def test_escalation_prompt_has_criteria_and_examples() -> None:
    prompt = build_escalation_prompt()
    assert "EXAMPLES" in prompt and "price" in prompt.lower()
    assert "Do NOT use sentiment" in prompt


# ==============================================================================
# TS 5.3: structured errors and coverage annotations
# ==============================================================================


def test_transient_error_recovered_locally() -> None:
    calls = {"n": 0}

    def flaky() -> list:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientSourceError("503")
        return [{"title": "T", "summary": "S"}]

    res = run_subagent_query("Src", "q", flaky, max_attempts=3)
    assert res.status == SubagentStatus.SUCCESS
    assert res.attempts == 3


def test_unresolved_failure_carries_structured_context() -> None:
    def down() -> list:
        raise PermanentSourceError("403 forbidden")

    res = run_subagent_query("Src", "revenue 2025", down, alternatives=["use cache"])
    assert res.status == SubagentStatus.UPSTREAM_FAILURE
    assert res.failure_type == "PERMANENT"
    assert res.attempted_query == "revenue 2025"
    assert res.alternatives == ["use cache"]
    assert res.attempts == 1


def test_valid_empty_is_not_a_failure_and_coverage_is_annotated() -> None:
    ok = run_subagent_query("A", "q", lambda: [{"title": "x", "summary": "y"}])
    empty = run_subagent_query("B", "q", lambda: [])

    def timeout() -> list:
        raise TransientSourceError("504")

    failed = run_subagent_query("C", "q3", timeout, max_attempts=2, alternatives=["retry later"])
    assert empty.status == SubagentStatus.VALID_EMPTY
    report = MultiAgentSynthesizer.synthesize([ok, empty, failed])
    assert report.coverage_state == "PARTIAL"
    assert report.source_omissions == ["C"]
    text = render_report(report)
    assert "Coverage: 2 of 3 sources answered." in text
    assert "NOT CHECKED: C" in text and "retry later" in text
    full = MultiAgentSynthesizer.synthesize([ok, empty])
    assert full.coverage_state == "COMPLETE" and full.coverage_annotations == []


# ==============================================================================
# TS 5.4: scratchpad, explore subagent, manifest recovery
# ==============================================================================


def test_explore_subagent_returns_compact_summary() -> None:
    files = {f"f{i}.py": "\n".join(f"line {j}" for j in range(50)) for i in range(5)}
    files["auth.py"] = "class TokenVerifier:\n    pass"
    summary = explore_subagent(files, "class TokenVerifier")
    assert summary.files_scanned == 6 and summary.raw_lines_seen > 250
    assert [f["file"] for f in summary.findings] == ["auth.py"]


def test_scratchpad_round_trip(tmp_path: Path) -> None:
    pad = CodebaseScratchpadManager()
    pad.record_finding("DB layer is MySQL")
    pad.record_finding("Refunds live in OrderService")
    path = tmp_path / "scratchpad.md"
    pad.save(path)
    assert CodebaseScratchpadManager.load(path).findings == pad.findings


def test_manifest_recovery_after_crash(tmp_path: Path) -> None:
    run = CrashRecoveryManifest(tmp_path / "state")
    run.export_agent_state("auth-explorer", "discovery", ["TokenVerifier in auth.py"])
    # A new process (new object) resumes from disk only.
    resumed = CrashRecoveryManifest(tmp_path / "state")
    manifest = resumed.load_manifest()
    assert "auth-explorer" in manifest["agents"]
    prompt = resumed.resume_prompt(["auth-explorer", "billing-explorer"])
    assert "TokenVerifier in auth.py" in prompt
    assert "billing-explorer" in prompt.split("Still to run:")[1]
    assert json.loads((tmp_path / "state" / "auth-explorer.json").read_text())["phase"] == (
        "discovery"
    )


# ==============================================================================
# TS 5.5: stratified sampling, per-segment accuracy, calibration
# ==============================================================================


def test_stratified_sampling_covers_every_segment_and_is_reproducible() -> None:
    data = demo_validation_set()
    first = stratified_audit_sample(data, rate=0.10, seed=7)
    second = stratified_audit_sample(data, rate=0.10, seed=7)
    assert [i.doc_id for i in first] == [i.doc_id for i in second]
    assert {i.segment for i in first} == {
        ("standard_invoice", "total"),
        ("customs_form", "hs_code"),
    }
    # 10% of 90 = 9, 10% of 10 = 1
    assert sum(1 for i in first if i.document_type == "standard_invoice") == 9
    assert sum(1 for i in first if i.document_type == "customs_form") == 1


def test_small_rare_segment_still_sampled_and_confidence_filter_applies() -> None:
    items = [FieldExtraction(f"a{i}", "invoice", "total", 0.99) for i in range(50)]
    items.append(FieldExtraction("r1", "handwritten", "total", 0.96))
    items.append(FieldExtraction("r2", "handwritten", "date", 0.40))
    sample = stratified_audit_sample(items, rate=0.02, min_confidence=0.90)
    assert ("handwritten", "total") in {i.segment for i in sample}
    assert all(i.confidence >= 0.90 for i in sample)
    assert ("handwritten", "date") not in {i.segment for i in sample}


def test_sampling_does_not_touch_global_random_state() -> None:
    random.seed(123)
    expected = random.random()
    random.seed(123)
    stratified_audit_sample(demo_validation_set())
    ConfidenceRouter(random_seed=1).route_item("d", 0.99, "invoice")
    assert random.random() == expected


def test_aggregate_accuracy_hides_weak_segment() -> None:
    data = demo_validation_set()
    assert round(aggregate_accuracy(data), 2) == 0.97
    assert weak_segments(data) == [("customs_form", "hs_code")]
    assert safe_to_reduce_review(data, ("standard_invoice", "total"), min_samples=50)
    assert not safe_to_reduce_review(data, ("customs_form", "hs_code"), min_samples=5)
    assert not safe_to_reduce_review(data, ("customs_form", "hs_code"))


def test_calibration_check_flags_overconfident_segment() -> None:
    data = demo_validation_set()
    per_segment = segment_calibration(data)
    assert per_segment[("customs_form", "hs_code")] > 0.2
    assert per_segment[("standard_invoice", "total")] < 0.05
    assert expected_calibration_error(data) < per_segment[("customs_form", "hs_code")]
    perfect = [FieldExtraction(str(i), "d", "f", 1.0, True) for i in range(10)]
    assert expected_calibration_error(perfect) == 0.0


def test_router_sends_ambiguous_or_conflicting_items_to_humans() -> None:
    router = ConfidenceRouter(random_seed=42)
    amb = router.route_item("x", 0.99, "invoice", ambiguous=True)
    conflict = router.route_item("y", 0.99, "invoice", sources_conflict=True)
    assert amb.routing_tier == RoutingTier.MANDATORY_ESCALATION
    assert conflict.routing_tier == RoutingTier.MANDATORY_ESCALATION


# ==============================================================================
# TS 5.6: claim-source mapping, conflicts, dates, rendering
# ==============================================================================


def test_claim_source_mapping_and_conflict_annotation() -> None:
    s = ProvenanceSynthesizer()
    s.add_claim("Revenue", "$1.2B", "Wire", "2024-10-01", "Preliminary", "est. $1.2B", "2024-Q3")
    s.add_claim("Revenue", "$1.4B", "10-Q", "2024-10-15", "Audited", "rev $1.4B", "2024-Q3")
    entry = s.synthesize_metrics()[0]
    assert entry.status == "PRESERVED_CONFLICT" and entry.has_conflict
    assert entry.sources_by_value == {"$1.2B": ["Wire"], "$1.4B": ["10-Q"]}
    assert {c["excerpt"] for c in entry.claims} == {"est. $1.2B", "rev $1.4B"}
    assert "average" in entry.synthesized_guidance


def test_different_periods_are_temporal_difference_not_conflict() -> None:
    s = ProvenanceSynthesizer()
    s.add_claim("Inventory", "50,000", "A", "2025-06-30", "Count", period="2025-06")
    s.add_claim("Inventory", "12,000", "B", "2026-09-30", "Count", period="2026-09")
    entry = s.synthesize_metrics()[0]
    assert entry.status == "TEMPORAL_DIFFERENCE"
    assert entry.has_conflict is False


def test_report_separates_established_from_contested_and_renders_types() -> None:
    s = ProvenanceSynthesizer()
    s.add_claim("Revenue", "$1.2B", "Wire", "2024-10-01", "Prelim")
    s.add_claim("Revenue", "$1.4B", "10-Q", "2024-10-15", "Audited")
    s.add_claim("Headcount", "12,500", "10-Q", "2024-10-15", "Payroll")
    entries = s.synthesize_metrics()
    report = render_provenance_report(entries, {"Revenue": "financial"})
    assert report.index("Well-established") < report.index("Contested")
    contested_part = report.split("## Contested")[1]
    assert "| $1.2B | Wire |" in contested_part and "Headcount" not in contested_part
    claims = entries[0].claims
    assert render_claims(claims, "news").startswith("Wire reported $1.2B")
    assert render_claims(claims, "technical").startswith("- $1.2B [Wire")
