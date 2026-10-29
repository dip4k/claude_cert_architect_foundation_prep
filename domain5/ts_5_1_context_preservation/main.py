"""
Domain 5: Context Management & Reliability
Task Statement 5.1: Manage conversation context to preserve critical information across long
interactions.
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated (all offline, no API calls):
1. Progressive summarisation loses numbers, dates and expectations -> keep a "case facts" block
   outside the summarised history and re-inject it on every turn.
2. Tool results accumulate. Trim 40+ raw fields to the few that matter BEFORE they enter context.
3. "Lost in the middle": put case facts at the start and the latest turns at the end; use section
   headers and put key findings first when aggregating inputs.
4. Subagents return structured data (key facts, citations, relevance scores, dates), not
   verbose reasoning.
5. Pass the complete conversation history on each request; the case facts block supplements it.

Manual Execution (WSL Ubuntu):
    uv run domain5/ts_5_1_context_preservation/main.py   (offline demo, no API calls)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

# ==============================================================================
# 1. Persistent Case Facts Layer
# ==============================================================================


@dataclass
class CaseFacts:
    """Transactional facts kept outside summarised history so summaries cannot erase them."""

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
        """Render the case facts block that is injected at the top of the prompt."""
        total = f"${self.order_amount:.2f}" if self.order_amount is not None else "Pending"
        eligible = self.return_eligible if self.return_eligible is not None else "Pending"
        lines = [
            "### PERSISTENT CASE FACTS (IMMUTABLE GROUND TRUTH)",
            f"- Customer ID: {self.customer_id or 'Pending'}",
            f"- Email: {self.customer_email or 'Pending'}",
            f"- Order ID: {self.order_id or 'Pending'}",
            f"- Order Total: {total}",
            f"- Order Date: {self.order_date or 'Pending'}",
            f"- Return Eligible: {eligible}",
        ]
        if self.refund_requested is not None:
            lines.append(f"- Refund Requested: ${self.refund_requested:.2f}")
        if self.custom_notes:
            lines.append("- Critical Notes (customer-stated expectations, dates):")
            lines.extend(f"  * {note}" for note in self.custom_notes)
        return "\n".join(lines)


ORDER_ID_PATTERN = re.compile(r"\bORD-[A-Z0-9-]+\b")
AMOUNT_PATTERN = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)")
DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def extract_case_facts(message: str, facts: CaseFacts) -> CaseFacts:
    """
    Deterministically copy order IDs, amounts and dates from a customer message into the facts.

    Existing values are never overwritten by a vaguer later mention; a changed value is recorded
    as a note so the conflict stays visible instead of silently replacing the ground truth.
    """
    order = ORDER_ID_PATTERN.search(message)
    if order:
        if facts.order_id is None:
            facts.order_id = order.group(0)
        elif facts.order_id != order.group(0):
            facts.custom_notes.append(f"Customer also mentioned order {order.group(0)}")
    amount = AMOUNT_PATTERN.search(message)
    if amount:
        value = float(amount.group(1).replace(",", ""))
        if facts.refund_requested is None:
            facts.refund_requested = value
        elif facts.refund_requested != value:
            facts.custom_notes.append(f"Customer later stated amount ${value:.2f}")
    date = DATE_PATTERN.search(message)
    if date and facts.order_date is None:
        facts.order_date = date.group(1)
    return facts


# ==============================================================================
# 2. Progressive Summarisation Drift (what the case facts block protects against)
# ==============================================================================


def lossy_summary(text: str) -> str:
    """
    Offline stand-in for an LLM summary: keeps the topic, drops IDs, amounts and dates.

    This is the failure mode the exam describes; it is intentionally lossy.
    """
    stripped = ORDER_ID_PATTERN.sub("an order", text)
    stripped = AMOUNT_PATTERN.sub("some amount", stripped)
    return DATE_PATTERN.sub("recently", stripped)


def facts_survive(prompt: str, facts: CaseFacts) -> bool:
    """Return True if every populated transactional fact still appears verbatim in the prompt."""
    expected: List[str] = []
    if facts.order_id:
        expected.append(facts.order_id)
    if facts.order_amount is not None:
        expected.append(f"${facts.order_amount:.2f}")
    if facts.refund_requested is not None:
        expected.append(f"${facts.refund_requested:.2f}")
    if facts.order_date:
        expected.append(facts.order_date)
    return all(item in prompt for item in expected)


# ==============================================================================
# 3. Tool Trimming Engine (PostToolUse-style normalisation)
# ==============================================================================

RAW_ORDER_PAYLOAD: Dict[str, Any] = {
    "order_id": "ORD-2026-9921",
    "customer_id": "CUST-441",
    "order_date": "2026-09-28",
    "amount": 149.99,
    "currency": "USD",
    "status": "delivered",
    "return_eligible": True,
    # Internal fields that waste tokens and dilute attention:
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
RAW_ORDER_PAYLOAD.update({f"internal_telemetry_{i:02d}": f"v{i}" for i in range(1, 32)})

ESSENTIAL_ORDER_FIELDS: Sequence[str] = (
    "order_id",
    "customer_id",
    "amount",
    "order_date",
    "return_eligible",
)


def trim_payload(raw_data: Dict[str, Any], keep: Sequence[str]) -> Dict[str, Any]:
    """Allow-list trim: keep only the named fields that are present in the raw payload."""
    return {key: raw_data[key] for key in keep if key in raw_data}


def trim_order_output(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Trim a verbose order payload to the fields a return/refund decision needs."""
    return trim_payload(raw_data, ESSENTIAL_ORDER_FIELDS)


