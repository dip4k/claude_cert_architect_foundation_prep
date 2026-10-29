"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated:
1. Tool descriptions are the primary selection mechanism: purpose, input formats, example
   queries, edge cases and boundaries ("use lookup_order instead") all live in the description.
2. Overlapping descriptions cause misrouting. `description_overlap` and `audit_tool` make the
   problem measurable offline; `SPLIT_DOCUMENT_TOOLS` shows the rename/split fix.
3. A forced tool_choice ({"type": "tool", ...}) is valid ONLY when extended thinking is off.
   The loop below sends no `thinking` and no `temperature`.
4. The loop reacts to stop_reason only (tool_use, end_turn, max_tokens, pause_turn, refusal).
   MAX_ITERATIONS is a safety cap (fallback), never the primary stop condition.

Manual Execution (WSL Ubuntu, makes API calls - run by hand only):
    uv run domain2/ts_2_1_tool_interface_design/main.py
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.response_logger import ResponseTrail, get_agent_trail_path  # noqa: E402
from lib.sdk_parser_py import create_parser  # noqa: E402

COORDINATOR_MODEL = "claude-sonnet-4-5"  # routing and reasoning
WORKER_MODEL = "claude-haiku-4-5"  # focused, high-volume work
MAX_ITERATIONS = 5  # safety cap only; stop_reason drives the loop

# ==============================================================================
# Production tool declarations: purpose, formats, examples and boundaries
# ==============================================================================

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_customer",
        "description": (
            "Retrieves customer identity, contact information, and account status by email "
            "address or customer ID. Use this tool ONLY to verify identity, check membership "
            "tier, or fetch an account profile. "
            "BOUNDARY: Do NOT call this tool for order tracking, tracking numbers, or shipment "
            "history; use lookup_order instead. "
            "Edge case: returns found=false for unknown identifiers (not an error). "
            "Example queries: 'Verify customer alice@example.com', "
            "'Retrieve account profile for CUST-101'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": (
                        "Customer email (e.g. 'user@example.com') or Customer ID matching "
                        "format 'CUST-XXXX'."
                    ),
                }
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieves order status, line items, shipment carrier tracking, and return "
            "eligibility for a specific order. Use this tool when users ask about delivery "
            "status, order contents, package location, or return windows. "
            "BOUNDARY: Do NOT call this tool for general profile lookups without an order "
            "reference; use get_customer instead. "
            "Edge case: returns found=false when the order ID does not exist. "
            "Example queries: 'Where is order ORD-9821?', "
            "'Check return eligibility for ORD-4412'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": (
                        "Unique Order ID with prefix 'ORD-' followed by digits "
                        "(e.g. 'ORD-9821')."
                    ),
                }
            },
            "required": ["order_id"],
        },
    },
]

# Anti-pattern: two tools whose descriptions overlap (the exam's analyze_content example).
VAGUE_TOOLS: List[Dict[str, Any]] = [
    {"name": "analyze_content", "description": "Analyzes content and returns results."},
    {"name": "analyze_document", "description": "Analyzes a document and returns results."},
]

# Fix: rename/split by purpose so each name and description has one job.
SPLIT_DOCUMENT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "extract_data_points",
        "description": (
            "Extracts named fields (dates, amounts, names) from ONE document by doc_id. "
            "Do NOT use for summaries; use summarize_content. "
            "Example: 'Pull the invoice total from DOC-12'."
        ),
    },
    {
        "name": "summarize_content",
        "description": (
            "Writes a short narrative summary of ONE document by doc_id. "
            "Do NOT use to extract fields or check facts. "
            "Example: 'Summarize DOC-12 in 100 words'."
        ),
    },
    {
        "name": "verify_claim_against_source",
        "description": (
            "Checks one factual claim against the text of ONE source document. "
            "Returns supported, contradicted, or not_found. "
            "Example: 'Does DOC-12 say revenue grew 8%?'."
        ),
    },
]

MOCK_CUSTOMER_DB: Dict[str, Dict[str, str]] = {
    "alice@example.com": {"customer_id": "CUST-101", "name": "Alice Smith", "tier": "Gold"},
    "cust-101": {"customer_id": "CUST-101", "name": "Alice Smith", "tier": "Gold"},
}

