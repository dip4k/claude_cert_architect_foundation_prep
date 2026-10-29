"""
Scenario 1: Customer Support Resolution Agent
End-to-End System Simulation

Weaves Together:
- TS 1.4: Multi-Step Workflows & Prerequisite Gates
- TS 2.1: Tool Interface Design & Boundaries
- TS 2.2: MCP Structured Error Responses
- TS 5.1: Context Window Preservation & Case Facts
- TS 5.2: Immediate Escalation Triggers & Human Handoff Protocols

Offline only: no anthropic import, no network. Tool names match the official scenario:
get_customer, lookup_order, process_refund, escalate_to_human.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class CaseFacts:
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    is_authenticated: bool = False
    verified_phone: Optional[str] = None
    active_order_id: Optional[str] = None


@dataclass
class EscalationPayload:
    reason: str
    case_facts: Dict[str, Any]
    summary_of_interaction: str
    recommended_tier_2_action: str
    escalation_type: str = "POLICY_GAP"
    actions_taken: List[str] = field(default_factory=list)


REFUND_APPROVAL_LIMIT_USD = 500.0  # Refunds above this need a human; enforced in code, not prompt
RETURN_WINDOW_DAYS = 30
GATED_TOOLS = {"lookup_order": "get_customer", "process_refund": "get_customer"}
POLICY_GAP_PHRASES = ["price match", "price-match", "competitor price"]


class CustomerSupportPipeline:
    """Production customer support agent with deterministic gates and immediate escalation."""

    MOCK_CUSTOMERS = {
        "alice@example.com": {"id": "cust_101", "name": "Alice Smith", "phone": "555-0101", "vip": True},
        "bob@example.com": {"id": "cust_102", "name": "Bob Jones", "phone": "555-0102", "vip": False},
        "alex1@example.com": {"id": "cust_201", "name": "Alex Kim", "phone": "555-0201", "vip": False},
        "alex2@example.com": {"id": "cust_202", "name": "Alex Kim", "phone": "555-0202", "vip": False},
    }

    MOCK_ORDERS = {
        "ord_9901": {
            "id": "ord_9901",
            "customer_id": "cust_101",
            "status": "DELIVERED",
            "days_since_delivery": 12,
            "total_usd": 79.99,
            "items": ["Wireless Headphones"],
            # Internal bloated fields that must be trimmed:
            "_internal_warehouse_id": "WH-EAST-4",
            "_db_partition_key": "part_0982",
            "_carrier_internal_audit_log": ["scan_1", "scan_2", "scan_3", "scan_4"],
            "_staff_packer_employee_id": "EMP_8812"
        },
        "ord_9902": {
            "id": "ord_9902",
            "customer_id": "cust_101",
            "status": "DELIVERED",
            "days_since_delivery": 45,  # Exceeds 30d return window!
            "total_usd": 150.00,
            "items": ["Ergonomic Chair"],
            "_internal_warehouse_id": "WH-WEST-1"
        },
        "ord_9903": {
            "id": "ord_9903",
            "customer_id": "cust_102",
            "status": "DELIVERED",
            "days_since_delivery": 5,
            "total_usd": 750.00,  # Above REFUND_APPROVAL_LIMIT_USD
            "items": ["Standing Desk"],
            "_internal_warehouse_id": "WH-EAST-2"
        }
    }

    def __init__(self) -> None:
        self.case_facts = CaseFacts()
        self.conversation_history: List[Dict[str, str]] = []
        self.escalated: bool = False
        self.escalation_data: Optional[EscalationPayload] = None
        self.actions_taken: List[str] = []

    def execute_tool(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Dispatch a tool call; the prerequisite gate runs in code before any handler.

        Returns a structured MCP-style error (isError/errorCategory/isRetryable) when blocked.
        """
        required = GATED_TOOLS.get(tool_name)
        if required and not self.case_facts.is_authenticated:
            return {
                "isError": True,
                "errorCategory": "permission",
                "isRetryable": False,
                "message": f"{tool_name} blocked: call {required} and verify identity first.",
            }
        handlers = {
            "get_customer": self._tool_get_customer,
            "lookup_order": self._tool_lookup_order,
            "process_refund": self._tool_process_refund,
        }
        if tool_name not in handlers:
            return {
                "isError": True,
                "errorCategory": "validation",
                "isRetryable": False,
                "message": f"Unknown tool: {tool_name}",
            }
        return handlers[tool_name](**kwargs)

    def resolve_customer_by_name(
        self, name: str, disambiguator: Optional[str] = None
    ) -> Dict[str, Any]:
        """Name search: on multiple matches ask for an identifier; never guess by recency."""
        matches = [
            (email, rec)
            for email, rec in self.MOCK_CUSTOMERS.items()
            if rec["name"].lower() == name.strip().lower()
        ]
        if not matches:
            return {"agent_reply": "No account found for that name.", "action_taken": "AUTH_FAILED"}
        if len(matches) > 1:
            narrowed = [m for m in matches if disambiguator and disambiguator == m[1]["phone"]]
            if len(narrowed) != 1:
                return {
                    "agent_reply": "I found more than one account. Please share the phone number "
                    "or email on the account.",
                    "action_taken": "ASK_DISAMBIGUATING_IDENTIFIER",
                    "candidate_count": len(matches),
                }
            matches = narrowed
        return self._tool_get_customer(matches[0][0])

    def process_customer_turn(self, user_utterance: str) -> Dict[str, Any]:
        """Processes a dialogue turn with escalation checks, gates, and tool routing."""
        self.conversation_history.append({"role": "user", "content": user_utterance})

        # Decision Point 1: Immediate Escalation Trigger
        human_triggers = ["talk to a human", "speak to a human", "speak to a person", "speak to a manager", "real person", "customer representative", "human"]
        if any(trig in user_utterance.lower() for trig in human_triggers):
            return self._trigger_immediate_escalation(
                reason="Customer explicit demand for human agent",
                user_utterance=user_utterance,
                escalation_type="EXPLICIT_REQUEST",
            )

        # Decision Point 1b: Policy gap (request the written policy does not cover)
        if any(p in user_utterance.lower() for p in POLICY_GAP_PHRASES):
            return self._trigger_immediate_escalation(
                reason="Policy gap: request not covered by written policy (price matching)",
                user_utterance=user_utterance,
                escalation_type="POLICY_GAP",
            )

        # Decision Point 2: Identity Verification & Disambiguation
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", user_utterance)
        if email_match and not self.case_facts.is_authenticated:
            email = email_match.group(0).lower()
            return self._tool_get_customer(email)

        # Decision Point 3: Refund Request (can contain order_id explicitly)
        order_match = re.search(r"ord_\d+", user_utterance.lower())
        if "refund" in user_utterance.lower():
            target_order = order_match.group(0) if order_match else self.case_facts.active_order_id
            if not target_order:
                return {
                    "agent_reply": "I'd be glad to check your refund options. Please provide your order number (e.g., ord_9901).",
                    "action_taken": "PROMPT_ORDER_ID"
                }
            return self._tool_process_refund(target_order)

        # Decision Point 4: Order Lookup (requires auth)
        if order_match:
            order_id = order_match.group(0)
            return self._tool_lookup_order(order_id)

        return {
            "agent_reply": "How can I assist you with your orders or account today?",
            "action_taken": "GENERAL_PROMPT"
        }

    def _tool_get_customer(self, email: str) -> Dict[str, Any]:
        """MCP Tool: get_customer with authentication enforcement."""
        self.actions_taken.append("get_customer")
        if email not in self.MOCK_CUSTOMERS:
            return {
                "agent_reply": f"I couldn't find an account for {email}. Could you double-check your email address?",
                "action_taken": "AUTH_FAILED"
            }
        
        record = self.MOCK_CUSTOMERS[email]
        # Update immutable Case Facts
        self.case_facts.customer_id = record["id"]
        self.case_facts.customer_name = record["name"]
        self.case_facts.verified_phone = record["phone"]
        self.case_facts.is_authenticated = True

        return {
            "agent_reply": f"Thank you {record['name']}, your identity is verified. How can I assist you with your orders?",
            "action_taken": "AUTH_SUCCESS",
            "customer_id": record["id"]
        }

    def _tool_lookup_order(self, order_id: str) -> Dict[str, Any]:
        """MCP Tool: lookup_order with programmatic auth gate and context trimming."""
        self.actions_taken.append("lookup_order")
        # Gate check: Must be authenticated
        if not self.case_facts.is_authenticated:
            return {
                "agent_reply": "Before I can look up that order, please provide your account email for verification.",
                "action_taken": "GATE_BLOCKED_UNAUTHENTICATED"
            }

        if order_id not in self.MOCK_ORDERS:
            return {
                "agent_reply": f"Order {order_id} was not found. Please verify the order number.",
                "action_taken": "ORDER_NOT_FOUND"
            }

        raw_order = self.MOCK_ORDERS[order_id]
        if raw_order["customer_id"] != self.case_facts.customer_id:
            return {
                "agent_reply": "That order does not belong to your verified account.",
                "action_taken": "SECURITY_VIOLATION_BLOCKED"
            }

        # Context Trimming: Strip out the 4 internal warehouse/audit fields!
        trimmed_order = {
            "order_id": raw_order["id"],
            "status": raw_order["status"],
            "total_usd": raw_order["total_usd"],
            "items": raw_order["items"],
            "days_since_delivery": raw_order["days_since_delivery"]
        }
        self.case_facts.active_order_id = order_id

        return {
            "agent_reply": f"Found order {order_id}: {trimmed_order['items'][0]} for ${trimmed_order['total_usd']:.2f} (Status: {trimmed_order['status']}).",
            "action_taken": "ORDER_FOUND_TRIMMED",
            "order_data": trimmed_order
        }

    def _tool_process_refund(self, order_id: str) -> Dict[str, Any]:
        """MCP Tool: process_refund with policy boundary checks."""
        self.actions_taken.append("process_refund")
        if not self.case_facts.is_authenticated:
            return {
                "agent_reply": "Authentication required before initiating refunds.",
                "action_taken": "GATE_BLOCKED_UNAUTHENTICATED"
            }

        order = self.MOCK_ORDERS.get(order_id)
        if not order:
            return {"agent_reply": "Order not found.", "action_taken": "NOT_FOUND"}

        # Policy Rule: Max 30 days return window
        if order["days_since_delivery"] > RETURN_WINDOW_DAYS:
            return self._trigger_immediate_escalation(
                reason=f"Policy exception: Order {order_id} delivered {order['days_since_delivery']} days ago (Policy max: 30 days)",
                user_utterance="Customer requested refund outside return window"
            )

        # Threshold hook: refunds above the limit are blocked in code and routed to a human
        if order["total_usd"] > REFUND_APPROVAL_LIMIT_USD:
            return self._trigger_immediate_escalation(
                reason=(
                    f"Refund threshold: ${order['total_usd']:.2f} exceeds the "
                    f"${REFUND_APPROVAL_LIMIT_USD:.0f} limit"
                ),
                user_utterance="Customer requested a high-value refund",
                escalation_type="THRESHOLD",
            )

        return {
            "agent_reply": f"Refund of ${order['total_usd']:.2f} for order {order_id} has been approved and issued to your original payment method.",
            "action_taken": "REFUND_SUCCESS",
            "amount_refunded": order["total_usd"]
        }

    def _trigger_immediate_escalation(
        self, reason: str, user_utterance: str, escalation_type: str = "POLICY_GAP"
    ) -> Dict[str, Any]:
        """Executes the immediate escalation contract (escalate_to_human) without probing."""
        self.escalated = True
        self.escalation_data = EscalationPayload(
            reason=reason,
            case_facts=dict(self.case_facts.__dict__),
            summary_of_interaction=f"Customer last stated: '{user_utterance}'",
            recommended_tier_2_action="Review policy exception or assist with specialized inquiry.",
            escalation_type=escalation_type,
            actions_taken=list(self.actions_taken),
        )

        return {
            "agent_reply": "I am transferring you immediately to a specialist with your verified account details.",
            "action_taken": "ESCALATED_TO_HUMAN",
            "escalation_payload": self.escalation_data.__dict__
        }


