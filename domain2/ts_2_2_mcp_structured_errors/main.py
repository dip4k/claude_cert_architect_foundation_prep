"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.2: Implement structured error responses for MCP tools
Exam Scenario 1 & 4

Key Exam Concepts Demonstrated:
1. Returning structured error metadata using the MCP isError flag pattern.
2. Distinct error categories:
   - "transient": Timeouts, connection failures -> isRetryable: true
   - "validation": Malformed parameters -> isRetryable: false
   - "business": Policy violations, account limits -> isRetryable: false, customer-friendly message
   - "permission": Insufficient privileges -> isRetryable: false
3. Why uniform generic errors ("Operation failed") prevent agents from making appropriate recovery decisions.
4. Distinguishing access failures from valid empty results (successful queries with 0 matches).

Manual Execution (WSL Ubuntu):
    uv run domain2/ts_2_2_mcp_structured_errors/main.py
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

load_dotenv()


# ==============================================================================
# 1. MCP Structured Tool Error Model
# ==============================================================================

def create_mcp_error(
    category: str,
    message: str,
    is_retryable: bool,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Formats an MCP structured error response conforming to exam standards."""
    return {
        "isError": True,
        "errorCategory": category,  # "transient" | "validation" | "business" | "permission"
        "isRetryable": is_retryable,
        "message": message,
        "details": details or {},
    }


# ==============================================================================
# 2. Tools with Structured Error Responses
# ==============================================================================

def query_inventory(sku: str, simulate_mode: str = "normal") -> Dict[str, Any]:
    """
    Inventory query tool demonstrating transient error vs empty match vs success.
    """
    if simulate_mode == "timeout":
        # Transient failure (e.g. database connection timeout)
        return create_mcp_error(
            category="transient",
            message="Database query timed out while reaching warehouse cluster.",
            is_retryable=True,
            details={"service": "warehouse_db", "timeout_ms": 5000},
        )

    if not sku.startswith("SKU-"):
        # Validation error
        return create_mcp_error(
            category="validation",
            message=f"Invalid SKU format: '{sku}'. SKUs must match format SKU-XXXXX.",
            is_retryable=False,
        )

    if sku == "SKU-99999":
        # Valid empty result (NOT an error!)
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
    """
    Refund tool demonstrating business policy error.
    """
    if amount > 500.0:
        # Business policy violation: requires human supervisor escalation
        return create_mcp_error(
            category="business",
            message=(
                f"Refund amount ${amount:.2f} exceeds automated policy threshold of $500.00. "
                "Must be routed to human supervisor for authorization."
            ),
            is_retryable=False,
            details={"max_allowed_automated": 500.00, "requested_amount": amount},
        )

    return {
        "isError": False,
        "success": True,
        "refund_id": f"REF-{uuid.uuid4().hex[:6].upper()}",
        "customer_id": customer_id,
        "amount": amount,
    }


TOOLS = [
    {
        "name": "query_inventory",
        "description": "Checks warehouse inventory levels by SKU. Returns stock count or structured error metadata.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Item SKU, e.g. SKU-10421."},
                "simulate_mode": {
                    "type": "string",
                    "enum": ["normal", "timeout"],
                    "description": "Simulation mode for testing error handling.",
                },
            },
            "required": ["sku"],
        },
    },
    {
        "name": "issue_refund",
        "description": "Processes refund for customer up to $500.00 automated limit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID."},
                "amount": {"type": "number", "description": "Refund dollar amount."},
            },
            "required": ["customer_id", "amount"],
        },
    },
]


def dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "query_inventory":
        return query_inventory(args.get("sku", ""), args.get("simulate_mode", "normal"))
    elif name == "issue_refund":
        return issue_refund(args.get("customer_id", ""), float(args.get("amount", 0.0)))
    return create_mcp_error("validation", f"Unknown tool: '{name}'", False)


# ==============================================================================
# 3. Agentic Loop with Error Interpretation
# ==============================================================================

def run_structured_error_agent(
    prompt: str,
    client: Any,
    trail: ResponseTrail,
    max_turns: int = 4,
) -> str:
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, "claude-haiku-4-5")
    messages = [{"role": "user", "content": prompt}]
    parser = create_parser()

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
                    result = dispatch_tool(tool_name, tool_input)
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
        print("ANTHROPIC_API_KEY not found in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    print("Running MCP Structured Error Handler Exercise...")
    # Example: Policy exceeding refund
    prompt = "Issue a refund of $750.00 to customer CUST-882 for damaged monitor."
    res = run_structured_error_agent(prompt, client, trail)
    print(f"\nFinal Agent Response:\n{res}")


if __name__ == "__main__":
    main()
