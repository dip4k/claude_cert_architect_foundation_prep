"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.4: Implement multi-step workflows with enforcement and handoff patterns
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated:
1. Programmatic prerequisite enforcement (blocking process_refund until get_customer verifies identity).
2. Why programmatic gates provide deterministic compliance where prompt instructions have non-zero failure rates.
3. Compiling structured handoff summaries (customer ID, root cause, refund amount, recommended action)
   when escalating to human agents.
4. ResponseTrail logging for JSONL audit trails.

Manual Execution (WSL Ubuntu):
    uv run domain1/ts_1_4_prerequisite_enforcement/main.py
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path
from domain1.loop_common import (
    COORDINATOR_MODEL,
    LoopStopped,
    read_stop_reason,
    response_text,
    stop_status,
)

load_dotenv()


# ==============================================================================
# 1. State & Programmatic Prerequisite Enforcement Gate
# ==============================================================================

class WorkflowState:
    """Tracks state and enforces deterministic compliance gates."""

    def __init__(self) -> None:
        self.verified_customer_id: Optional[str] = None
        self.verified_customer_name: Optional[str] = None
        self.order_lookup_done: bool = False
        self.escalated_to_human: bool = False
        self.escalation_summary: Optional[Dict[str, Any]] = None

    def verify_customer(self, customer_id: str, name: str) -> None:
        self.verified_customer_id = customer_id
        self.verified_customer_name = name

    def check_gate(self, tool_name: str, tool_inputs: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Deterministic Prerequisite Gate:
        Blocks downstream financial and sensitive operations until prerequisites are met.
        """
        if tool_name in ["process_refund", "lookup_order"] and not self.verified_customer_id:
            return False, {
                "isError": True,
                "errorCategory": "permission",
                "isRetryable": False,
                "message": (
                    f"Programmatic Gate Violation: Cannot call '{tool_name}' before customer identity "
                    "is verified via 'get_customer'. Deterministic policy requires verified customer ID."
                ),
            }
        return True, None


# ==============================================================================
# 2. Tool Implementations
# ==============================================================================

MOCK_CUSTOMERS = {
    "alice@example.com": {"id": "CUST-101", "name": "Alice Smith", "verified": True},
    "bob@example.com": {"id": "CUST-102", "name": "Bob Jones", "verified": True},
}

MOCK_ORDERS = {
    "ORD-991": {"customer_id": "CUST-101", "amount": 85.0, "status": "delivered", "eligible_for_refund": True},
}


def get_customer(email: str, state: WorkflowState) -> Dict[str, Any]:
    """Retrieves customer record and updates verification state."""
    record = MOCK_CUSTOMERS.get(email.lower().strip())
    if record:
        state.verify_customer(record["id"], record["name"])
        return {"found": True, "customer_id": record["id"], "name": record["name"]}
    return {
        "found": False,
        "isError": True,
        "errorCategory": "validation",
        "isRetryable": False,
        "message": f"No customer found with email: {email}",
    }


def lookup_order(order_id: str, state: WorkflowState) -> Dict[str, Any]:
    """Look up order details. Enforces customer ownership."""
    order = MOCK_ORDERS.get(order_id.upper().strip())
    if not order:
        return {"found": False, "isError": True, "errorCategory": "validation", "isRetryable": False, "message": "Order not found."}

    if order["customer_id"] != state.verified_customer_id:
        return {
            "isError": True,
            "errorCategory": "permission",
            "isRetryable": False,
            "message": "Order does not belong to the currently verified customer.",
        }

    state.order_lookup_done = True
    return {"found": True, "order_id": order_id, "amount": order["amount"], "eligible": order["eligible_for_refund"]}


def process_refund(order_id: str, amount: float, state: WorkflowState) -> Dict[str, Any]:
    """Executes refund for verified customer."""
    return {
        "success": True,
        "refund_id": f"REF-{uuid.uuid4().hex[:6].upper()}",
        "order_id": order_id,
        "customer_id": state.verified_customer_id,
        "amount": amount,
    }


def escalate_to_human(
    root_cause: str,
    recommended_action: str,
    state: WorkflowState,
    refund_amount: Optional[float] = None,
) -> Dict[str, Any]:
    """Structured handoff: a human can act on this without reading the transcript."""
    state.escalated_to_human = True
    state.escalation_summary = {
        "customer_id": state.verified_customer_id or "UNVERIFIED",
        "customer_name": state.verified_customer_name or "UNKNOWN",
        "root_cause": root_cause,
        "refund_amount": refund_amount,
        "recommended_action": recommended_action,
        "handoff_timestamp": "2026-10-06T12:00:00Z",
    }
    return {
        "escalated": True,
        "message": "Ticket successfully escalated with structured handoff summary.",
        "summary": state.escalation_summary,
    }


# ==============================================================================
# 3. Tool Schemas
# ==============================================================================

TOOLS = [
    {
        "name": "get_customer",
        "description": "Verifies customer identity by email address. Must be called before any order or refund operations.",
        "input_schema": {
            "type": "object",
            "properties": {"email": {"type": "string", "description": "Customer email address."}},
            "required": ["email"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Retrieves order status and eligibility. Requires prior customer identity verification.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID (e.g. ORD-991)."}},
            "required": ["order_id"],
        },
    },
    {
        "name": "process_refund",
        "description": "Processes a monetary refund for an order. Blocked by a code gate until get_customer has verified the customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to refund."},
                "amount": {"type": "number", "description": "Refund amount."},
            },
            "required": ["order_id", "amount"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalates session to a human supervisor with a structured handoff protocol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "root_cause": {"type": "string", "description": "Root cause explanation."},
                "recommended_action": {"type": "string", "description": "Recommended supervisor action."},
                "refund_amount": {"type": "number", "description": "Refund amount in question, if any."},
            },
            "required": ["root_cause", "recommended_action"],
        },
    },
]


# ==============================================================================
# 4. Agentic Loop with Prerequisite Enforcement
# ==============================================================================

def execute_dispatched_tool(tool_name: str, tool_inputs: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
    """Checks programmatic gates before dispatching tool call."""
    allowed, gate_err = state.check_gate(tool_name, tool_inputs)
    if not allowed:
        return gate_err or {"error": "Gate violation"}

    if tool_name == "get_customer":
        return get_customer(tool_inputs["email"], state)
    elif tool_name == "lookup_order":
        return lookup_order(tool_inputs["order_id"], state)
    elif tool_name == "process_refund":
        return process_refund(tool_inputs["order_id"], tool_inputs["amount"], state)
    elif tool_name == "escalate_to_human":
        return escalate_to_human(
            tool_inputs["root_cause"],
            tool_inputs["recommended_action"],
            state,
            tool_inputs.get("refund_amount"),
        )
    return {"error": f"Unknown tool: {tool_name}"}


def run_prerequisite_agent(
    prompt: str,
    client: Any,
    trail: ResponseTrail,
    state: Optional[WorkflowState] = None,
    max_turns: int = 5,
) -> Tuple[str, WorkflowState]:
    """
    Agentic loop with programmatic prerequisite enforcement.

    max_turns is a safety cap (fallback only). The loop ends on stop_reason == "end_turn";
    any other terminal stop_reason raises LoopStopped.
    """
    if state is None:
        state = WorkflowState()

    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, COORDINATOR_MODEL)
    messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]
    parser = create_parser()

    for turn in range(1, max_turns + 1):
        trail.api_request(session_id, turn, messages)
        response = client.messages.create(
            model=COORDINATOR_MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        stop_reason = read_stop_reason(parser, response)

        if stop_reason == "tool_use":
            # Echo assistant content unchanged (including any thinking blocks and signatures).
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if getattr(block, "type", "") == "tool_use":
                    tool_name = block.name
                    tool_inputs = block.input
                    tool_id = block.id

                    trail.tool_call(session_id, turn, tool_name, tool_id, tool_inputs)
                    result = execute_dispatched_tool(tool_name, tool_inputs, state)
                    trail.tool_result(session_id, turn, tool_name, tool_id, result)

                    tool_result: Dict[str, Any] = {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result),
                    }
                    if result.get("isError"):
                        tool_result["is_error"] = True
                    tool_results.append(tool_result)

            messages.append({"role": "user", "content": tool_results})

        elif stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})

        elif stop_reason == "end_turn":
            final_text = response_text(response)
            trail.session_end(session_id, final_text, "end_turn")
            return final_text, state

        else:
            text = response_text(response)
            trail.session_end(session_id, text, stop_status(stop_reason))
            raise LoopStopped(stop_reason, text)

    trail.session_end(session_id, "", "safety_cap_reached")
    return "", state


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY missing in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    print("Running Customer Support Workflow with Programmatic Prerequisite Enforcement...")
    prompt = "Hi, my name is Alice (alice@example.com). Please look up order ORD-991 and process my refund."
    ans, state = run_prerequisite_agent(prompt, client, trail)
    print(f"\nFinal Response:\n{ans}")
    print(f"Verified Customer ID: {state.verified_customer_id}")


if __name__ == "__main__":
    main()
