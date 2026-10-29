"""
Domain 5: Context Management & Reliability
Task Statement 5.2: Design effective escalation and ambiguity resolution patterns
Exam Scenario 1: Customer Support Resolution Agent

Key Exam Concepts Demonstrated (all offline, no API calls):
1. Escalate immediately when the customer explicitly asks for a human (no investigation first).
2. Escalate on policy gaps/exceptions (e.g. competitor price matching when policy only covers
   our own site) and when the agent cannot make progress.
3. Frustration alone is not an escalation: acknowledge it and offer a resolution if the issue
   is within the agent's capability.
4. Multiple customer matches -> ask for more identifiers; never pick heuristically.
5. Sentiment and self-reported confidence are unreliable escalation proxies. Use explicit
   escalation criteria with few-shot examples instead.

Cross-reference: the provenance/conflicting-statistics helpers at the bottom belong to TS 5.6
(see domain5/ts_5_6_provenance_and_uncertainty). They stay here only for backward compatibility.
"""

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence

HUMAN_REQUEST_PHRASES = (
    "talk to a human",
    "speak to a human",
    "speak to a person",
    "speak with a person",
    "human agent",
    "real person",
    "representative",
    "supervisor",
    "manager",
)
FRUSTRATION_PHRASES = (
    "frustrated",
    "frustrating",
    "annoyed",
    "angry",
    "ridiculous",
    "fed up",
    "unacceptable",
)

# ==============================================================================
# 1. Ambiguity & Escalation Router (TS 5.2)
# ==============================================================================


@dataclass
class EscalationDecision:
    """Outcome of the escalation rules."""

    escalate: bool
    reason: str
    target: str  # "human_supervisor" | "autonomous_resolution" | "user_clarification"
    clarification_prompt: Optional[str] = None
    acknowledge_frustration: bool = False


def evaluate_escalation_rules(
    user_message: str,
    matching_accounts_count: int,
    policy_has_rule: bool,
    within_capability: bool = True,
) -> EscalationDecision:
    """
    Apply explicit escalation criteria in priority order.

    Args:
        user_message: Latest customer message.
        matching_accounts_count: How many customer records the lookup returned.
        policy_has_rule: False when policy is silent on the request (a policy gap).
        within_capability: False when the agent cannot make progress with its tools.
    """
    lower_msg = user_message.lower()

    # Rule 1: explicit human request -> escalate now, do not investigate first.
    if any(phrase in lower_msg for phrase in HUMAN_REQUEST_PHRASES):
        return EscalationDecision(
            escalate=True,
            reason="Explicit customer demand for human agent.",
            target="human_supervisor",
        )

    # Rule 2: multiple matches -> ask for more identifiers, never guess.
    if matching_accounts_count > 1:
        return EscalationDecision(
            escalate=False,
            reason="Multiple matching accounts found. Must clarify unique identifier.",
            target="user_clarification",
            clarification_prompt=(
                "Multiple accounts match your name. "
                "Could you please provide your email or order ID?"
            ),
        )

    # Rule 3: policy gap or exception -> escalate, never invent policy.
    if not policy_has_rule:
        return EscalationDecision(
            escalate=True,
            reason="Policy gap: company policy is silent on this specific request.",
            target="human_supervisor",
        )

    # Rule 4: no meaningful progress possible -> escalate.
    if not within_capability:
        return EscalationDecision(
            escalate=True,
            reason="Unable to make progress with available tools.",
            target="human_supervisor",
        )

    # Rule 5: frustration alone -> acknowledge and resolve; a later explicit request escalates.
    frustrated = any(phrase in lower_msg for phrase in FRUSTRATION_PHRASES)
    return EscalationDecision(
        escalate=False,
        reason=(
            "Customer is frustrated but the issue is within capability: acknowledge and resolve."
            if frustrated
            else "Within policy bounds and clear identity match."
        ),
        target="autonomous_resolution",
        acknowledge_frustration=frustrated,
    )


