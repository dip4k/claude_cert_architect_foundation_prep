"""
Unit tests for newly added Task Statement modules across Domains 2, 3, 4, and 5.
All tests execute 100% offline with zero token costs and zero external network calls.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from domain2.ts_2_5_builtin_tools_usage.main import BuiltinToolbox
from domain3.ts_3_2_slash_commands_and_skills.main import SkillCommandParser, ClaudeCodeRunner
from domain3.ts_3_3_path_specific_rules.main import RuleEngine
from domain3.ts_3_5_iterative_refinement_interview.main import RefinementCoordinator
from domain3.ts_3_6_cicd_pipeline_automation.main import HeadlessCIRunner
from domain4.ts_4_1_explicit_criteria_classification.main import ExplicitCriteriaClassifier
from domain4.ts_4_4_validation_retry_feedback.main import ExtractionValidator, ResilientExtractorLoop
from domain4.ts_4_6_multi_pass_review.main import IndependentReviewerInstance, MultiPassReviewPipeline
from domain5.ts_5_3_error_propagation_coverage.main import MultiAgentSynthesizer, SubagentResult, SubagentStatus
from domain5.ts_5_5_human_review_calibration.main import ConfidenceRouter, RoutingTier
from domain5.ts_5_6_provenance_and_uncertainty.main import ProvenanceSynthesizer


# ==============================================================================
# Domain 2 Tests
# ==============================================================================

def test_ts25_builtin_tools_edit_and_fallback():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        toolbox = BuiltinToolbox(temp_dir)
        toolbox.write_file("test.py", "def a(): return 1\ndef b(): return 1\n")

        # Ambiguous edit should fail
        res = toolbox.edit_file("test.py", "return 1", "return 2")
        assert res["success"] is False
        assert "Ambiguous edit" in res["error"]

        # Fallback with unique context should succeed
        fallback_res = toolbox.execute_edit_with_fallback(
            "test.py",
            old_str="return 1",
            new_str="return 2",
            unique_context="def a(): return 1"
        )
        assert fallback_res["status"] == "EDIT_RETRY_SUCCESS"

        read_res = toolbox.read_file("test.py")
        assert "def a(): return 2" in read_res["content"]
        assert "def b(): return 1" in read_res["content"]
    finally:
        shutil.rmtree(temp_dir)


# ==============================================================================
# Domain 3 Tests
# ==============================================================================

def test_ts32_slash_command_and_forked_skill():
    template = "Deploy branch $ARGUMENTS to stage $1"
    expanded = SkillCommandParser.parse_slash_command(template, "feature/auth prod")
    assert expanded == "Deploy branch feature/auth prod to stage feature/auth"

    skill_md = """---
name: mock-audit
context: fork
allowed-tools: [Read, Grep]
---
Perform security checks.
"""
    skill = SkillCommandParser.parse_skill_markdown(skill_md)
    assert skill.name == "mock-audit"
    assert skill.context == "fork"
    assert "Read" in skill.allowed_tools

    runner = ClaudeCodeRunner()
    result = runner.execute_skill(skill, "src/auth")
    assert result["execution_mode"] == "forked"
    assert result["main_context_bloat_prevented"] is True


def test_ts33_path_specific_rules_scoping():
    engine = RuleEngine()
    engine.register_rule(
        "backend_rule",
        """---
paths:
  - "backend/**"
  - "*.py"
---
Use async handlers."""
    )
    engine.register_rule(
        "frontend_rule",
        """---
paths:
  - "frontend/**"
