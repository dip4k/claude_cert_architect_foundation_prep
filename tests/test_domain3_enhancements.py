"""
Offline unit tests for the Domain 3 enhancements (frontmatter, globs, hierarchy, CI builder).

No Anthropic API calls and no `claude` process: pure stdlib logic over files in this repo.
"""

from pathlib import Path

import pytest

from domain3.ts_3_1_claude_code_workflows.main import (
    find_imports,
    load_path_rules,
    resolve_claude_md_chain,
    teammate_visible,
)
from domain3.ts_3_2_slash_commands_and_skills.main import (
    SkillCommandParser,
    classify_command_path,
)
from domain3.ts_3_3_path_specific_rules.main import (
    RuleEngine,
    glob_match,
    parse_frontmatter,
)
from domain3.ts_3_4_plan_mode_and_refinement.main import evaluate_execution_mode
from domain3.ts_3_5_iterative_refinement_interview.main import (
    Issue,
    format_test_failure_feedback,
    group_feedback,
)
from domain3.ts_3_6_cicd_pipeline_automation.main import (
    CIReviewFinding,
    HeadlessCIRunner,
    build_ci_command,
    build_rerun_prompt,
    findings_to_inline_comments,
    gate_exit_code,
    validate_ci_command,
    validate_findings_payload,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------
# Frontmatter parsing (TS 3.2 / 3.3)
# ------------------------------------------------------------------------------


def test_frontmatter_block_inline_and_scalar_forms() -> None:
    text = (
        "---\n"
        "name: demo\n"
        "context: fork\n"
        "allowed-tools:\n"
        "  - Read\n"
        '  - "Grep"\n'
        'argument-hint: "<path>"\n'
        "paths: [a/**, '*.md']\n"
        "---\n"
        "Body text\n"
    )
    data, body = parse_frontmatter(text)
    assert data["name"] == "demo"
    assert data["context"] == "fork"
    assert data["allowed-tools"] == ["Read", "Grep"]
    assert data["argument-hint"] == "<path>"
    assert data["paths"] == ["a/**", "*.md"]
    assert body.strip() == "Body text"


def test_frontmatter_absent_returns_text_unchanged() -> None:
    data, body = parse_frontmatter("No frontmatter here")
    assert data == {}
    assert body == "No frontmatter here"


def test_real_repo_rule_files_have_paths() -> None:
    rules = {r.rule_name: r for r in load_path_rules(REPO_ROOT / ".claude" / "rules")}
    assert rules["python_quality"].globs == ["**/*.py"]
    assert "**/*.md" in rules["mermaid_standards"].globs
    assert ".mcp.json" in rules["mcp_tools"].globs


def test_real_repo_skills_parse_fork_and_tools() -> None:
    skills = {
        s.name: s
        for s in SkillCommandParser.load_skills_from_dir(REPO_ROOT / ".claude" / "skills")
    }
    assert skills["architect-eval"].context == "fork"
    assert skills["architect-eval"].allowed_tools == ["Read", "Grep", "Glob"]
    assert skills["architect-eval"].argument_hint == "<domain_or_filepath>"
    assert skills["scaffold-exercise"].allowed_tools == ["Read", "Write", "Glob"]


# ------------------------------------------------------------------------------
# Glob matching (TS 3.3)
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "pattern", "expected"),
    [
        ("src/auth/auth.test.tsx", "**/*.test.tsx", True),
        ("auth.test.tsx", "**/*.test.tsx", True),
        ("src/auth/auth.tsx", "**/*.test.tsx", False),
        ("terraform/main.tf", "terraform/**/*", True),
        ("terraform/modules/vpc/main.tf", "terraform/**/*", True),
        ("infra/terraform/main.tf", "terraform/**/*", False),
        ("README.md", "*.md", True),
        ("docs/README.md", "*.md", False),
        ("backend\\api\\auth.py", "backend/**", True),
    ],
)
def test_glob_match(path: str, pattern: str, expected: bool) -> None:
    assert glob_match(path, pattern) is expected


def test_rule_loads_only_for_matching_files() -> None:
    engine = RuleEngine()
    engine.register_rule("tests", '---\npaths:\n  - "**/*.test.tsx"\n---\nUse Vitest.')
    engine.register_rule("always", "Universal rule with no frontmatter.")
    matched = [r["rule_id"] for r in engine.get_applicable_instructions(["src/a/b.test.tsx"])]
    other = [r["rule_id"] for r in engine.get_applicable_instructions(["src/a/b.tsx"])]
    assert matched == ["tests", "always"]
    assert other == ["always"]


def test_repo_rules_engine_scopes_python_files() -> None:
    engine = RuleEngine()
    assert engine.register_rules_from_dir(REPO_ROOT / ".claude" / "rules") >= 4
    ids = [r["rule_id"] for r in engine.get_applicable_instructions(["lib/x/y.py"])]
    assert "python_quality" in ids
    assert "mermaid_standards" not in ids


# ------------------------------------------------------------------------------
# CLAUDE.md hierarchy (TS 3.1) and command scope (TS 3.2)
# ------------------------------------------------------------------------------


