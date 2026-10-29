"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.2: Implement structured error responses for MCP tools
Exam Scenarios 1 (Customer Support) and 3 (Research)

Key Exam Concepts Demonstrated:
1. Every failure sets isError=True and carries errorCategory, isRetryable and message.
   - "transient":  timeouts, outages            -> isRetryable True
   - "validation": malformed input              -> isRetryable False (fix the input)
   - "business":   policy limit, e.g. refund    -> isRetryable False (explain or escalate)
   - "permission": caller not allowed           -> isRetryable False (do not retry)
2. A uniform "Operation failed" hides all of this and is an anti-pattern.
   `validate_error_payload` rejects it.
3. A valid empty result (query worked, 0 matches) is NOT an error: isError=False.
4. A subagent recovers from transient errors locally (`recover_locally`) and propagates only
   unresolved errors, with partial results and what was attempted.

Manual Execution (WSL Ubuntu, makes API calls - run by hand only):
    uv run domain2/ts_2_2_mcp_structured_errors/main.py
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.response_logger import ResponseTrail, get_agent_trail_path  # noqa: E402
from lib.sdk_parser_py import create_parser  # noqa: E402

COORDINATOR_MODEL = "claude-sonnet-4-5"  # interprets errors and decides recovery
WORKER_MODEL = "claude-haiku-4-5"  # subagent work
MAX_ITERATIONS = 5  # safety cap only; stop_reason drives the loop

ERROR_CATEGORIES = ("transient", "validation", "business", "permission")
GENERIC_MESSAGES = ("operation failed", "error", "failed", "something went wrong")
REFUND_AUTO_LIMIT = 500.0

# ==============================================================================
# 1. MCP structured error model
# ==============================================================================


def create_mcp_error(
    category: str,
    message: str,
    is_retryable: bool,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a structured tool error: isError, errorCategory, isRetryable, message, details."""
    if category not in ERROR_CATEGORIES:
        raise ValueError(f"errorCategory must be one of {ERROR_CATEGORIES}, got '{category}'")
    return {
        "isError": True,
        "errorCategory": category,
        "isRetryable": is_retryable,
        "message": message,
        "details": details or {},
    }


def validate_error_payload(payload: Dict[str, Any]) -> List[str]:
    """Return schema problems of a tool error payload (empty list means valid)."""
    problems: List[str] = []
    if payload.get("isError") is not True:
        problems.append("isError must be True")
    if payload.get("errorCategory") not in ERROR_CATEGORIES:
        problems.append(f"errorCategory must be one of {ERROR_CATEGORIES}")
    if not isinstance(payload.get("isRetryable"), bool):
        problems.append("isRetryable must be a bool")
    message = str(payload.get("message", "")).strip()
    if not message or message.lower().rstrip(".") in GENERIC_MESSAGES:
        problems.append("message must be specific and human-readable, not 'Operation failed'")
    if payload.get("errorCategory") in ("validation", "business", "permission"):
        if payload.get("isRetryable") is True:
            problems.append("only transient errors may be retryable")
    return problems


def to_call_tool_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a payload in the MCP CallToolResult shape (isError + JSON text content)."""
    return {
        "isError": bool(payload.get("isError", False)),
        "content": [{"type": "text", "text": json.dumps(payload)}],
    }


def recovery_action(error: Dict[str, Any]) -> str:
    """Map an error to the next step: retry, fix_input, explain_or_escalate or stop."""
    category = error.get("errorCategory")
    if category == "transient" and error.get("isRetryable"):
        return "retry"
    if category == "validation":
        return "fix_input"
    if category == "business":
        return "explain_or_escalate"
    return "stop"


# ==============================================================================
# 2. Tools with structured errors
# ==============================================================================


def query_inventory(sku: str, simulate_mode: str = "normal") -> Dict[str, Any]:
    """Return stock for a SKU: transient error, validation error, empty result or success."""
    if simulate_mode == "timeout":
        return create_mcp_error(
            category="transient",
            message="Warehouse database timed out. Retry the same request shortly.",
            is_retryable=True,
            details={"service": "warehouse_db", "timeout_ms": 5000},
        )

    if not sku.startswith("SKU-"):
        return create_mcp_error(
            category="validation",
            message=f"Invalid SKU format: '{sku}'. SKUs must match format SKU-XXXXX.",
            is_retryable=False,
        )

    if sku == "SKU-99999":
        # Valid empty result: the query worked and the item has zero stock. NOT an error.
        return {
            "isError": False,
            "found": True,
            "sku": sku,
            "stock_count": 0,
            "is_empty_result": True,
            "message": "Item is recognized but currently out of stock.",
        }

    return {
        "isError": False,
        "found": True,
        "sku": sku,
        "stock_count": 42,
        "warehouse_location": "Bay-4B",
    }


def issue_refund(customer_id: str, amount: float) -> Dict[str, Any]:
    """Refund up to REFUND_AUTO_LIMIT; larger amounts are a non-retryable business error."""
    if amount > REFUND_AUTO_LIMIT:
        return create_mcp_error(
            category="business",
            message=(
                f"Refund amount ${amount:.2f} exceeds automated policy threshold of "
                f"${REFUND_AUTO_LIMIT:.2f}. Must be routed to a human supervisor for approval."
            ),
            is_retryable=False,
            details={"max_allowed_automated": REFUND_AUTO_LIMIT, "requested_amount": amount},
        )

    return {
        "isError": False,
        "success": True,
        "refund_id": f"REF-{uuid.uuid4().hex[:6].upper()}",
        "customer_id": customer_id,
        "amount": amount,
    }


def read_payment_method(customer_id: str, caller_scope: str) -> Dict[str, Any]:
    """Return a masked card; callers without the 'payments:read' scope get a permission error."""
    if caller_scope != "payments:read":
        return create_mcp_error(
            category="permission",
            message="This agent is not allowed to read payment methods. Escalate to a human.",
            is_retryable=False,
            details={"required_scope": "payments:read", "caller_scope": caller_scope},
        )
    return {"isError": False, "customer_id": customer_id, "card_last4": "4242"}


TOOLS: List[Dict[str, Any]] = [
    {
        "name": "query_inventory",
        "description": (
            "Checks warehouse stock for one SKU. Returns stock_count (0 is a valid result, not "
            "an error) or a structured error with errorCategory and isRetryable. "
            "Do NOT use for order status; use lookup_order. Example: 'Is SKU-10421 in stock?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Item SKU, e.g. SKU-10421."},
                "simulate_mode": {
                    "type": "string",
                    "enum": ["normal", "timeout"],
                    "description": "Test switch: 'timeout' forces a transient error.",
                },
            },
            "required": ["sku"],
        },
    },
    {
        "name": "issue_refund",
        "description": (
            f"Issues a refund of up to ${REFUND_AUTO_LIMIT:.0f} for a verified customer. Larger "
            "amounts return a business error (isRetryable false): escalate, do not retry. "
            "Example: 'Refund $40 to CUST-101'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID, e.g. CUST-101."},
                "amount": {"type": "number", "description": "Refund amount in USD."},
            },
            "required": ["customer_id", "amount"],
        },
    },
]


def dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Route a tool_use block to its implementation; unknown tools return a validation error."""
    if name == "query_inventory":
        return query_inventory(args.get("sku", ""), args.get("simulate_mode", "normal"))
    if name == "issue_refund":
        return issue_refund(args.get("customer_id", ""), float(args.get("amount", 0.0)))
    return create_mcp_error("validation", f"Unknown tool: '{name}'", False)


# ==============================================================================
# 3. Subagent local recovery: retry transient, propagate the rest with context
# ==============================================================================


def recover_locally(
    call: Callable[[], Dict[str, Any]],
    max_retries: int = 2,
    partial_results: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Retry transient errors; return ok, or unresolved with partial results and attempts."""
    attempts: List[Dict[str, Any]] = []
    result: Dict[str, Any] = {}
    for attempt in range(1, max_retries + 2):
        result = call()
        if not result.get("isError"):
            return {"status": "ok", "result": result, "attempts": attempts}
        attempts.append(
            {
                "attempt": attempt,
                "errorCategory": result.get("errorCategory"),
                "message": result.get("message"),
            }
        )
        if recovery_action(result) != "retry":
            break
    return {
        "status": "unresolved",
        "error": result,
        "attempted": attempts,
        "partial_results": list(partial_results or []),
    }


# ==============================================================================
# 4. Agentic loop with error interpretation (stop_reason only)
# ==============================================================================


def _text_of(response: Any) -> str:
    """Join the text blocks of a response."""
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")


def run_structured_error_agent(
    prompt: str,
    client: Any,
    trail: ResponseTrail,
    max_iterations: int = MAX_ITERATIONS,
    model: str = COORDINATOR_MODEL,
) -> str:
    """Run a tool loop that returns each tool_result as JSON so Claude can read errorCategory.

    Control flow uses stop_reason only; max_iterations is a safety cap.
    """
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, model)
    messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]
    parser = create_parser()

    for iteration in range(1, max_iterations + 1):
        trail.api_request(session_id, iteration, messages)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        parse_result = parser.parse(response.model_dump())
        parsed = parse_result.get("data") if parse_result.get("success") else None
        stop_reason: Optional[str] = parsed.stop_reason if parsed else response.stop_reason

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results: List[Dict[str, Any]] = []
            for block in response.content:
                if getattr(block, "type", "") != "tool_use":
                    continue
                trail.tool_call(session_id, iteration, block.name, block.id, block.input)
                result = dispatch_tool(block.name, block.input)
                trail.tool_result(session_id, iteration, block.name, block.id, result)
                tool_result: Dict[str, Any] = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
                if result.get("isError"):
                    tool_result["is_error"] = True
                tool_results.append(tool_result)
            messages.append({"role": "user", "content": tool_results})
        elif stop_reason == "end_turn":
            final_text = _text_of(response)
            trail.session_end(session_id, final_text, "end_turn")
            return final_text
        elif stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
        elif stop_reason == "max_tokens":
            partial = _text_of(response)
            trail.session_end(session_id, partial, "max_tokens")
            return partial
        elif stop_reason == "refusal":
            trail.session_end(session_id, "", "refusal")
            return ""
        else:
            trail.session_end(session_id, "", f"unexpected_stop_reason:{stop_reason}")
            return ""

    trail.session_end(session_id, "", "safety_cap_reached")
    return ""


def main() -> None:
    """Manual entry point (makes live API calls)."""
    import anthropic
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment or .env. Set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail = ResponseTrail(path=get_agent_trail_path(__file__))
    prompt = "Issue a refund of $750.00 to customer CUST-882 for damaged monitor."
    print(run_structured_error_agent(prompt, client, trail))


if __name__ == "__main__":
    main()
