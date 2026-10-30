"""
Offline tests for the Domain 1 loop hardening (explicit stop_reason handling, thinking-block
echo, parallel Task ordering, model split, hooks, handoff, session resume).

Runs 100% offline using lib.mock_claude. Zero Anthropic API tokens or costs.
"""

import json
from typing import Any, List

import pytest

from domain1.loop_common import COORDINATOR_MODEL, WORKER_MODEL, LoopStopped
from domain1.ts_1_1_multi_tool_agent_loop.main import run_agent as run_ts11
from domain1.ts_1_2_coordinator_subagents.main import MultiAgentCoordinator
from domain1.ts_1_3_subagent_invocation_spawning.main import (
    run_parallel_spawning_coordinator as run_ts13,
)
from domain1.ts_1_4_prerequisite_enforcement.main import (
    WorkflowState,
    escalate_to_human,
    run_prerequisite_agent,
)
from domain1.ts_1_5_sdk_hooks.main import (
    execute_with_hooks,
    post_tool_use_normalization_hook,
    run_hook_agent,
)
from domain1.ts_1_6_task_decomposition.main import (
    CodeFile,
    plan_adaptive_subtasks,
    run_prompt_chaining_review,
)
from domain1.ts_1_7_session_management.main import SessionManager, execute_turn
from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse
from lib.response_logger import ResponseTrail


def _text(text: str, stop_reason: str = "end_turn") -> MockMessageResponse:
    return MockMessageResponse(
        content=[MockContentBlock(block_type="text", text=text)], stop_reason=stop_reason
    )


def _tool(name: str, tool_id: str, **inputs: Any) -> MockContentBlock:
    return MockContentBlock(block_type="tool_use", name=name, tool_id=tool_id, input_data=inputs)


def _runners(tmp_path: Any) -> List[Any]:
    """(label, callable(client) -> result, first tool_use block) for each looping exercise."""
    def trail(name: str) -> ResponseTrail:
        return ResponseTrail(path=str(tmp_path / f"{name}.jsonl"))

    return [
        ("ts11", lambda c: run_ts11("q", c, trail("ts11")), _tool("calculator", "t1", expression="1+1")),
        ("ts12", lambda c: MultiAgentCoordinator(c, trail("ts12")).run_research_pipeline("q"),
         _tool("delegate_web_search", "t1", query="claude agent sdk")),
        ("ts13", lambda c: run_ts13("q", c, trail("ts13")),
         _tool("Task", "t1", subagent_type="web_researcher", prompt="p",
               task_metadata={"task_id": "T1"})),
        ("ts14", lambda c: run_prerequisite_agent("q", c, trail("ts14")),
         _tool("get_customer", "t1", email="alice@example.com")),
        ("ts15", lambda c: run_hook_agent("q", c, trail("ts15")),
         _tool("check_account_status", "t1", account_id="ACC-1")),
    ]


RUNNER_IDS = ["ts11", "ts12", "ts13", "ts14", "ts15"]


@pytest.mark.parametrize("idx", range(5), ids=RUNNER_IDS)
@pytest.mark.parametrize("stop_reason", ["max_tokens", "refusal", "stop_sequence", "banana"])
def test_non_end_turn_stop_reasons_raise(tmp_path, idx, stop_reason):
    _, run, _ = _runners(tmp_path)[idx]
    client = MockClaudeClient([_text("partial", stop_reason)])
    with pytest.raises(LoopStopped) as exc:
        run(client)
    assert exc.value.stop_reason == stop_reason
    assert exc.value.partial_text == "partial"


@pytest.mark.parametrize("idx", range(5), ids=RUNNER_IDS)
def test_pause_turn_continues_then_end_turn(tmp_path, idx):
    _, run, _ = _runners(tmp_path)[idx]
    paused = _text("working", "pause_turn")
    client = MockClaudeClient([paused, _text("all done")])
    result = run(client)
    text = result[0] if isinstance(result, tuple) else result
    assert text == "all done"
    # Second request carries the paused assistant turn back unchanged.
    sent = client.messages.call_history[1]["messages"]
    assert sent[-1] == {"role": "assistant", "content": paused.content}


@pytest.mark.parametrize("idx", range(5), ids=RUNNER_IDS)
def test_thinking_blocks_are_echoed_unchanged(tmp_path, idx):
    _, run, tool_block = _runners(tmp_path)[idx]
    thinking = MockContentBlock(block_type="thinking", text="reasoning...")
    first = MockMessageResponse(content=[thinking, tool_block], stop_reason="tool_use")
    client = MockClaudeClient([first, _text("done")])
    run(client)
    sent = client.messages.call_history[1]["messages"]
    assistant = next(m for m in sent if m["role"] == "assistant")
    assert assistant["content"] is first.content
    assert assistant["content"][0] is thinking
    result_msg = sent[sent.index(assistant) + 1]
    assert result_msg["role"] == "user"
    assert result_msg["content"][0]["tool_use_id"] == tool_block.id


@pytest.mark.parametrize("idx", range(5), ids=RUNNER_IDS)
def test_requests_use_coordinator_model_and_no_sampling_params(tmp_path, idx):
    _, run, _ = _runners(tmp_path)[idx]
    client = MockClaudeClient([_text("done")])
    run(client)
    call = client.messages.call_history[0]
    assert call["model"] == COORDINATOR_MODEL == "claude-sonnet-4-5"
    for forbidden in ("temperature", "top_k", "top_p"):
        assert forbidden not in call


