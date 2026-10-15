"""
Domain 5: Context Management & Reliability
Task Statement 5.1: Manage conversation context to preserve critical information across long interactions
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated:
1. Risks of progressive summarization: condensing loses specific numerical values, dates,
   order numbers, and customer-stated expectations.
2. The "Case Facts" pattern: extracting and maintaining transactional facts (order IDs, amounts,
   statuses) in a persistent context layer outside summarized conversation history.
3. Trimming verbose tool outputs to only relevant fields before they accumulate in context
   (e.g., stripping 40+ warehouse/internal database fields down to the 4 needed for returns).
4. Mitigating the "lost in the middle" effect by positioning critical state at the top of prompts.

Manual Execution (WSL Ubuntu):
    uv run domain5/ts_5_1_context_preservation/main.py
"""

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path

load_dotenv()


# ==============================================================================
# 1. Persistent Case Facts Layer
# ==============================================================================

@dataclass
class CaseFacts:
    """
    Persistent transactional facts preserved outside conversation history.
    Prevents information degradation and loss across progressive summarization.
    """
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    order_id: Optional[str] = None
    order_amount: Optional[float] = None
    order_date: Optional[str] = None
    return_eligible: Optional[bool] = None
    refund_requested: Optional[float] = None
    escalation_reason: Optional[str] = None
    custom_notes: List[str] = field(default_factory=list)

    def render_prompt_block(self) -> str:
        """Renders case facts block to be injected at the top of the prompt."""
        lines = [
            "### PERSISTENT CASE FACTS (IMMUTABLE GROUND TRUTH)",
            f"- Customer ID: {self.customer_id or 'Pending'}",
            f"- Email: {self.customer_email or 'Pending'}",
            f"- Order ID: {self.order_id or 'Pending'}",
            f"- Order Total: ${self.order_amount:.2f}" if self.order_amount else "- Order Total: Pending",
            f"- Order Date: {self.order_date or 'Pending'}",
            f"- Return Eligible: {self.return_eligible if self.return_eligible is not None else 'Pending'}",
        ]
        if self.custom_notes:
            lines.append("- Critical Notes:")
            for note in self.custom_notes:
                lines.append(f"  * {note}")
        return "\n".join(lines)


# ==============================================================================
# 2. Tool Trimming Engine (Reducing Context Token Bloat)
# ==============================================================================

RAW_ORDER_PAYLOAD = {
    "order_id": "ORD-2026-9921",
    "customer_id": "CUST-441",
    "order_date": "2026-09-28",
    "amount": 149.99,
    "currency": "USD",
    "status": "delivered",
    "return_eligible": True,
    # 25+ internal fields that waste tokens and dilute context window attention:
    "warehouse_rack_id": "WH-RACK-092-B",
    "carrier_tracking_code": "1Z9999999999999999",
    "carrier_internal_hub_id": "HUB-ORD-IL-01",
    "erp_sync_timestamp": 1727500000,
    "payment_gateway_auth_token": "tok_live_secret_masked",
    "shipping_dimension_cubic_inches": 142.5,
    "package_tare_weight_grams": 450,
    "legacy_billing_subsystem_account": "ACC_OLD_441",
    "audit_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}


def trim_order_output(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trims verbose backend tool payload to only decision-relevant fields.
    Mitigates token consumption and protects attention quality.
    """
    return {
        "order_id": raw_data["order_id"],
        "customer_id": raw_data["customer_id"],
        "amount": raw_data["amount"],
        "order_date": raw_data["order_date"],
        "return_eligible": raw_data["return_eligible"],
    }


def lookup_order_tool(order_id: str, case_facts: CaseFacts) -> Dict[str, Any]:
    """Tool that looks up order and updates persistent CaseFacts."""
    if order_id == RAW_ORDER_PAYLOAD["order_id"]:
        trimmed = trim_order_output(RAW_ORDER_PAYLOAD)
        case_facts.order_id = trimmed["order_id"]
        case_facts.customer_id = trimmed["customer_id"]
        case_facts.order_amount = trimmed["amount"]
        case_facts.order_date = trimmed["order_date"]
        case_facts.return_eligible = trimmed["return_eligible"]
        return trimmed
    return {"found": False, "error": f"Order {order_id} not found."}


TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up order details and return eligibility by Order ID.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    }
]


# ==============================================================================
# 3. Prompt Construction with Case Facts
# ==============================================================================

def build_system_prompt_with_facts(case_facts: CaseFacts) -> str:
    return f"""You are an empathetic, precise Customer Support Resolution Agent.

{case_facts.render_prompt_block()}

Instructions:
1. Always base resolution upon the immutable case facts above.
2. If order return is eligible, offer standard refund or exchange.
3. Keep answers concise and direct.
"""


def main() -> None:
    facts = CaseFacts(
        customer_id="CUST-441",
        customer_email="customer@example.com",
    )
    print("Initial Persistent Case Facts Layer:")
    print(facts.render_prompt_block())

    print("\nSimulating order lookup tool call with output trimming...")
    trimmed_result = lookup_order_tool("ORD-2026-9921", facts)
    print("Trimmed Result returned to model:")
    print(json.dumps(trimmed_result, indent=2))

    print("\nUpdated Persistent Case Facts Layer (Notice preserved details):")
    print(facts.render_prompt_block())


if __name__ == "__main__":
    main()
