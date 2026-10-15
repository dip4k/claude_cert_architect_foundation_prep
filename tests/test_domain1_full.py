"""
Comprehensive Offline Unit Test Suite for Domain 1: Agentic Architecture & Orchestration.

Tests all 7 Task Statements (TS 1.1 to TS 1.7) 100% offline using lib.mock_claude.
Zero Anthropic API tokens used.
"""

import json
import pytest
from lib.mock_claude import (
    MockClaudeClient,
    MockMessageResponse,
    MockContentBlock,
)
from lib.response_logger import ResponseTrail

# TS 1.1 Imports
from domain1.ts_1_1_multi_tool_agent_loop.main import (
    calculator_tool,
    web_search_tool,
    run_agent as run_ts11_agent,
    TOOLS as TS11_TOOLS,
)

# TS 1.2 Imports
from domain1.ts_1_2_coordinator_subagents.main import (
    MultiAgentCoordinator,
    WebSearchSubagent,
    DocumentAnalysisSubagent,
    SynthesisSubagent,
)

# TS 1.3 Imports
from domain1.ts_1_3_subagent_invocation_spawning.main import (
    execute_subagent_task,
    run_parallel_spawning_coordinator,
    TASK_TOOL,
)

# TS 1.4 Imports
from domain1.ts_1_4_prerequisite_enforcement.main import (
    WorkflowState,
    get_customer,
    lookup_order,
    process_refund,
    escalate_to_human,
)

# TS 1.5 Imports
from domain1.ts_1_5_sdk_hooks.main import (
    compliance_interception_hook,
    post_tool_use_normalization_hook,
    execute_with_hooks,
    run_hook_agent,
)

# TS 1.6 Imports
from domain1.ts_1_6_task_decomposition.main import (
    CodeFile,
    run_prompt_chaining_review,
)

# TS 1.7 Imports
from domain1.ts_1_7_session_management.main import (
    SessionManager,
    SessionState,
    execute_turn,
)


# ==============================================================================
# TS 1.1: Agentic Loop & Stop Reason Lifecycle
# ==============================================================================

def test_ts11_calculator_and_search_tools():
    calc_res = calculator_tool("10 * (5 + 3)")
    assert calc_res["result"] == 80

    search_res = web_search_tool("speed of light")
    assert "299,792,458" in search_res["results"][0]["snippet"]


def test_ts11_agent_loop_offline(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts11_trail.jsonl"))

    resp_t1 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="calculator",
                tool_id="call_c1",
                input_data={"expression": "12 * 12"},
            )
        ],
        stop_reason="tool_use",
    )
    resp_t2 = MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="12 * 12 is 144.")],
        stop_reason="end_turn",
    )

    client = MockClaudeClient([resp_t1, resp_t2])
    res = run_ts11_agent("What is 12 * 12?", client, trail)
    assert "144" in res


# ==============================================================================
# TS 1.2: Coordinator-Subagent Patterns & Isolated Contexts
# ==============================================================================

def test_ts12_subagent_context_isolation():
    web_sub = WebSearchSubagent()
    # Runs solely with its query
    res = web_sub.execute("claude agent sdk")
    assert res["found"] is True
    assert len(res["findings"]) > 0

    doc_sub = DocumentAnalysisSubagent()
    res_doc = doc_sub.execute("doc_01", "certification metrics")
    assert res_doc["key_metrics"][0]["metric"] == "Passing score"

    synth_sub = SynthesisSubagent()
    res_synth = synth_sub.execute([res, res_doc], required_topics=["claude agent sdk", "missing topic"])
    assert res_synth["coverage_sufficient"] is False
    assert "missing topic" in res_synth["missing_topics"]


def test_ts12_coordinator_loop_offline(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts12_trail.jsonl"))

    resp_t1 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="delegate_web_search",
                tool_id="call_ws1",
                input_data={"query": "claude agent sdk"},
            )
        ],
        stop_reason="tool_use",
    )
    resp_t2 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="evaluate_synthesis",
                tool_id="call_syn1",
                input_data={"required_topics": ["claude agent sdk"]},
            )
        ],
        stop_reason="tool_use",
    )
    resp_t3 = MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="Comprehensive research synthesis report complete.")],
        stop_reason="end_turn",
    )

    client = MockClaudeClient([resp_t1, resp_t2, resp_t3])
    coord = MultiAgentCoordinator(client, trail)
    final_text, findings = coord.run_research_pipeline("Research Claude Agent SDK")
    assert "Comprehensive research synthesis" in final_text
    assert len(findings) >= 1


# ==============================================================================
# TS 1.3: Subagent Invocation & Parallel Spawning
# ==============================================================================

def test_ts13_metadata_content_separation():
    res = execute_subagent_task("web_researcher", "find rules", {"task_id": "T1"})
    assert res["status"] == "completed"
    finding = res["findings"][0]
    assert "content" in finding
    assert "metadata" in finding
    assert "source_url" in finding["metadata"]