def approx_tokens(payload: Dict[str, Any]) -> int:
    """Rough size estimate (about 4 characters per token); for relative comparison only."""
    return max(1, len(json.dumps(payload)) // 4)


def lookup_order_tool(order_id: str, case_facts: CaseFacts) -> Dict[str, Any]:
    """Look up an order, return only the trimmed result and update the case facts."""
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
# 4. Subagent Output Contract and Aggregation Layout ("lost in the middle")
# ==============================================================================


@dataclass
class SubagentFinding:
    """Structured subagent return: facts and provenance, not a reasoning transcript."""

    claim: str
    source: str
    date: str
    relevance: float


def render_aggregated_findings(findings: Sequence[SubagentFinding], top_n: int = 3) -> str:
    """
    Lay out aggregated subagent input: key findings first, then headed detail sections.

    Models attend best to the start and end of long inputs, so the summary goes first and
    each source gets an explicit section header instead of being buried mid-stream.
    """
    ranked = sorted(findings, key=lambda f: f.relevance, reverse=True)
    lines = ["## KEY FINDINGS (highest relevance first)"]
    lines.extend(f"- {f.claim} [{f.source}, {f.date}]" for f in ranked[:top_n])
    for source in sorted({f.source for f in ranked}):
        lines.append(f"\n## DETAIL: {source}")
        lines.extend(f"- {f.claim} ({f.date}, relevance {f.relevance:.2f})" for f in ranked
                     if f.source == source)
    return "\n".join(lines)


# ==============================================================================
# 5. Prompt Construction with Case Facts
# ==============================================================================


def build_system_prompt_with_facts(case_facts: CaseFacts) -> str:
    """System prompt with the case facts block at the very top."""
    return f"""You are an empathetic, precise Customer Support Resolution Agent.

{case_facts.render_prompt_block()}

Instructions:
1. Always base resolution upon the immutable case facts above.
2. If order return is eligible, offer standard refund or exchange.
3. Keep answers concise and direct.
"""


def assemble_context(
    facts: CaseFacts,
    earlier_summary: str,
    recent_turns: Sequence[Dict[str, str]],
    user_message: str,
) -> Dict[str, Any]:
    """
    Build request pieces: facts in `system`, summary + verbatim recent turns + new user turn.

    The summary only carries narrative (tone, troubleshooting); numbers live in the facts block.
    """
    messages: List[Dict[str, str]] = []
    if earlier_summary:
        messages.append({"role": "user", "content": f"Earlier conversation: {earlier_summary}"})
        messages.append({"role": "assistant", "content": "Understood."})
    messages.extend(dict(turn) for turn in recent_turns)
    messages.append({"role": "user", "content": user_message})
    return {"system": build_system_prompt_with_facts(facts), "messages": messages}


def main() -> None:
    """Offline demo of facts, trimming and drift protection."""
    facts = CaseFacts(customer_id="CUST-441", customer_email="customer@example.com")
    first = "Refund order ORD-2026-9921, I paid $149.99 on 2026-09-28."
    extract_case_facts(first, facts)
    print(facts.render_prompt_block())

    print("\nSummary drift:", lossy_summary(first))
    summary_only = lossy_summary(first)
    print("Facts survive in summary alone:", facts_survive(summary_only, facts))
    ctx = assemble_context(facts, summary_only, [], "Where is my refund?")
    print("Facts survive with case facts block:", facts_survive(ctx["system"], facts))

    result = lookup_order_tool("ORD-2026-9921", facts)
    print(f"\nTrimmed {len(RAW_ORDER_PAYLOAD)} fields -> {len(result)}:")
    print(f"~{approx_tokens(RAW_ORDER_PAYLOAD)} tokens -> ~{approx_tokens(result)} tokens")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