---
Use React hooks."""
    )

    # Touching backend
    backend_active = engine.get_applicable_instructions(["backend/main.py"])
    rule_ids = [r["rule_id"] for r in backend_active]
    assert "backend_rule" in rule_ids
    assert "frontend_rule" not in rule_ids

    # Touching frontend
    frontend_active = engine.get_applicable_instructions(["frontend/App.tsx"])
    rule_ids = [r["rule_id"] for r in frontend_active]
    assert "frontend_rule" in rule_ids
    assert "backend_rule" not in rule_ids


def test_ts35_interview_pattern_clarification():
    coordinator = RefinementCoordinator()
    is_ambiguous, questions = coordinator.evaluate_requirement_clarity(
        "Build an auth service storing records in database"
    )
    assert is_ambiguous is True
    assert len(questions) >= 2

    q_ids = [q.question_id for q in questions]
    assert "auth_type" in q_ids
    assert "storage_backend" in q_ids

    spec = coordinator.formulate_grounded_spec(
        "Auth", {"auth_type": "JWT Bearer tokens", "storage_backend": "PostgreSQL (SQLAlchemy)"}
    )
    assert len(spec.concrete_examples) == 2


def test_ts36_cicd_headless_execution():
    runner = HeadlessCIRunner(non_interactive=True)
    diff = """
    + result = eval(user_supplied_str)
    """
    res = runner.run_pr_audit(diff)
    assert res.exit_code == 1
    assert res.status == "CHANGES_REQUESTED"
    assert any(f.rule_violated == "SEC001_NO_DYNAMIC_EXEC" for f in res.findings)


# ==============================================================================
# Domain 4 Tests
# ==============================================================================

def test_ts41_explicit_criteria_negative_boundary():
    classifier = ExplicitCriteriaClassifier()
    
    # Negative boundary: test file with mock key
    test_code = 'mock_key = "sk-ant-test_mock_dummy_0123456789"'
    findings_test = classifier.evaluate_snippet("tests/test_auth.py", test_code)
    assert len(findings_test) == 0  # Filtered by negative boundary!

    # Production code: real key pattern
    prod_code = 'prod_key = "sk-ant-live0123456789abcdef0123456789"'
    findings_prod = classifier.evaluate_snippet("src/auth.py", prod_code)
    assert len(findings_prod) == 1
    assert findings_prod[0].severity == "CRITICAL"


def test_ts44_validation_retry_and_unrecoverable_exit():
    loop = ResilientExtractorLoop(max_retries=3)

    # 1. Recoverable retry
    doc1 = "Invoice 1: Subtotal 100, Total 110, Tax ID: TX-1"
    turns1 = [
        {"subtotal": 100, "total": 90, "tax_id": "TX-1"},
        {"subtotal": 100, "total": 110, "tax_id": "TX-1"}
    ]
    res1 = loop.run_validation_cycle(doc1, turns1)
    assert res1["status"] == "SUCCESS"
    assert res1["retries_used"] == 1

    # 2. Unrecoverable missing tax info -> fast fail without burning retries
    doc2 = "Simple lunch receipt: $12"
    turns2 = [{"subtotal": 12, "total": 12, "tax_id": None}]
    res2 = loop.run_validation_cycle(doc2, turns2)
    assert res2["status"] == "ABORTED_UNRECOVERABLE"
    assert res2["retries_used"] == 0


def test_ts46_multipass_review_catches_interface_mismatch():
    codebase = {
        "auth_api.py": "def verify_session(bearer_token: str):\n    try: pass\n    except: pass",
        "auth_client.py": "def login(): return verify_session(auth_token='xyz')"
    }
    pipeline = MultiPassReviewPipeline()
    report = pipeline.run_review(codebase)

    assert report["approved"] is False
    assert report["pass_1_local_count"] >= 1  # Catches bare except
    assert report["pass_2_integration_count"] >= 1  # Catches parameter name mismatch


# ==============================================================================
# Domain 5 Tests
# ==============================================================================

def test_ts53_error_propagation_and_partial_coverage():
    results = [
        SubagentResult("SourceA", SubagentStatus.SUCCESS, [{"title": "Doc1", "summary": "Valid"}]),
        SubagentResult("SourceB", SubagentStatus.VALID_EMPTY, []),
        SubagentResult("SourceC", SubagentStatus.UPSTREAM_FAILURE, error_message="Timeout 504")
    ]
    report = MultiAgentSynthesizer.synthesize(results)
    assert report.coverage_state == "PARTIAL"
    assert "SourceC" in report.source_omissions
    assert report.confidence_level < 1.0


def test_ts55_confidence_calibration_stratified_audit():
    router = ConfidenceRouter(random_seed=42)
    # High confidence doc
    dec = router.route_item("doc_1", 0.98, "invoice")
    assert dec.routing_tier in (RoutingTier.AUTO_APPROVE, RoutingTier.STRATIFIED_AUDIT)

    # Low confidence doc
    dec_low = router.route_item("doc_2", 0.50, "invoice")
    assert dec_low.routing_tier == RoutingTier.MANDATORY_ESCALATION


def test_ts56_provenance_preserves_conflicts():
    synth = ProvenanceSynthesizer()
    synth.add_claim("Revenue", "$1.0B", "Source_Oct1", "2024-10-01", "Preliminary")
    synth.add_claim("Revenue", "$1.2B", "Source_Oct15", "2024-10-15", "Audited 10-Q")

    entries = synth.synthesize_metrics()
    assert len(entries) == 1
    assert entries[0].has_conflict is True
    assert entries[0].status == "PRESERVED_CONFLICT"
    assert "Do NOT calculate an average" in entries[0].synthesized_guidance
