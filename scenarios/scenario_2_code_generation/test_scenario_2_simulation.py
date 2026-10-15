"""
Unit tests for Scenario 2: Code Generation with Claude Code simulation.
Runs 100% offline with zero token costs.
"""

import pytest
from scenarios.scenario_2_code_generation.simulation import (
    ClaudeCodeGenerationEngine,
    CodeGenTask,
    ExecutionMode,
)


def test_code_gen_routes_multi_file_to_plan_mode():
    engine = ClaudeCodeGenerationEngine()
    task = CodeGenTask(
        task_id="t1",
        description="Refactor user models and controllers",
        target_files=["backend/models.py", "backend/controllers.py"],
        is_architectural_shift=True
    )
    outcome = engine.evaluate_task(task)
    assert outcome.mode_selected == ExecutionMode.PLAN_MODE
    assert outcome.forked_execution_used is True
    assert "backend_auth" in outcome.injected_path_rules
    assert "frontend_react" not in outcome.injected_path_rules


def test_code_gen_routes_single_file_to_direct_execution():
    engine = ClaudeCodeGenerationEngine()
    task = CodeGenTask(
        task_id="t2",
        description="Fix typo in variable name",
        target_files=["frontend/ui/Button.tsx"],
        is_architectural_shift=False
    )
    outcome = engine.evaluate_task(task)
    assert outcome.mode_selected == ExecutionMode.DIRECT_EXECUTION
    assert "frontend_react" in outcome.injected_path_rules
    assert "backend_auth" not in outcome.injected_path_rules
    assert outcome.interview_required is False


def test_code_gen_triggers_interview_pattern_on_ambiguity():
    engine = ClaudeCodeGenerationEngine()
    task = CodeGenTask(
        task_id="t3",
        description="Implement user auth service",
        target_files=["backend/api/auth.py"],
        is_architectural_shift=False
    )
    outcome = engine.evaluate_task(task)
    assert outcome.interview_required is True
    assert len(outcome.clarification_options) >= 1
    assert any("JWT" in opt for opt in outcome.clarification_options)


def test_code_gen_ambiguous_database_triggers_interview_options():
    engine = ClaudeCodeGenerationEngine()
    task = CodeGenTask(
        task_id="t4",
        description="Connect service to database storage",
        target_files=["backend/db.py"],
        is_architectural_shift=False
    )
    outcome = engine.evaluate_task(task)
    assert outcome.interview_required is True
    assert any("PostgreSQL" in opt for opt in outcome.clarification_options)


def test_code_gen_isolated_rules_do_not_leak_across_stacks():
    engine = ClaudeCodeGenerationEngine()
    # Task only touching backend files
    task_backend = CodeGenTask(
        task_id="t5",
        description="Add error handling",
        target_files=["backend/server.py"],
        is_architectural_shift=False
    )
    res_b = engine.evaluate_task(task_backend)
    assert "backend_auth" in res_b.injected_path_rules
    assert "frontend_react" not in res_b.injected_path_rules


def test_code_gen_plan_mode_generates_blueprint_requiring_approval():
    engine = ClaudeCodeGenerationEngine()
    task = CodeGenTask(
        task_id="t6_plan",
        description="Refactor user schema and migration scripts",
        target_files=["backend/models/user.py", "backend/migrations/001.py", "backend/api/users.py"],
        is_architectural_shift=True
    )
    outcome = engine.evaluate_task(task)
    assert outcome.mode_selected == ExecutionMode.PLAN_MODE
    assert outcome.blueprint is not None
    assert outcome.blueprint.requires_approval is True
    assert outcome.blueprint.is_approved is False
    assert len(outcome.blueprint.steps) == 4

    # Developer approves blueprint
    approved = engine.approve_plan_blueprint(outcome.blueprint)
    assert approved is True
    assert outcome.blueprint.is_approved is True


def test_code_gen_enterprise_policy_precedence():
    engine = ClaudeCodeGenerationEngine()
    assert "enforce_proxy" in engine.ENTERPRISE_POLICY
    assert "proxy.corp.internal" in engine.ENTERPRISE_POLICY["enforce_proxy"]