def test_hierarchy_order_and_teammate_visibility(tmp_path: Path) -> None:
    home = tmp_path / "home" / ".claude"
    home.mkdir(parents=True)
    (home / "CLAUDE.md").write_text("personal", encoding="utf-8")
    project = tmp_path / "repo"
    (project / "services" / "billing").mkdir(parents=True)
    (project / "CLAUDE.md").write_text("team", encoding="utf-8")
    (project / "services" / "billing" / "CLAUDE.md").write_text("billing", encoding="utf-8")

    chain = resolve_claude_md_chain(project, Path("services/billing/api.py"), user_dir=home)
    assert [e.scope for e in chain] == ["user", "project", "directory"]
    assert [e.scope for e in teammate_visible(chain)] == ["project", "directory"]

    other = resolve_claude_md_chain(project, Path("services/other/x.py"), user_dir=home)
    assert [e.scope for e in other] == ["user", "project"]


def test_find_imports() -> None:
    text = (
        "# Standards\nSee @.claude/rules/testing.md for tests and @docs/api.md.\n"
        "Literal `@README` and a@b.com are not imports.\n```\n@fenced.md\n```\n"
    )
    assert find_imports(text) == [".claude/rules/testing.md", "docs/api.md"]


def test_command_scope_classification(tmp_path: Path) -> None:
    project_cmd = REPO_ROOT / ".claude" / "commands" / "review.md"
    assert classify_command_path(project_cmd, REPO_ROOT) == "project-scoped"
    personal = tmp_path / "home" / ".claude" / "commands" / "mine.md"
    assert classify_command_path(personal, REPO_ROOT) == "user-scoped"
    assert classify_command_path(REPO_ROOT / "README.md", REPO_ROOT) == "not-a-command"


# ------------------------------------------------------------------------------
# Plan mode vs direct execution (TS 3.4) and refinement (TS 3.5)
# ------------------------------------------------------------------------------


def test_plan_mode_then_direct_execution_phases() -> None:
    plan = evaluate_execution_mode(45, True, False, False)
    assert plan.mode == "plan_mode"
    assert plan.use_explore_subagent is True
    assert plan.phases[-1].startswith("direct execution")
    direct = evaluate_execution_mode(1, False, True, True)
    assert direct.mode == "direct_execution"
    assert direct.use_explore_subagent is False


def test_group_feedback_interacting_vs_independent() -> None:
    issues = [
        Issue("token-payload", frozenset({"auth", "router"})),
        Issue("router-order", frozenset({"router"})),
        Issue("css-padding", frozenset({"dashboard"})),
    ]
    assert group_feedback(issues) == [["token-payload", "router-order"], ["css-padding"]]


def test_test_failure_feedback_lists_failures() -> None:
    text = format_test_failure_feedback(["test_a: expected 1 got 2"])
    assert "test_a: expected 1 got 2" in text


# ------------------------------------------------------------------------------
# CI command builder and findings (TS 3.6)
# ------------------------------------------------------------------------------


def test_ci_command_always_has_print_and_json_schema() -> None:
    schema = '{"type": "object", "properties": {"findings": {"type": "array"}}}'
    argv = build_ci_command("Review", schema)
    assert argv[:2] == ["claude", "-p"]
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--json-schema") + 1] == schema
    assert validate_ci_command(argv) == []


def test_ci_command_rejects_bad_inputs_and_flags_hangs() -> None:
    with pytest.raises(ValueError):
        build_ci_command("Review", "")
    with pytest.raises(ValueError):
        build_ci_command("Review", "{}", output_format="text")
    with pytest.raises(ValueError):
        build_ci_command("Review", ".ci/schema.json")
    problems = validate_ci_command(["claude", "Review PR"])
    assert any("-p" in p for p in problems)
    assert any("--output-format" in p for p in problems)


def test_findings_payload_validation_and_comments() -> None:
    result = HeadlessCIRunner().run_pr_audit("+ x = eval(y)")
    payload = {
        "status": result.status,
        "summary": result.summary,
        "findings": [f.__dict__ for f in result.findings],
    }
    assert validate_findings_payload(payload) == []
    comments = findings_to_inline_comments(result.findings)
    assert comments[0]["path"] == "auth/eval_handler.py"
    assert comments[0]["line"] == 42
    bad = {"status": "MAYBE", "summary": "x", "findings": [{"severity": "HIGH", "line": "3"}]}
    assert len(validate_findings_payload(bad)) >= 4


def test_gate_exit_code_blocks_only_critical() -> None:
    warn = CIReviewFinding("WARNING", "a.py", 1, "R", "d", "f")
    crit = CIReviewFinding("CRITICAL", "a.py", 2, "R", "d", "f")
    assert gate_exit_code([warn]) == 0
    assert gate_exit_code([warn, crit]) == 1


def test_rerun_prompt_includes_prior_findings_and_asks_for_new_only() -> None:
    prior = [
        {"file": "a.py", "line": 3, "rule_violated": "SEC001", "description": "eval used"},
    ]
    prompt = build_rerun_prompt("Review the diff.", prior)
    assert "a.py:3 SEC001" in prompt
    assert "only NEW issues" in prompt
    assert build_rerun_prompt("Review the diff.", []) == "Review the diff."