def test_ts13_parallel_spawning_offline(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts13_trail.jsonl"))

    # Single response emitting TWO Task calls concurrently
    resp_t1 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="Task",
                tool_id="call_task1",
                input_data={
                    "subagent_type": "web_researcher",
                    "prompt": "Search slash commands",
                    "task_metadata": {"task_id": "T-WEB"},
                },
            ),
            MockContentBlock(
                block_type="tool_use",
                name="Task",
                tool_id="call_task2",
                input_data={
                    "subagent_type": "code_analyzer",
                    "prompt": "Analyze .claude/rules",
                    "task_metadata": {"task_id": "T-CODE"},
                },
            ),
        ],
        stop_reason="tool_use",
    )
    resp_t2 = MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="Both subagent tasks completed in parallel.")],
        stop_reason="end_turn",
    )

    client = MockClaudeClient([resp_t1, resp_t2])
    text, tasks = run_parallel_spawning_coordinator("Analyze configs", client, trail)
    assert len(tasks) == 2
    assert "completed in parallel" in text


# ==============================================================================
# TS 1.4: Workflow Enforcement & Handoff Patterns
# ==============================================================================

def test_ts14_prerequisite_enforcement_logic():
    state = WorkflowState()
    # Block before verification
    allowed, err = state.check_gate("process_refund", {"order_id": "ORD-991", "amount": 85.0})
    assert allowed is False
    assert err["errorCategory"] == "permission"

    # Allow after verification
    get_customer("alice@example.com", state)
    allowed, err = state.check_gate("process_refund", {"order_id": "ORD-991", "amount": 85.0})
    assert allowed is True
    assert err is None


# ==============================================================================
# TS 1.5: SDK Hooks for Interception & Normalization
# ==============================================================================

def test_ts15_compliance_interception_hook():
    # Below threshold ($500) -> allowed
    allowed_ok, _ = compliance_interception_hook("process_payout", {"amount": 350.00})
    assert allowed_ok is True

    # Exceeding threshold ($500) -> blocked
    allowed_blocked, block_data = compliance_interception_hook("process_payout", {"amount": 750.00})
    assert allowed_blocked is False
    assert block_data["blocked_by_hook"] is True
    assert block_data["redirect_action"] == "escalate_to_supervisor"


def test_ts15_post_tool_use_normalization_hook():
    raw_payload = {
        "account_id": "ACC-100",
        "epoch_timestamp": 1728216000,
        "raw_status_code": 200,
    }
    normalized = post_tool_use_normalization_hook("check_account_status", raw_payload)
    assert "iso_timestamp" in normalized
    assert "epoch_timestamp" not in normalized
    assert normalized["status"] == "active"
    assert "raw_status_code" not in normalized


def test_ts15_run_hook_agent_offline(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts15_trail.jsonl"))

    resp_t1 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="tool_use",
                name="check_account_status",
                tool_id="call_acc1",
                input_data={"account_id": "ACC-100"},
            )
        ],
        stop_reason="tool_use",
    )
    resp_t2 = MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="Account ACC-100 is active.")],
        stop_reason="end_turn",
    )

    client = MockClaudeClient([resp_t1, resp_t2])
    result = run_hook_agent("Check status of ACC-100", client, trail)
    assert "Account ACC-100 is active" in result


# ==============================================================================
# TS 1.6: Task Decomposition & Multi-Pass Review
# ==============================================================================

def test_ts16_prompt_chaining_decomposition(tmp_path):
    trail = ResponseTrail(path=str(tmp_path / "ts16_trail.jsonl"))

    # Responses for Pass 1 (file 1, file 2) and Pass 2 (integration)
    resp_f1 = MockMessageResponse(content=[MockContentBlock(block_type="text", text="auth_service lacks expiry.")])
    resp_f2 = MockMessageResponse(content=[MockContentBlock(block_type="text", text="api_router has SQL injection.")])
    resp_cross = MockMessageResponse(content=[MockContentBlock(block_type="text", text="Cross-file token verification vulnerable.")])

    client = MockClaudeClient([resp_f1, resp_f2, resp_cross])
    files = [
        CodeFile("auth_service.py", "jwt.encode()"),
        CodeFile("api_router.py", "SELECT * FROM users"),
    ]

    out = run_prompt_chaining_review(files, client, trail)
    assert "auth_service lacks expiry" in out["local_findings"]["auth_service.py"]
    assert "Cross-file token verification" in out["integration_findings"]


# ==============================================================================
# TS 1.7: Session State, Resumption & Forking
# ==============================================================================

def test_ts17_session_state_forking_and_summary():
    mgr = SessionManager()
    base_sess = mgr.create_session("base", [{"role": "user", "content": "Analyze architecture"}])
    assert base_sess.session_name == "base"

    # Fork session into branch A
    fork_a = base_sess.fork("branch_a")
    assert fork_a.session_name == "branch_a"
    assert fork_a.metadata["parent_session_id"] == base_sess.session_id

    # Mutate fork without polluting parent
    fork_a.messages.append({"role": "user", "content": "Branch A specific question"})
    assert len(fork_a.messages) == 2
    assert len(base_sess.messages) == 1

    # Resume with injected summary (stale context mitigation)
    clean_sess = mgr.resume_with_injected_summary(
        name="base",
        structured_summary="Summary of architecture findings.",
        new_instruction="Final recommendations",
    )
    assert "Summary of architecture findings" in clean_sess.messages[0]["content"]
    assert "Final recommendations" in clean_sess.messages[0]["content"]
