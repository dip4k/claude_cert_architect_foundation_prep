"""
Offline tests for Domain 2 enhancements (TS 2.1-2.5). Uses lib.mock_claude; zero API cost.
"""

import re
from pathlib import Path
from typing import Any, List

import pytest

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse
from lib.response_logger import ResponseTrail

from domain2.ts_2_1_tool_interface_design import main as ts21
from domain2.ts_2_2_mcp_structured_errors import main as ts22
from domain2.ts_2_3_tool_distribution_and_choice import main as ts23
from domain2.ts_2_4_mcp_server_integration import main as ts24
from domain2.ts_2_5_builtin_tools_usage.main import BuiltinToolbox

DOMAIN2 = Path(__file__).resolve().parent.parent / "domain2"


def _text(text: str, stop_reason: str = "end_turn") -> MockMessageResponse:
    return MockMessageResponse([MockContentBlock("text", text=text)], stop_reason)


def _tool_use(name: str, args: dict, tool_id: str = "t1") -> MockMessageResponse:
    block = MockContentBlock("tool_use", name=name, tool_id=tool_id, input_data=args)
    return MockMessageResponse([block], "tool_use")


@pytest.fixture
def trail(tmp_path: Path) -> ResponseTrail:
    return ResponseTrail(path=str(tmp_path / "trail.jsonl"))


# ==============================================================================
# TS 2.1
# ==============================================================================


def test_ts21_audit_flags_thin_and_passes_production_tools() -> None:
    thin = {"name": "lookup_order", "description": "Retrieves order details"}
    assert len(ts21.audit_tool(thin)) >= 2
    for tool in ts21.TOOLS:
        assert ts21.audit_tool(tool) == []


def test_ts21_vague_pair_overlaps_more_than_split_tools() -> None:
    vague = ts21.description_overlap(*ts21.VAGUE_TOOLS)
    split = ts21.SPLIT_DOCUMENT_TOOLS
    worst = max(ts21.description_overlap(a, b) for i, a in enumerate(split) for b in split[i + 1:])
    assert vague > worst
    assert [t["name"] for t in split] == [
        "extract_data_points",
        "summarize_content",
        "verify_claim_against_source",
    ]


def test_ts21_loop_forces_first_tool_without_thinking(trail: ResponseTrail) -> None:
    client = MockClaudeClient(
        [_tool_use("get_customer", {"identifier": "alice@example.com"}), _text("Verified.")]
    )
    result = ts21.run_bounded_tool_agent("verify", client, trail, force_customer_first=True)
    first, second = client.messages.call_history
    assert result == "Verified."
    assert first["tool_choice"] == {"type": "tool", "name": "get_customer"}
    assert second["tool_choice"] == {"type": "auto"}
    assert "thinking" not in first and "temperature" not in first
    assert first["model"] == ts21.COORDINATOR_MODEL == "claude-sonnet-4-5"


@pytest.mark.parametrize(
    "responses, expected",
    [
        ([_text("partial", "max_tokens")], "partial"),
        ([_text("no", "refusal")], ""),
        ([_text("odd", "stop_sequence")], ""),
        ([MockMessageResponse([MockContentBlock("text", text="wait")], "pause_turn"),
          _text("done")], "done"),
    ],
)
def test_ts21_loop_handles_each_stop_reason(
    trail: ResponseTrail, responses: List[Any], expected: str
) -> None:
    client = MockClaudeClient(responses)
    assert ts21.run_bounded_tool_agent("q", client, trail) == expected


def test_ts21_safety_cap_is_fallback_only(trail: ResponseTrail) -> None:
    calls = [_tool_use("lookup_order", {"order_id": "ORD-9821"}, f"t{i}") for i in range(10)]
    client = MockClaudeClient(calls)
    assert ts21.run_bounded_tool_agent("loop", client, trail, max_iterations=3) == ""
    assert len(client.messages.call_history) == 3


# ==============================================================================
# TS 2.2
# ==============================================================================


def test_ts22_error_schema_is_uniform_across_categories() -> None:
    errors = [
        ts22.query_inventory("SKU-1", "timeout"),
        ts22.query_inventory("BAD"),
        ts22.issue_refund("CUST-1", 900.0),
        ts22.read_payment_method("CUST-1", "orders:read"),
    ]
    assert [e["errorCategory"] for e in errors] == list(ts22.ERROR_CATEGORIES)
    for error in errors:
        assert ts22.validate_error_payload(error) == []
    assert [e["isRetryable"] for e in errors] == [True, False, False, False]


def test_ts22_generic_and_invalid_errors_are_rejected() -> None:
    generic = {"isError": True, "errorCategory": "transient", "isRetryable": True,
               "message": "Operation failed"}
    assert ts22.validate_error_payload(generic)
    bad_retry = ts22.create_mcp_error("business", "Over limit, ask a supervisor.", True)
    assert ts22.validate_error_payload(bad_retry)
    with pytest.raises(ValueError):
        ts22.create_mcp_error("unknown", "x", False)