def main() -> None:
    print("=" * 70)
    print("Scenario 1: Customer Support Resolution Agent Simulation")
    print("=" * 70)

    pipeline = CustomerSupportPipeline()

    # Step 1: Unauthenticated request for refund (Gate triggers!)
    t1 = pipeline.process_customer_turn("Hi, I want a refund on ord_9901")
    print("\nTurn 1 (Attempt unauthenticated access):")
    print(f"Reply: {t1['agent_reply']}")
    print(f"Gate Action: {t1['action_taken']}")

    # Step 2: Customer provides email
    t2 = pipeline.process_customer_turn("My email is alice@example.com")
    print("\nTurn 2 (Authenticate):")
    print(f"Reply: {t2['agent_reply']}")
    print(f"Auth State: {pipeline.case_facts.is_authenticated} (CustID: {pipeline.case_facts.customer_id})")

    # Step 3: Lookup order (Trimmed context)
    t3 = pipeline.process_customer_turn("Okay, check ord_9901 now")
    print("\nTurn 3 (Lookup order):")
    print(f"Reply: {t3['agent_reply']}")
    print(f"Trimmed Order Payload: {t3['order_data']}")

    # Step 4: Refund processed within 30 days
    t4 = pipeline.process_customer_turn("Please issue the refund.")
    print("\nTurn 4 (Process refund within policy):")
    print(f"Reply: {t4['agent_reply']}")
    print(f"Outcome: {t4['action_taken']}")

    # Step 5: Immediate Escalation on user demand
    t5 = pipeline.process_customer_turn("Actually, let me speak to a manager right now!")
    print("\nTurn 5 (Human demand escalation contract):")
    print(f"Reply: {t5['agent_reply']}")
    print(f"Escalation Payload Sent: {json.dumps(t5['escalation_payload'], indent=2)}")


if __name__ == "__main__":
    main()