def test_safety_cap_is_fallback_not_primary_stop(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "cap.jsonl"))
    looping = [
        MockMessageResponse(
            content=[_tool("get_customer", f"t{i}", email="alice@example.com")],
            stop_reason="tool_use",
        )
        for i in range(5)
    ]
    client = MockClaudeClient(looping)
    text, _ = run_prerequisite_agent("q", client, trail, max_turns=3)
    assert text == ""
    assert len(client.messages.call_history) == 3


def test_ts13_parallel_task_results_keep_order_and_unknown_tool_gets_error(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts13.jsonl"))
    blocks = [
        _tool("Task", "a", subagent_type="code_analyzer", prompt="p",
              task_metadata={"task_id": "T-CODE"}),
        _tool("bash", "b", cmd="ls"),
        _tool("Task", "c", subagent_type="web_researcher", prompt="p",
              task_metadata={"task_id": "T-WEB"}),
    ]
    client = MockClaudeClient([
        MockMessageResponse(content=blocks, stop_reason="tool_use"), _text("ok"),
    ])
    _, results = run_ts13("goal", client, trail)
    assert [r["task_id"] for r in results] == ["T-CODE", "T-WEB"]

    user_turn = client.messages.call_history[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in user_turn] == ["a", "b", "c"]
    assert user_turn[1].get("is_error") is True
    assert json.loads(user_turn[0]["content"])["task_id"] == "T-CODE"


def test_ts13_task_tool_only_offered_when_in_allowed_tools(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts13b.jsonl"))
    client = MockClaudeClient([_text("no spawning")])
    run_ts13("goal", client, trail, allowed_tools=["Read"])
    assert "tools" not in client.messages.call_history[0]

    client = MockClaudeClient([_text("spawning")])
    run_ts13("goal", client, trail)
    assert client.messages.call_history[0]["tools"][0]["name"] == "Agent"

    client = MockClaudeClient([_text("legacy")])
    run_ts13("goal", client, trail, allowed_tools=["Task"])
    assert client.messages.call_history[0]["tools"][0]["name"] == "Agent"


def test_ts14_gate_error_is_flagged_and_handoff_has_refund_amount(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts14.jsonl"))
    refund = _tool("process_refund", "r1", order_id="ORD-991", amount=85.0)
    client = MockClaudeClient([
        MockMessageResponse(content=[refund], stop_reason="tool_use"), _text("blocked"),
    ])
    _, state = run_prerequisite_agent("refund me", client, trail)
    result = client.messages.call_history[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True
    assert json.loads(result["content"])["errorCategory"] == "permission"
    assert state.verified_customer_id is None

    state = WorkflowState()
    state.verify_customer("CUST-101", "Alice")
    out = escalate_to_human("Damaged goods", "Approve exception", state, refund_amount=750.0)
    assert out["summary"]["refund_amount"] == 750.0
    assert out["summary"]["customer_id"] == "CUST-101"


def test_ts15_post_hook_trims_internal_fields_and_blocked_call_is_error(tmp_path):
    cleaned = post_tool_use_normalization_hook(
        "t", {"id": "A", "_db_shard": 7, "epoch_timestamp": 1728216000, "raw_status_code": 404}
    )
    assert "_db_shard" not in cleaned
    assert cleaned["status"] == "not_found"
    assert cleaned["iso_timestamp"].startswith("2024-10-06T")

    assert execute_with_hooks("process_payout", {"account_id": "A", "amount": 500.0})["success"]
    assert execute_with_hooks("process_payout", {"account_id": "A", "amount": 500.01})[
        "blocked_by_hook"
    ]

    trail = ResponseTrail(path=str(tmp_path / "ts15.jsonl"))
    payout = _tool("process_payout", "p1", account_id="A", amount=850.0)
    client = MockClaudeClient([
        MockMessageResponse(content=[payout], stop_reason="tool_use"), _text("escalated"),
    ])
    run_hook_agent("pay 850", client, trail)
    assert client.messages.call_history[1]["messages"][-1]["content"][0]["is_error"] is True


def test_ts16_models_per_pass_and_adaptive_plan(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts16.jsonl"))
    client = MockClaudeClient([_text("f1"), _text("f2"), _text("cross")])
    run_prompt_chaining_review([CodeFile("a.py", "x"), CodeFile("b.py", "y")], client, trail)
    models = [c["model"] for c in client.messages.call_history]
    assert models == [WORKER_MODEL, WORKER_MODEL, COORDINATOR_MODEL]
    assert WORKER_MODEL == "claude-haiku-4-5"

    plan = plan_adaptive_subtasks({
        "controller": ["service", "utils"], "service": ["utils"], "utils": [], "external": ["x"],
    })
    assert plan.index("utils") < plan.index("service") < plan.index("controller")
    assert plan_adaptive_subtasks({"a": ["b"], "b": ["a"]}) == ["a", "b"]


def test_ts17_resume_informs_session_of_changed_files(tmp_path):
    mgr = SessionManager()
    mgr.create_session("work", [{"role": "user", "content": "start"}])
    sess = mgr.resume("work", changed_files=["db/conn.py", "db/pool.py"])
    last = sess.messages[-1]["content"]
    assert "db/conn.py" in last and "db/pool.py" in last
    assert len(mgr.resume("work").messages) == 2  # no changes -> nothing added


def test_ts17_execute_turn_rejects_truncated_reply(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts17.jsonl"))
    mgr = SessionManager()
    sess = mgr.create_session("s", [{"role": "user", "content": "hi"}])
    with pytest.raises(LoopStopped):
        execute_turn(sess, MockClaudeClient([_text("cut off", "max_tokens")]), trail)
    assert len(sess.messages) == 1
    assert execute_turn(sess, MockClaudeClient([_text("fine")]), trail) == "fine"