def resolve_customer(
    matches: Sequence[Dict[str, str]], identifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolve a customer lookup without heuristics.

    One match -> return it. Several matches -> ask for an identifier; use it only to narrow the
    list, and ask again if it still does not give exactly one record.
    """
    candidates = list(matches)
    if identifier:
        needle = identifier.strip().lower()
        candidates = [m for m in candidates if needle in {v.lower() for v in m.values()}]
    if len(candidates) == 1:
        return {"status": "resolved", "customer": candidates[0]}
    if not candidates:
        return {"status": "not_found", "prompt": "No account matches. Please re-check details."}
    return {
        "status": "needs_identifier",
        "prompt": "I found several accounts. Please share your account number or email.",
    }


ESCALATION_FEW_SHOT_EXAMPLES: List[Dict[str, str]] = [
    {
        "customer": "I want to speak to a real person now.",
        "decision": "ESCALATE_NOW",
        "why": "Explicit human request. Do not investigate or ask questions first.",
    },
    {
        "customer": "My parcel arrived broken. Can you send a replacement?",
        "decision": "RESOLVE",
        "why": "Standard damage replacement is within policy and tools. Do not escalate.",
    },
    {
        "customer": "Another shop sells this cheaper. Match their price.",
        "decision": "ESCALATE_POLICY_GAP",
        "why": "Policy covers our own site only; competitor matching is not addressed.",
    },
    {
        "customer": "This is so frustrating, my refund is late!",
        "decision": "ACKNOWLEDGE_AND_RESOLVE",
        "why": "Frustration alone is not a trigger. Offer the refund status fix first.",
    },
    {
        "customer": "Please find my order. I'm John Lee.",
        "decision": "ASK_FOR_IDENTIFIER",
        "why": "Lookup returned 3 customers. Ask for email or order ID; never pick one.",
    },
]


def build_escalation_prompt() -> str:
    """Render explicit escalation criteria plus few-shot examples for the system prompt."""
    lines = [
        "ESCALATION CRITERIA (apply in order):",
        "1. Customer explicitly asks for a human -> escalate immediately.",
        "2. Policy is silent or an exception is requested -> escalate.",
        "3. You cannot make progress -> escalate.",
        "4. Frustration only -> acknowledge, offer a fix, escalate only if they ask for a human.",
        "5. Several customer matches -> ask for an identifier; never guess.",
        "Do NOT use sentiment or your own confidence score to decide.",
        "",
        "EXAMPLES:",
    ]
    for ex in ESCALATION_FEW_SHOT_EXAMPLES:
        lines.append(f'- Customer: "{ex["customer"]}" -> {ex["decision"]} ({ex["why"]})')
    return "\n".join(lines)


# ==============================================================================
# 2. Backward-compatible provenance helpers (canonical home: TS 5.6)
# ==============================================================================


@dataclass
class SourceClaim:
    claim: str
    statistic_value: str
    source_name: str
    collection_date: str
    methodology: str


def synthesize_conflicting_sources(claims: List[SourceClaim]) -> Dict[str, Any]:
    """Keep contradictory statistics with attribution and dates (see TS 5.6 for the full model)."""
    has_conflict = len(set(c.statistic_value for c in claims)) > 1
    attributed = "; ".join(
        f"{c.source_name} ({c.collection_date}) reported {c.statistic_value}" for c in claims
    )
    return {
        "status": "synthesized",
        "has_contested_findings": has_conflict,
        "claims_with_provenance": [asdict(c) for c in claims],
        "synthesis_summary": (
            f"Findings contested across reputable sources: {attributed}"
            if has_conflict
            else "Consensus findings verified across sources."
        ),
    }


def main() -> None:
    """Offline demo of the escalation rules."""
    cases = [
        ("Let me speak to a person right now", 1, True),
        ("This is frustrating, my refund is late", 1, True),
        ("Check my balance", 2, True),
        ("Can you price-match a competitor?", 1, False),
    ]
    for message, count, has_rule in cases:
        dec = evaluate_escalation_rules(message, count, has_rule)
        print(f"{message!r}\n  -> escalate={dec.escalate} target={dec.target} ({dec.reason})")
    print()
    print(build_escalation_prompt())
    print(json.dumps(resolve_customer([{"id": "A1"}, {"id": "A2"}], "A2"), indent=2))


if __name__ == "__main__":
    main()
