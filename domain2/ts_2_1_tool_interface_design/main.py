"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries
Task Statement 2.3: Distribute tools appropriately and configure tool choice
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated:
1. Tool descriptions as the primary router: Differentiating similar tools (e.g., lookup_order vs get_customer)
   with explicit boundaries, parameter constraints, and example queries to eliminate misrouting.
2. Principle of least privilege: Assigning focused tool subsets.
3. tool_choice forced selection: Enforcing tool_choice: {"type": "tool", "name": "get_customer"}
   to guarantee identity verification occurs before other tools.
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
# Production Tool Declarations with Differentiated Boundary Descriptions
# ==============================================================================

TOOLS = [
    {
        "name": "get_customer",
        "description": (
            "Retrieves customer identity, contact information, and account status by email address or customer ID. "
            "Use this tool EXCLUSIVELY for verifying user identity, checking membership tier, or retrieving account profiles. "
            "BOUNDARY: Do NOT call this tool for order tracking, tracking numbers, or shipment history; use lookup_order instead. "
            "Example queries: 'Verify customer alice@example.com', 'Retrieve account profile for CUST-101'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Customer email (e.g. 'user@example.com') or Customer ID matching format 'CUST-XXXX'.",
                }
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieves order status, line items, shipment carrier tracking, and return eligibility for a specific order. "
            "Use this tool when users ask about delivery status, order contents, package location, or return windows. "
            "BOUNDARY: Do NOT call this tool for general user profile lookups without an order reference; use get_customer instead. "
            "Example queries: 'Where is order ORD-9821?', 'Check return eligibility for ORD-4412'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Unique Order ID matching prefix 'ORD-' followed by digits (e.g. 'ORD-9821').",
                }
            },
            "required": ["order_id"],
        },
    },
]

MOCK_CUSTOMER_DB = {
    "alice@example.com": {"customer_id": "CUST-101", "name": "Alice Smith", "tier": "Gold"},
    "cust-101": {"customer_id": "CUST-101", "name": "Alice Smith", "tier": "Gold"},
}

MOCK_ORDER_DB = {
    "ord-9821": {"order_id": "ORD-9821", "status": "Shipped", "carrier": "FedEx", "tracking": "12345678"},
}


def get_customer_tool(identifier: str) -> Dict[str, Any]:
    norm = identifier.lower().strip()
    if norm in MOCK_CUSTOMER_DB:
        return {"found": True, "customer": MOCK_CUSTOMER_DB[norm]}
    return {"found": False, "message": f"Customer '{identifier}' not found."}


def lookup_order_tool(order_id: str) -> Dict[str, Any]:
    norm = order_id.lower().strip()
    if norm in MOCK_ORDER_DB:
        return {"found": True, "order": MOCK_ORDER_DB[norm]}
    return {"found": False, "message": f"Order '{order_id}' not found."}


def dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "get_customer":
        return get_customer_tool(args.get("identifier", ""))
    elif name == "lookup_order":
        return lookup_order_tool(args.get("order_id", ""))
    return {"error": f"Unknown tool: {name}"}


def run_bounded_tool_agent(
    prompt: str,
    client: Any,
    trail: ResponseTrail,
    force_customer_first: bool = False,
    max_turns: int = 3,
) -> str:
    """Agent demonstrating differentiated boundaries and optional forced tool choice."""
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, "claude-haiku-4-5")
    messages = [{"role": "user", "content": prompt}]
    parser = create_parser()

    for turn in range(1, max_turns + 1):
        trail.api_request(session_id, turn, messages)

        # Apply forced tool choice on Turn 1 if requested
        tool_choice: Any = "auto"
        if turn == 1 and force_customer_first:
            tool_choice = {"type": "tool", "name": "get_customer"}

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            tools=TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )

        parse_result = parser.parse(response.model_dump())
        parsed = parse_result.get("data") if parse_result.get("success") else None
        stop_reason = parsed.stop_reason if parsed else getattr(response, "stop_reason", "end_turn")

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for b in response.content:
                if getattr(b, "type", "") == "tool_use":
                    trail.tool_call(session_id, turn, b.name, b.id, b.input)
                    res = dispatch_tool(b.name, b.input)
                    trail.tool_result(session_id, turn, b.name, b.id, res)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": json.dumps(res),
                    })
            messages.append({"role": "user", "content": tool_results})
        elif stop_reason == "end_turn":
            text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
            trail.session_end(session_id, text, "end_turn")
            return text

    trail.session_end(session_id, "", "max_turns_exceeded")
    return ""


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to run manually.")
        return
    client = anthropic.Anthropic(api_key=api_key)
    trail = ResponseTrail(path=get_agent_trail_path(__file__))
    res = run_bounded_tool_agent("Check tracking for order ORD-9821", client, trail)
    print(res)


if __name__ == "__main__":
    main()
