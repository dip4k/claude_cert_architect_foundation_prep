"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.5: Apply Agent SDK hooks for tool call interception and data normalization
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated:
1. Tool call interception hooks: Intercept outgoing tool calls before execution to enforce
   hard business compliance rules (e.g. blocking financial operations exceeding $500 threshold
   and redirecting to human supervisor escalation).
2. PostToolUse hooks: Intercept incoming raw tool results to normalize heterogeneous formats
   (Unix epoch timestamps vs ISO 8601 strings, numeric status codes to canonical enums)
   before the model processes them.
3. Deterministic guarantees vs probabilistic compliance: Why hooks provide 100% policy enforcement
   whereas prompt instructions have non-zero failure rates.
4. ResponseTrail logging for JSONL audit trails.

Manual Execution (WSL Ubuntu):
    uv run domain1/ts_1_5_sdk_hooks/main.py
"""

import datetime
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path

load_dotenv()


# ==============================================================================
# 1. SDK Hook Architecture
# ==============================================================================

class PolicyViolationError(Exception):
    """Raised when an outgoing tool call violates compliance policies."""
    pass


def compliance_interception_hook(tool_name: str, tool_inputs: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Outgoing Tool Call Interception Hook:
    Enforces hard policy bounds. Cannot be bypassed by prompt injection or model hallucination.
    """
    if tool_name == "process_payout":
        amount = float(tool_inputs.get("amount", 0.0))
        MAX_AUTONOMOUS_THRESHOLD = 500.00
        if amount > MAX_AUTONOMOUS_THRESHOLD:
            # Block tool call deterministically
            return False, {
                "blocked_by_hook": True,
                "hook_type": "PreToolExecutionComplianceGate",
                "reason": (
                    f"Compliance Threshold Exceeded: Requested payout ${amount:.2f} exceeds "
                    f"${MAX_AUTONOMOUS_THRESHOLD:.2f} limit. Action blocked. Diverting to supervisor."
                ),
                "redirect_action": "escalate_to_supervisor",
            }
    return True, None


def post_tool_use_normalization_hook(tool_name: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    PostToolUse Hook:
    Normalizes heterogeneous data formats (Unix epoch vs ISO 8601, numeric HTTP codes to semantic strings)
    before the model processes the tool result in subsequent reasoning turns.
    """
    normalized = dict(raw_result)

    # 1. Normalize timestamps to ISO 8601
    if "epoch_timestamp" in normalized:
        epoch = normalized.pop("epoch_timestamp")
        dt = datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc)
        normalized["iso_timestamp"] = dt.isoformat()

    # 2. Normalize raw numeric status codes to semantic status enums
    if "raw_status_code" in normalized:
        code = normalized.pop("raw_status_code")
        STATUS_MAP = {
            200: "active",
            201: "created",
            400: "client_error",
            404: "not_found",
            500: "server_error",
        }
        normalized["status"] = STATUS_MAP.get(code, "unknown")

    return normalized


# ==============================================================================
# 2. Tools
# ==============================================================================

def check_account_status(account_id: str) -> Dict[str, Any]:
    """Tool returning legacy format with raw epoch timestamp and numeric status code."""
    return {
        "account_id": account_id,
        "epoch_timestamp": 1728216000,  # Legacy timestamp
        "raw_status_code": 200,          # Legacy integer code
        "balance": 1250.00,
    }


def process_payout(account_id: str, amount: float) -> Dict[str, Any]:
    """Tool that performs monetary payout."""
    return {
        "success": True,
        "payout_id": f"PAY-{uuid.uuid4().hex[:6].upper()}",
        "account_id": account_id,
        "amount": amount,
    }


TOOLS = [
    {
        "name": "check_account_status",
        "description": "Checks account balance and activity status.",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
        },
    },
    {
        "name": "process_payout",
        "description": "Issues payout from account. Limited to automated threshold.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["account_id", "amount"],
        },
    },
]


# ==============================================================================
# 3. Agentic Loop with Hook Integration
# ==============================================================================

def execute_with_hooks(tool_name: str, tool_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Executes tool through interception and post-execution normalization hooks."""
    # Step 1: Pre-execution Interception Hook
    allowed, hook_block_data = compliance_interception_hook(tool_name, tool_inputs)
    if not allowed:
        return hook_block_data or {"error": "Blocked by hook"}

    # Step 2: Tool Execution
    if tool_name == "check_account_status":
        raw = check_account_status(tool_inputs.get("account_id", ""))
    elif tool_name == "process_payout":
        raw = process_payout(tool_inputs.get("account_id", ""), float(tool_inputs.get("amount", 0.0)))
    else:
        raw = {"error": f"Unknown tool: {tool_name}"}

    # Step 3: PostToolUse Normalization Hook
    return post_tool_use_normalization_hook(tool_name, raw)


def run_hook_agent(
    prompt: str,
    client: Any,
    trail: ResponseTrail,
    max_turns: int = 4,
) -> str:
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, "claude-haiku-4-5")
    parser = create_parser()
    messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]

    for turn in range(1, max_turns + 1):
        trail.api_request(session_id, turn, messages)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        parse_result = parser.parse(response.model_dump())
        parsed = parse_result.get("data") if parse_result.get("success") else None
        stop_reason = parsed.stop_reason if parsed else getattr(response, "stop_reason", "end_turn")

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if getattr(block, "type", "") == "tool_use":
                    tool_name = block.name
                    tool_id = block.id
                    tool_input = block.input

                    trail.tool_call(session_id, turn, tool_name, tool_id, tool_input)
                    result = execute_with_hooks(tool_name, tool_input)
                    trail.tool_result(session_id, turn, tool_name, tool_id, result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})

        elif stop_reason == "end_turn":
            final_text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
            trail.session_end(session_id, final_text, "end_turn")
            return final_text

    trail.session_end(session_id, "", "max_turns_exceeded")
    return ""


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY missing in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    print("Running Hook Demonstration 1 (Normalized timestamps):")
    res1 = run_hook_agent("Check status of account ACC-100", client, trail)
    print(res1)

    print("\nRunning Hook Demonstration 2 (Policy Interception of > $500 payout):")
    res2 = run_hook_agent("Issue payout of $850.00 to account ACC-100", client, trail)
    print(res2)


if __name__ == "__main__":
    main()
