"""
Tests for all dedicated task statement exercises across Domains 2, 3, 4, and 5.
Runs 100% offline with zero token consumption.
"""

import pytest
from pathlib import Path

# Domain 2 imports
from domain2.ts_2_3_tool_distribution_and_choice.main import (
    BuiltinToolsEngine,
    resolve_tool_choice_mode,
)

# Domain 3 imports
from domain3.ts_3_4_plan_mode_and_refinement.main import (
    evaluate_execution_mode,
    build_interview_pattern_prompt,
    format_few_shot_refinement,
)

# Domain 4 imports
from domain4.ts_4_2_few_shot_and_multi_instance.main import (
    render_few_shot_prompt_block,
    FEW_SHOT_EXTRACTION_EXAMPLES,
    MultiInstanceReviewPipeline,
)

# Domain 5 imports
from domain5.ts_5_4_scratchpads_and_human_review.main import (
    HumanReviewRoutingEngine,
    ExtractionRecord,
    CodebaseScratchpadManager,
)


def test_d2_builtin_tools_engine(tmp_path):
    f1 = tmp_path / "app.py"
    f1.write_text("def run():\n    return 'hello'\n", encoding="utf-8")
    engine = BuiltinToolsEngine(tmp_path)

    # Glob
    files = engine.glob_files("*.py")
    assert "app.py" in files

    # Grep
    grep_res = engine.grep_content("def run", "*.py")
    assert len(grep_res) == 1
    assert grep_res[0]["file"] == "app.py"

    # tool_choice resolver
    assert resolve_tool_choice_mode("auto") == "auto"
    assert resolve_tool_choice_mode("any") == "any"
    forced = resolve_tool_choice_mode("forced", "my_tool")
    assert forced == {"type": "tool", "name": "my_tool"}


def test_d3_plan_mode_vs_direct_execution():
    # Multi-file architectural refactor -> Plan Mode
    d_plan = evaluate_execution_mode(file_count_affected=15, has_architectural_tradeoffs=True, has_known_stack_trace=False, is_single_function_fix=False)
    assert d_plan.mode == "plan_mode"
    assert "Explore" in d_plan.recommended_tools

    # Isolated bug fix with stack trace -> Direct Execution
    d_direct = evaluate_execution_mode(file_count_affected=1, has_architectural_tradeoffs=False, has_known_stack_trace=True, is_single_function_fix=True)
    assert d_direct.mode == "direct_execution"

    # Interview pattern prompt
    prompt = build_interview_pattern_prompt("Redis Caching Layer")
    assert "interview me" in prompt


def test_d4_few_shot_and_multi_instance():
    block = render_few_shot_prompt_block(FEW_SHOT_EXTRACTION_EXAMPLES)
    assert "FEW-SHOT REASONING EXAMPLES" in block
    assert "Architectural Reasoning:" in block

    payload = MultiInstanceReviewPipeline.prepare_reviewer_payload("code", ["Check A"])
    assert "independent" in payload["content"].lower()
    assert "Check A" in payload["content"]


def test_d5_human_review_and_scratchpad():
    router = HumanReviewRoutingEngine(confidence_threshold=0.85)
    r_high = router.route_record(ExtractionRecord("D1", "standard_invoice", 0.95, 100.0))
    assert r_high.requires_human_review is False

    r_low = router.route_record(ExtractionRecord("D2", "customs_doc", 0.60, 500.0))
    assert r_low.requires_human_review is True

    # Stratified sampling
    records = [
        ExtractionRecord("D1", "A", 0.9, 10.0),
        ExtractionRecord("D2", "A", 0.8, 20.0),
        ExtractionRecord("D3", "B", 0.7, 30.0),
    ]
    sampled = HumanReviewRoutingEngine.stratified_random_sample(records, 1)
    assert len(sampled) == 2  # 1 from segment A, 1 from segment B

    # Scratchpad persistence
    pad = CodebaseScratchpadManager()
    pad.record_finding("Class OrderService handles refunds")
    assert "OrderService" in pad.render_scratchpad()