def test_ts22_call_tool_result_shape() -> None:
    wrapped = ts22.to_call_tool_result(ts22.issue_refund("CUST-1", 900.0))
    assert wrapped["isError"] is True
    assert "errorCategory" in wrapped["content"][0]["text"]
    assert ts22.to_call_tool_result(ts22.query_inventory("SKU-99999"))["isError"] is False


def test_ts22_recover_locally_retries_only_transient() -> None:
    state = {"n": 0}

    def flaky() -> dict:
        state["n"] += 1
        return ts22.query_inventory("SKU-1", "timeout" if state["n"] < 3 else "normal")

    ok = ts22.recover_locally(flaky, max_retries=2)
    assert ok["status"] == "ok" and len(ok["attempts"]) == 2

    unresolved = ts22.recover_locally(
        lambda: ts22.query_inventory("SKU-1", "timeout"), 1, partial_results=["a"]
    )
    assert unresolved["status"] == "unresolved"
    assert len(unresolved["attempted"]) == 2 and unresolved["partial_results"] == ["a"]

    blocked = ts22.recover_locally(lambda: ts22.issue_refund("C", 900.0))
    assert len(blocked["attempted"]) == 1


def test_ts22_loop_returns_structured_error_to_claude(trail: ResponseTrail) -> None:
    client = MockClaudeClient(
        [_tool_use("issue_refund", {"customer_id": "C", "amount": 750}), _text("Escalating.")]
    )
    assert ts22.run_structured_error_agent("refund", client, trail) == "Escalating."
    result_block = client.messages.call_history[1]["messages"][-1]["content"][0]
    assert result_block["is_error"] is True
    assert '"errorCategory": "business"' in result_block["content"]
    assert client.messages.call_history[0]["model"] == "claude-sonnet-4-5"


# ==============================================================================
# TS 2.3
# ==============================================================================


def test_ts23_scoped_roles_fit_budget_and_monolith_does_not() -> None:
    assert ts23.check_tool_budget(ts23.MONOLITH_TOOLS)
    assert len(ts23.MONOLITH_TOOLS) == 18
    for role in ts23.ROLE_TOOLSETS:
        assert ts23.check_tool_budget(ts23.tools_for_role(role)) == []
    assert "fetch_url" not in ts23.tools_for_role("search")
    assert "verify_fact" in ts23.tools_for_role("synthesis")


def test_ts23_constrained_load_document_and_verify_fact() -> None:
    assert ts23.load_document("https://docs.example.com/a")["isError"] is False
    for url in ("http://docs.example.com/a", "https://evil.example.net/a"):
        blocked = ts23.load_document(url)
        assert blocked["isError"] and blocked["errorCategory"] == "validation"
    sources = {"D1": "Revenue grew 8%."}
    assert ts23.verify_fact("revenue grew 8%", "D1", sources)["verdict"] == "supported"
    assert ts23.verify_fact("x", "D9", sources)["verdict"] == "not_found"


def test_ts23_tool_choice_shapes_and_forced_first_turn() -> None:
    assert ts23.build_tool_choice("auto") == {"type": "auto"}
    assert ts23.build_tool_choice("any") == {"type": "any"}
    assert ts23.build_tool_choice("none") == {"type": "none"}
    assert ts23.tool_choice_for_turn(1) == {"type": "tool", "name": "extract_metadata"}
    assert ts23.tool_choice_for_turn(2) == {"type": "auto"}
    with pytest.raises(ValueError):
        ts23.build_tool_choice("forced")


@pytest.mark.parametrize("mode", ["any", "forced"])
def test_ts23_thinking_rejects_any_and_forced(mode: str) -> None:
    choice = ts23.build_tool_choice(mode, "extract_metadata")
    with pytest.raises(ValueError, match="auto or none"):
        ts23.build_request_params("coordinator", [], choice, thinking_budget=2048)
    # The same choice is fine when thinking is off.
    assert ts23.build_request_params("search", [], choice)["tool_choice"] == choice


def test_ts23_thinking_parameter_limits_and_models() -> None:
    auto = ts23.build_tool_choice("auto")
    params = ts23.build_request_params("coordinator", [], auto, thinking_budget=2048)
    assert "temperature" not in params and params["model"] == "claude-sonnet-4-5"
    assert ts23.build_request_params("search", [], auto)["model"] == "claude-haiku-4-5"
    with pytest.raises(ValueError):
        ts23.build_request_params("coordinator", [], auto, thinking_budget=512)
    with pytest.raises(ValueError):
        ts23.build_request_params("coordinator", [], auto, thinking_budget=4096, max_tokens=4096)
    for extra in ({"temperature": 0.2}, {"top_k": 5}, {"top_p": 0.5}):
        with pytest.raises(ValueError):
            ts23.validate_request_params({**params, **extra})
    assert ts23.validate_request_params({**params, "top_p": 0.97})


# ==============================================================================
# TS 2.4
# ==============================================================================