MOCK_ORDER_DB: Dict[str, Dict[str, str]] = {
    "ord-9821": {
        "order_id": "ORD-9821",
        "status": "Shipped",
        "carrier": "FedEx",
        "tracking": "12345678",
    },
}


def description_overlap(tool_a: Dict[str, Any], tool_b: Dict[str, Any]) -> float:
    """Return Jaccard word overlap (0..1) of two tool descriptions; high means misrouting risk."""
    words_a = set(str(tool_a.get("description", "")).lower().split())
    words_b = set(str(tool_b.get("description", "")).lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def audit_tool(tool: Dict[str, Any]) -> List[str]:
    """Return the quality problems of one tool definition (empty list means it passes)."""
    problems: List[str] = []
    description = str(tool.get("description", ""))
    lowered = description.lower()
    if len(description) < 80:
        problems.append("description too short to state purpose and edge cases")
    if "do not" not in lowered and "boundary" not in lowered:
        problems.append("missing boundary ('Do NOT use for ...; use <other_tool>')")
    if "example" not in lowered:
        problems.append("missing example queries")
    properties = tool.get("input_schema", {}).get("properties", {})
    for prop_name, prop in properties.items():
        if not prop.get("description"):
            problems.append(f"parameter '{prop_name}' has no format description")
    return problems


def get_customer_tool(identifier: str) -> Dict[str, Any]:
    """Look up a customer; an unknown identifier is a valid empty result, not an error."""
    norm = identifier.lower().strip()
    if norm in MOCK_CUSTOMER_DB:
        return {"found": True, "customer": MOCK_CUSTOMER_DB[norm]}
    return {"found": False, "message": f"Customer '{identifier}' not found."}


def lookup_order_tool(order_id: str) -> Dict[str, Any]:
    """Look up an order; an unknown order ID is a valid empty result, not an error."""
    norm = order_id.lower().strip()
    if norm in MOCK_ORDER_DB:
        return {"found": True, "order": MOCK_ORDER_DB[norm]}
    return {"found": False, "message": f"Order '{order_id}' not found."}


def dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Route a tool_use block to its implementation."""
    if name == "get_customer":
        return get_customer_tool(args.get("identifier", ""))
    if name == "lookup_order":
        return lookup_order_tool(args.get("order_id", ""))
    return {"error": f"Unknown tool: {name}"}


def _text_of(response: Any) -> str:
    """Join the text blocks of a response."""
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")


def run_bounded_tool_agent(
    prompt: str,
    client: Any,
    trail: ResponseTrail,
    force_customer_first: bool = False,
    max_iterations: int = MAX_ITERATIONS,
    model: str = COORDINATOR_MODEL,
) -> str:
    """Run a tool loop driven by stop_reason; optionally force get_customer on iteration 1.

    The forced tool_choice is legal here because no `thinking` is sent. Returns the final
    text, or "" when the safety cap, a refusal or an unknown stop_reason ends the loop.
    """
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, model)
    messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]
    parser = create_parser()

    for iteration in range(1, max_iterations + 1):
        trail.api_request(session_id, iteration, messages)

        tool_choice: Any = {"type": "auto"}
        if iteration == 1 and force_customer_first:
            tool_choice = {"type": "tool", "name": "get_customer"}

        response = client.messages.create(
            model=model,
            max_tokens=800,
            tools=TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )

        parse_result = parser.parse(response.model_dump())
        parsed = parse_result.get("data") if parse_result.get("success") else None
        stop_reason: Optional[str] = parsed.stop_reason if parsed else response.stop_reason

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results: List[Dict[str, Any]] = []
            for block in response.content:
                if getattr(block, "type", "") == "tool_use":
                    trail.tool_call(session_id, iteration, block.name, block.id, block.input)
                    result = dispatch_tool(block.name, block.input)
                    trail.tool_result(session_id, iteration, block.name, block.id, result)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
        elif stop_reason == "end_turn":
            text = _text_of(response)
            trail.session_end(session_id, text, "end_turn")
            return text
        elif stop_reason == "pause_turn":
            # Server-side tool turn paused: send the assistant content back to continue.
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
        print("Set ANTHROPIC_API_KEY to run manually.")
        return
    client = anthropic.Anthropic(api_key=api_key)
    trail = ResponseTrail(path=get_agent_trail_path(__file__))
    print(run_bounded_tool_agent("Check tracking for order ORD-9821", client, trail))


if __name__ == "__main__":
    main()
