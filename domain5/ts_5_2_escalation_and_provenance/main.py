"""
Domain 5: Context Management & Reliability
Task Statement 5.2: Design effective escalation and ambiguity resolution patterns
Task Statement 5.6: Preserve information provenance and handle uncertainty in multi-source synthesis
Exam Scenario 1 & 3: Customer Support & Multi-Agent Research System

Key Exam Concepts Demonstrated:
1. Escalation Decision Logic:
   - Immediate escalation upon explicit user human request.
   - Escalating on policy gaps/uncovered situations.
   - Ambiguity resolution: Prompting user for clarification when lookups return multiple hits.
2. Multi-Source Synthesis Provenance:
   - Preserving structured claim-source mappings with collection dates.
   - Preserving conflicting statistics with source attribution rather than arbitrarily picking one.
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# ==============================================================================
# 1. Ambiguity & Escalation Router (TS 5.2)
# ==============================================================================

@dataclass
class EscalationDecision:
    escalate: bool
    reason: str
    target: str  # "human_supervisor" | "autonomous_resolution" | "user_clarification"
    clarification_prompt: Optional[str] = None


def evaluate_escalation_rules(
    user_message: str,
    matching_accounts_count: int,
    policy_has_rule: bool,
) -> EscalationDecision:
    """Evaluates explicit customer demand, ties, and policy gaps."""
    lower_msg = user_message.lower()

    # Rule 1: Immediate human escalation on explicit request
    if any(phrase in lower_msg for phrase in ["talk to a human", "speak to a person", "human agent", "representative"]):
        return EscalationDecision(
            escalate=True,
            reason="Explicit customer demand for human agent.",
            target="human_supervisor",
        )

    # Rule 2: Ambiguity resolution on multiple matches (Clarify, never guess!)
    if matching_accounts_count > 1:
        return EscalationDecision(
            escalate=False,
            reason="Multiple matching accounts found. Must clarify unique identifier.",
            target="user_clarification",
            clarification_prompt="Multiple accounts match your name. Could you please provide your email or order ID?",
        )

    # Rule 3: Policy gap (policy silent on customer request)
    if not policy_has_rule:
        return EscalationDecision(
            escalate=True,
            reason="Policy gap: company policy is silent on this specific request.",
            target="human_supervisor",
        )

    return EscalationDecision(
        escalate=False,
        reason="Within policy bounds and clear identity match.",
        target="autonomous_resolution",
    )


# ==============================================================================
# 2. Synthesis Provenance & Conflicting Statistics Engine (TS 5.6)
# ==============================================================================

@dataclass
class SourceClaim:
    claim: str
    statistic_value: str
    source_name: str
    collection_date: str
    methodology: str


def synthesize_conflicting_sources(claims: List[SourceClaim]) -> Dict[str, Any]:
    """
    Synthesizes multi-source data without discarding contradictory statistics.
    Annotates uncertainty with source attribution and collection timestamps.
    """
    has_conflict = len(set(c.statistic_value for c in claims)) > 1

    return {
        "status": "synthesized",
        "has_contested_findings": has_conflict,
        "claims_with_provenance": [asdict(c) for c in claims],
        "synthesis_summary": (
            "Findings contested across reputable sources: "
            + "; ".join(f"{c.source_name} ({c.collection_date}) reported {c.statistic_value}" for c in claims)
            if has_conflict
            else "Consensus findings verified across sources."
        ),
    }


def main() -> None:
    print("Testing Escalation Logic:")
    dec1 = evaluate_escalation_rules("Let me speak to a person right now", 1, True)
    print(f"Human Demand: Escalate={dec1.escalate}, Target={dec1.target}")

    dec2 = evaluate_escalation_rules("Check my balance", 2, True)
    print(f"Ambiguity Tie: Target={dec2.target}, Prompt={dec2.clarification_prompt}\n")

    print("Testing Conflicting Source Synthesis:")
    claims = [
        SourceClaim("Cloud Market Size", "$4.2B", "Reuters", "2026-08-15", "Enterprise Survey"),
        SourceClaim("Cloud Market Size", "$3.8B", "Bloomberg", "2026-09-01", "SEC Filings"),
    ]
    synth = synthesize_conflicting_sources(claims)
    print(json.dumps(synth, indent=2))


if __name__ == "__main__":
    main()