def test_ts24_env_expansion_and_missing_variable() -> None:
    env = {"GITHUB_TOKEN": "g", "JIRA_API_TOKEN": "j"}
    config = ts24.load_mcp_config(ts24.EXAMPLE_PROJECT_MCP_JSON, env)
    assert config["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "g"
    with pytest.raises(ts24.MissingEnvVarError, match="GITHUB_TOKEN"):
        ts24.load_mcp_config(ts24.EXAMPLE_PROJECT_MCP_JSON, {"JIRA_API_TOKEN": "j"})
    with pytest.raises(ValueError):
        ts24.load_mcp_config("{}", {})


def test_ts24_detects_hardcoded_secrets() -> None:
    assert ts24.find_hardcoded_secrets(ts24.EXAMPLE_PROJECT_MCP_JSON) == []
    leaky = ts24.EXAMPLE_PROJECT_MCP_JSON.replace("${JIRA_API_TOKEN}", "abc123")
    assert ts24.find_hardcoded_secrets(leaky) == ["jira.JIRA_API_TOKEN"]


def test_ts24_all_servers_discovered_and_resources_listed() -> None:
    catalog = ts24.discover_tools({"github": ["create_pr"], "jira": ["search_issues"]})
    assert catalog == {"create_pr": "github", "search_issues": "jira"}
    uris = [r["uri"] for r in ts24.DeveloperMCPService.list_resources()]
    assert "catalog://schema/orders" in uris
    assert ts24.DeveloperMCPService.read_resource("catalog://missing") is None
    assert ts24.audit_mcp_tool({"description": "Search"})
    assert ts24.audit_mcp_tool({"description": "x" * 90 + " Example: find ticket PROJ-1."}) == []


# ==============================================================================
# TS 2.5
# ==============================================================================


def test_ts25_read_write_fallback_replaces_chosen_occurrence(tmp_path: Path) -> None:
    toolbox = BuiltinToolbox(tmp_path)
    toolbox.write_file("dup.py", "a = 1\nb = 0\na = 1\n")
    result = toolbox.execute_edit_with_fallback("dup.py", "a = 1", "a = 2", occurrence=1)
    assert result["status"] == "FALLBACK_WRITE_SUCCESS"
    assert (tmp_path / "dup.py").read_text(encoding="utf-8") == "a = 1\nb = 0\na = 2\n"
    missing = toolbox.execute_edit_with_fallback("dup.py", "zzz", "y")
    assert missing["status"] == "FAILED"


def test_ts25_trace_usage_through_wrapper(tmp_path: Path) -> None:
    toolbox = BuiltinToolbox(tmp_path)
    toolbox.write_file("pkg/__init__.py", "def get_order():\n    return 1\n\ndef _hidden():\n    pass\n")
    toolbox.write_file("app.py", "from pkg import get_order\nget_order()\n")
    assert toolbox.list_exported_names("pkg/__init__.py") == ["get_order"]
    assert toolbox.trace_usage("pkg/__init__.py") == {"get_order": ["app.py"]}
    toolbox.write_file("pkg2/__init__.py", "__all__ = ['a', 'b']\n")
    assert toolbox.list_exported_names("pkg2/__init__.py") == ["a", "b"]


# ==============================================================================
# Study material consistency
# ==============================================================================

TS_DIRS = sorted(p for p in DOMAIN2.iterdir() if p.is_dir() and p.name.startswith("ts_2_"))
REQUIRED_SECTIONS = [
    "## In One Minute",
    "## 🧪 Worked Example",
    "## ⚠️ Exam Traps and Correct Patterns",
    "## 📝 Exam-Style Practice Questions",
    "### Answers",
    "## ✅ Self-Check Checklist",
    "**Memory hook**",
]


@pytest.mark.parametrize("ts_dir", TS_DIRS, ids=lambda p: p.name)
def test_readmes_have_required_sections_and_clean_mermaid(ts_dir: Path) -> None:
    text = (ts_dir / "README.md").read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in text, f"{ts_dir.name} missing {section}"
    assert text.count("**Q") >= 6  # 3 questions + 3 answers
    assert "%%{init" not in text and "<b>" not in text
    for block in text.split("```mermaid")[1:]:
        body = re.sub(r"\A\s*---\r?\n.*?\r?\n---\r?\n", "", block, flags=re.S)
        assert body.lstrip().startswith(("flowchart TD", "flowchart LR"))


@pytest.mark.parametrize("ts_dir", TS_DIRS, ids=lambda p: p.name)
def test_notebook_markdown_mirrors_readme(ts_dir: Path) -> None:
    import json

    nb = json.loads((ts_dir / f"{ts_dir.name}.ipynb").read_text(encoding="utf-8"))
    first = "".join(nb["cells"][0]["source"])
    assert first == (ts_dir / "README.md").read_text(encoding="utf-8").rstrip("\n")


def test_domain2_readme_states_weight_and_study_order() -> None:
    text = (DOMAIN2 / "README.md").read_text(encoding="utf-8")
    assert "18%" in text and "Study Order" in text
    assert "D1 27%" in text and "D5 15%" in text
    for name in ("ts_2_1", "ts_2_2", "ts_2_3", "ts_2_4", "ts_2_5"):
        assert name in text


def test_loops_do_not_use_getattr_stop_reason_fallback() -> None:
    for ts_dir in TS_DIRS:
        source = (ts_dir / "main.py").read_text(encoding="utf-8")
        assert 'getattr(response, "stop_reason"' not in source
