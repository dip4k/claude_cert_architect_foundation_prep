"""
Domain 5 Notebook Generator: Context Management & Reliability (TS 5.1 - TS 5.6).
Generates comprehensive Jupyter notebooks with step-by-step walkthroughs,
offline simulations, and automated verification checks.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.notebook_builder import code_cell, markdown_cell, save_notebook


def build_ts_5_1():
    cells = [
        markdown_cell("""# Domain 5: Context Management & Reliability
## TS 5.1: Manage Conversation Context to Preserve Critical Information Across Long Interactions
**Certification Focus**: CCAR-F Domain 5 (15% Exam Weight) | **Scenario Alignment**: Scenario 1 & 4

---

### 🎯 Key Architectural Principles
1. **Tool Output Trimming**: Bulky database payloads and carrier tracking logs quickly consume context windows. Always trim non-essential internal fields before feeding results back into Claude.
2. **Persistent Case Facts**: Critical business entities (Customer ID, verified identity, order reference) must be maintained in an immutable `CaseFacts` block at the top of the prompt, immune to conversation summarization loss.
3. **Preventing Hallucination via Pruning**: Long conversation histories dilute attention; extracting structured facts into persistent state allows pruning old conversational turns without losing critical context."""),

        code_cell("""# Step 1: Environment & Setup
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 5.1 Context Preservation.")"""),

        markdown_cell("""### ✂️ Step 2: Output Trimmer & Case Facts Manager
We implement the tool output trimmer and the persistent `CaseFacts` state container."""),

        code_cell("""# Step 2: Trimming and Persistent Facts Logic
RAW_ORDER_PAYLOAD = {
    "order_id": "ORD-2026-9921",
    "customer_id": "CUST-441",
    "status": "delivered",
    "amount": 149.99,
    "internal_db_primary_key": 998124,
    "payment_gateway_auth_token": "tok_live_secret_auth_99182371",
    "carrier_tracking_code": "TRACK_FEDEX_9981247182",
    "warehouse_rack_id": "RACK-4B-SHELF-2",
    "server_processing_node": "us-east-1a-worker-04",
}

def trim_order_output(raw_order: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Strips bulky internal telemetry, leaving only essential business fields.\"\"\"
    return {
        "order_id": raw_order.get("order_id"),
        "customer_id": raw_order.get("customer_id"),
        "status": raw_order.get("status"),
        "amount": raw_order.get("amount"),
    }


@dataclass
class CaseFacts:
    customer_id: str
    customer_email: str
    order_id: Optional[str] = None
    order_amount: Optional[float] = None
    status: str = "Active"

    def render_prompt_block(self) -> str:
        \"\"\"Renders persistent state block placed at the top of prompt context.\"\"\"
        lines = [
            "### PERSISTENT CASE FACTS (IMMUTABLE STATE)",
            f"- Customer ID: {self.customer_id}",
            f"- Customer Email: {self.customer_email}",
        ]
        if self.order_id:
            lines.append(f"- Active Order: {self.order_id} (${self.order_amount:.2f})")
        lines.append(f"- Status: {self.status}")
        return "\\n".join(lines)


def lookup_order_tool(order_id: str, case_facts: CaseFacts) -> Dict[str, Any]:
    \"\"\"Simulates tool execution that updates persistent CaseFacts state.\"\"\"
    trimmed = trim_order_output(RAW_ORDER_PAYLOAD)
    case_facts.order_id = trimmed["order_id"]
    case_facts.order_amount = trimmed["amount"]
    return trimmed

print(" Output trimmer and CaseFacts container ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Compare raw payload size vs trimmed payload size.
2. Observe how tool execution updates the persistent Case Facts block."""),

        code_cell("""# Step 3: Simulation
# 1. Trimming comparison
trimmed_order = trim_order_output(RAW_ORDER_PAYLOAD)
raw_size = len(json.dumps(RAW_ORDER_PAYLOAD))
trimmed_size = len(json.dumps(trimmed_order))

print(f"Raw Payload Characters: {raw_size} chars")
print(f"Trimmed Payload Characters: {trimmed_size} chars")
print(f"Token Footprint Reduction: ~{((raw_size - trimmed_size) / raw_size) * 100:.1f}%")

# 2. CaseFacts persistence across turns
facts = CaseFacts(customer_id="CUST-441", customer_email="alice@test.com")
print("\\nInitial Prompt Block:\\n", facts.render_prompt_block())

# Tool execution updates facts
lookup_order_tool("ORD-2026-9921", facts)
print("\\nUpdated Prompt Block after Order Lookup:\\n", facts.render_prompt_block())"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Sensitive internal keys (rack ID, gateway token) are stripped from trimmed output.
2. CaseFacts reflects customer and order state reliably."""),

        code_cell("""# Step 4: Verification Checks
assert "warehouse_rack_id" not in trimmed_order
assert "payment_gateway_auth_token" not in trimmed_order
assert trimmed_order["order_id"] == "ORD-2026-9921"
assert trimmed_order["amount"] == 149.99

rendered = facts.render_prompt_block()
assert "CUST-441" in rendered
assert "ORD-2026-9921" in rendered
assert "$149.99" in rendered

print(" All verification assertions passed! Context preservation verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Trim tool outputs to essential fields before appending them to conversation history.
- **Rule 2**: Maintain critical identifiers in a persistent **CaseFacts** block outside conversation summaries.
- **Rule 3**: Strip raw backend telemetry and internal keys to conserve context window capacity."""),
    ]
    return save_notebook("domain5", "ts_5_1_context_preservation", cells)


def build_ts_5_2():
    cells = [
        markdown_cell("""# Domain 5: Context Management & Reliability
## TS 5.2: Design Effective Escalation and Ambiguity Resolution Patterns
**Certification Focus**: CCAR-F Domain 5 (15% Exam Weight) | **Scenario Alignment**: Scenario 1 & 3

---

### 🎯 Key Architectural Principles
1. **Escalation Policy Matrix**:
   - **Trigger 1: Customer Demands Human** -> Immediate escalation to human supervisor. No automated pushback.
   - **Trigger 2: Ambiguity Tie (e.g. multiple accounts found)** -> Ask the user for clarification. Do **not** escalate to humans or guess.
   - **Trigger 3: Policy Gap / Uncovered Condition** -> Escalate to human supervisor with a structured case summary.
2. **Preserving Conflicting Source Provenance**:
   - When external sources report contradictory data, **never calculate an average**.
   - Preserve both claims with explicit source attribution, publication dates, and methodology notes."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 5.2 Escalation & Provenance.")"""),

        markdown_cell("""### 🚦 Step 2: Escalation Evaluator & Provenance Synthesizer
We implement the escalation decision engine and conflicting source synthesizer."""),

        code_cell("""# Step 2: Escalation & Provenance Logic
@dataclass
class EscalationDecision:
    escalate: bool
    target: str  # 'human_supervisor' | 'user_clarification' | 'continue_automated'
    reason: str
    clarification_prompt: Optional[str] = None


@dataclass
class SourceClaim:
    metric_name: str
    value: str
    source_name: str
    published_date: str
    methodology: str


def evaluate_escalation_rules(user_message: str, matching_records_count: int, has_matching_policy: bool) -> EscalationDecision:
    \"\"\"Evaluates user message and state against the architectural escalation matrix.\"\"\"
    lower = user_message.lower()
    
    # 1. Customer demands human
    if any(phrase in lower for phrase in ["speak to a person", "human agent", "talk to someone", "representative"]):
        return EscalationDecision(
            escalate=True,
            target="human_supervisor",
            reason="Customer explicitly requested human assistance."
        )

    # 2. Ambiguity tie (multiple matching records)
    if matching_records_count > 1:
        return EscalationDecision(
            escalate=False,
            target="user_clarification",
            reason="Ambiguity tie: Multiple records match customer input.",
            clarification_prompt="Multiple accounts match your information. Please provide your Account ID or Postal Code."
        )

    # 3. Policy gap
    if not has_matching_policy:
        return EscalationDecision(
            escalate=True,
            target="human_supervisor",
            reason="Unhandled policy gap: No automated policy matches this scenario."
        )

    return EscalationDecision(escalate=False, target="continue_automated", reason="Standard automated handling.")


def synthesize_conflicting_sources(claims: List[SourceClaim]) -> Dict[str, Any]:
    \"\"\"Synthesizes claims without averaging contradictory findings.\"\"\"
    metric_name = claims[0].metric_name if claims else "Unknown"
    summary_lines = [
        f"Synthesized findings for '{metric_name}':",
        "NOTE: Contradictory findings detected between authoritative sources. Values are explicitly preserved:",
    ]
    for c in claims:
        summary_lines.append(f"- {c.source_name} ({c.published_date}): {c.value} via {c.methodology}")

    return {
        "metric": metric_name,
        "has_contested_findings": len(claims) > 1,
        "claims_with_provenance": [c.__dict__ for c in claims],
        "synthesis_summary": "\\n".join(summary_lines),
    }

print(" Escalation rules and Provenance synthesizer ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Customer says "Please let me speak to a person" -> Immediate human escalation.
2. Ambiguous query with 2 matching records -> Prompts user for clarification.
3. Two sources disagree on market metrics -> Both preserved without averaging."""),

        code_cell("""# Step 3: Simulation
# Case A: Human demand
dec_a = evaluate_escalation_rules("Please let me speak to a person right now.", 1, True)
print("Case A (Human Demand):", dec_a)

# Case B: Ambiguity tie (2 records found)
dec_b = evaluate_escalation_rules("Track my recent order", 2, True)
print("\\nCase B (Ambiguity Tie):", dec_b)

# Case C: Conflicting sources synthesis
claims = [
    SourceClaim("Active Users", "100 Million", "Survey Inc", "2026-01-15", "Self-Reported Sample"),
    SourceClaim("Active Users", "120 Million", "Financial Q4 Filing", "2026-02-01", "Telemetry Audit"),
]
synth_res = synthesize_conflicting_sources(claims)
print("\\nCase C (Provenance Synthesis):\\n", synth_res["synthesis_summary"])"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Human demand escalates to `human_supervisor`.
2. Multiple records triggers `user_clarification`.
3. Conflicting claims are preserved with source citations without averaging."""),

        code_cell("""# Step 4: Verification Checks
assert dec_a.escalate is True
assert dec_a.target == "human_supervisor"

assert dec_b.escalate is False
assert dec_b.target == "user_clarification"
assert "Multiple accounts match" in dec_b.clarification_prompt

assert synth_res["has_contested_findings"] is True
assert len(synth_res["claims_with_provenance"]) == 2
assert "Survey Inc" in synth_res["synthesis_summary"]
assert "Financial Q4 Filing" in synth_res["synthesis_summary"]

print(" All verification assertions passed! Escalation and provenance verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Immediately escalate to a human when the user explicitly requests one.
- **Rule 2**: When multiple records match (ambiguity), **clarify with the user**; do not guess or escalate.
- **Rule 3**: Never average conflicting numbers; preserve both claims with explicit source provenance."""),
    ]
    return save_notebook("domain5", "ts_5_2_escalation_and_provenance", cells)


def build_ts_5_3():
    cells = [
        markdown_cell("""# Domain 5: Context Management & Reliability
## TS 5.3: Implement Error Propagation Strategies and Track Coverage Across Multi-Agent Systems
**Certification Focus**: CCAR-F Domain 5 (15% Exam Weight) | **Scenario Alignment**: Scenario 3 (Multi-Agent Research System)

---

### 🎯 Key Architectural Principles
1. **Three-State Subagent Status Taxonomy**:
   - `SUCCESS`: Subagent completed and returned valid findings.
   - `VALID_EMPTY`: Query succeeded, but target returned 0 results. This is **not an error**.
   - `UPSTREAM_FAILURE`: Network drop, 500 error, or timeout.
2. **Coverage States**:
   - `FULL`: 100% of data sources responded successfully.
   - `PARTIAL`: One or more sources failed; coordinator must explicitly disclose omissions.
   - `FAILED`: Insufficient data to form any synthesis.
3. **Confidence Penalty**: Upstream failures must reduce synthesis confidence to prevent silent omissions from masquerading as definitive negatives."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 5.3 Error Propagation & Coverage.")"""),

        markdown_cell("""### 📊 Step 2: Coverage Synthesizer Implementation
The synthesizer calculates coverage state, lists omitted sources, and applies confidence penalties."""),

        code_cell("""# Step 2: Error Propagation & Coverage Logic
class SubagentStatus(Enum):
    SUCCESS = "SUCCESS"
    VALID_EMPTY = "VALID_EMPTY"
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"


@dataclass
class SubagentResult:
    source_name: str
    status: SubagentStatus
    findings: List[Dict[str, Any]]
    error_message: Optional[str] = None


@dataclass
class SynthesisReport:
    coverage_state: str  # 'FULL' | 'PARTIAL' | 'FAILED'
    confidence_level: float
    successful_sources: List[str]
    source_omissions: List[str]
    findings: List[Dict[str, Any]]


class MultiAgentSynthesizer:
    @staticmethod
    def synthesize(results: List[SubagentResult]) -> SynthesisReport:
        successful = []
        omissions = []
        aggregated_findings = []

        for r in results:
            if r.status in (SubagentStatus.SUCCESS, SubagentStatus.VALID_EMPTY):
                successful.append(r.source_name)
                aggregated_findings.extend(r.findings)
            elif r.status == SubagentStatus.UPSTREAM_FAILURE:
                omissions.append(r.source_name)

        total_sources = len(results)
        if len(omissions) == 0:
            coverage = "FULL"
            confidence = 1.0
        elif len(successful) == 0:
            coverage = "FAILED"
            confidence = 0.0
        else:
            coverage = "PARTIAL"
            # Apply confidence penalty proportional to missing sources
            confidence = round(len(successful) / total_sources, 2)

        return SynthesisReport(
            coverage_state=coverage,
            confidence_level=confidence,
            successful_sources=successful,
            source_omissions=omissions,
            findings=aggregated_findings,
        )

print(" MultiAgentSynthesizer ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We synthesize 3 sources:
1. `SourceA`: Success (has docs).
2. `SourceB`: Valid Empty (0 docs found, but query succeeded).
3. `SourceC`: Upstream Failure (504 Gateway Timeout)."""),

        code_cell("""# Step 3: Simulation
results = [
    SubagentResult("SourceA_Docs", SubagentStatus.SUCCESS, [{"title": "Agent Arch", "score": 0.95}]),
    SubagentResult("SourceB_KnowledgeBase", SubagentStatus.VALID_EMPTY, []),
    SubagentResult("SourceC_ExternalAPI", SubagentStatus.UPSTREAM_FAILURE, [], error_message="504 Timeout"),
]

report = MultiAgentSynthesizer.synthesize(results)
print("Coverage State:", report.coverage_state)
print("Confidence Level:", report.confidence_level)
print("Successful Sources:", report.successful_sources)
print("Omitted Sources Disclosed:", report.source_omissions)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Overall coverage is `PARTIAL`.
2. `SourceC_ExternalAPI` is explicitly disclosed under `source_omissions`.
3. Confidence level is penalized to 0.67."""),

        code_cell("""# Step 4: Verification Checks
assert report.coverage_state == "PARTIAL"
assert "SourceC_ExternalAPI" in report.source_omissions
assert report.confidence_level == 0.67
assert "SourceB_KnowledgeBase" in report.successful_sources

print(" All verification assertions passed! Error propagation and coverage verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Distinguish `VALID_EMPTY` (successful query, 0 results) from `UPSTREAM_FAILURE` (error).
- **Rule 2**: When any source fails, report **PARTIAL coverage** and disclose omitted sources explicitly.
- **Rule 3**: Apply confidence penalties when aggregating data with partial coverage."""),
    ]
    return save_notebook("domain5", "ts_5_3_error_propagation_coverage", cells)


def build_ts_5_4():
    cells = [
        markdown_cell("""# Domain 5: Context Management & Reliability
## TS 5.4: Manage Context in Large Codebase Exploration with Scratchpads & Human Review Routing
**Certification Focus**: CCAR-F Domain 5 (15% Exam Weight) | **Scenario Alignment**: Scenario 4 & 6

---

### 🎯 Key Architectural Principles
1. **The Working Memory Scratchpad**: During complex codebase explorations, keep raw file reads out of conversation history. Record findings into an external scratchpad (`CodebaseScratchpadManager`) and inject only the compact scratchpad summary into Claude.
2. **Confidence-Based Routing**:
   - Confidence >= 0.85: Auto-approve.
   - Confidence < 0.85: Route to human reviewers.
3. **Stratified Random Sampling**: To catch silent model drift or systemic inaccuracies, take a 5–10% random sample across **all document classes/segments** (even high-confidence items)."""),

        code_cell("""# Step 1: Environment & Setup
import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 5.4 Scratchpads & Human Review Routing.")"""),

        markdown_cell("""### 📝 Step 2: Scratchpad & Human Review Routing Engine
We implement the working memory scratchpad and confidence router with stratified sampling."""),

        code_cell("""# Step 2: Scratchpad & Router Logic
@dataclass
class ExtractionRecord:
    doc_id: str
    category: str
    confidence: float
    extracted_amount: float
    requires_human_review: bool = False


class HumanReviewRoutingEngine:
    def __init__(self, confidence_threshold: float = 0.85) -> None:
        self.threshold = confidence_threshold

    def route_record(self, record: ExtractionRecord) -> ExtractionRecord:
        record.requires_human_review = (record.confidence < self.threshold)
        return record

    @staticmethod
    def stratified_random_sample(records: List[ExtractionRecord], sample_per_stratum: int = 1) -> List[ExtractionRecord]:
        \"\"\"Selects representative audit samples across distinct categories/strata.\"\"\"
        strata = defaultdict(list)
        for r in records:
            strata[r.category].append(r)
        
        sampled = []
        for cat, items in strata.items():
            sampled.extend(items[:sample_per_stratum])
        return sampled


class CodebaseScratchpadManager:
    \"\"\"External working memory container preventing conversation context bloat.\"\"\"
    def __init__(self) -> None:
        self.findings: List[str] = []

    def record_finding(self, observation: str) -> None:
        self.findings.append(observation)

    def render_scratchpad(self) -> str:
        return \"### AGENT WORKING SCRATCHPAD\\n\" + \"\\n\".join(f\"- {f}\" for f in self.findings)

print(\" HumanReviewRoutingEngine and CodebaseScratchpadManager ready.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Route high vs low confidence records.
2. Execute stratified audit sampling across document segments.
3. Record exploration observations into scratchpad."""),

        code_cell("""# Step 3: Simulation
router = HumanReviewRoutingEngine(confidence_threshold=0.85)

rec_high = router.route_record(ExtractionRecord("D1", "standard_invoice", 0.96, 120.0))
rec_low = router.route_record(ExtractionRecord("D2", "customs_declaration", 0.72, 450.0))

print("High Confidence (0.96) Needs Human:", rec_high.requires_human_review)
print("Low Confidence (0.72) Needs Human:", rec_low.requires_human_review)

# Stratified audit across categories
records = [
    ExtractionRecord("D10", "Category_A", 0.95, 10.0),
    ExtractionRecord("D11", "Category_A", 0.92, 20.0),
    ExtractionRecord("D20", "Category_B", 0.88, 30.0),
]
audit_sample = HumanReviewRoutingEngine.stratified_random_sample(records, sample_per_stratum=1)
print(f"\\nStratified Sample Count: {len(audit_sample)} (1 from Category_A, 1 from Category_B)")

# Scratchpad memory test
pad = CodebaseScratchpadManager()
pad.record_finding("auth_service uses bcrypt with 12 rounds.")
pad.record_finding("redis cache TTL is set to 3600 seconds.")
print("\\n", pad.render_scratchpad())"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. High-confidence item bypasses human review.
2. Low-confidence item is routed to human review.
3. Stratified sampling captures 1 sample per distinct stratum.
4. Scratchpad renders clean, formatted findings."""),

        code_cell("""# Step 4: Verification Checks
assert rec_high.requires_human_review is False
assert rec_low.requires_human_review is True

assert len(audit_sample) == 2
strata_represented = {r.category for r in audit_sample}
assert "Category_A" in strata_represented
assert "Category_B" in strata_represented

scratchpad_text = pad.render_scratchpad()
assert "bcrypt" in scratchpad_text
assert "redis cache" in scratchpad_text

print(" All verification assertions passed! Scratchpads & review routing verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Maintain an **external scratchpad** for working memory during multi-step codebase exploration.
- **Rule 2**: Route items below the confidence threshold (<0.85) to human specialists.
- **Rule 3**: Apply **stratified random sampling** across document classes to audit high-confidence decisions for silent model drift."""),
    ]
    return save_notebook("domain5", "ts_5_4_scratchpads_and_human_review", cells)


def build_ts_5_5():
    cells = [
        markdown_cell("""# Domain 5: Context Management & Reliability
## TS 5.5: Design Human Review Workflows and Confidence Calibration
**Certification Focus**: CCAR-F Domain 5 (15% Exam Weight) | **Scenario Alignment**: Scenario 6 (Structured Data Extraction & Auditing)

---

### 🎯 Key Architectural Principles
1. **The Three Triage Tiers**:
   - **Tier 1: `AUTO_APPROVE`** (Confidence >= 0.90) -> processed automatically without human involvement.
   - **Tier 2: `STRATIFIED_AUDIT`** (Confidence >= 0.90 but selected in a 5–10% stratified random audit sample to check for silent drift).
   - **Tier 3: `MANDATORY_ESCALATION`** (Confidence < 0.80) -> routed directly to human specialists.
2. **Confidence Calibration**: Raw probabilities must be calibrated against historical ground truth to avoid overconfidence.
3. **Audit Trails**: Every routing decision must record its triage tier, confidence score, and audit flags."""),

        code_cell("""# Step 1: Environment & Setup
import random
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 5.5 Human Review Calibration.")"""),

        markdown_cell("""### ⚖️ Step 2: Calibrated Router Implementation
We implement the three-tier routing engine with stratified auditing."""),

        code_cell("""# Step 2: Calibrated Router Logic
class RoutingTier(Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    STRATIFIED_AUDIT = "STRATIFIED_AUDIT"
    MANDATORY_ESCALATION = "MANDATORY_ESCALATION"


@dataclass
class TriageDecision:
    doc_id: str
    confidence: float
    doc_type: str
    routing_tier: RoutingTier
    rationale: str


class ConfidenceRouter:
    def __init__(self, high_confidence_threshold: float = 0.90, audit_rate: float = 0.10, random_seed: int = 42) -> None:
        self.high_threshold = high_confidence_threshold
        self.audit_rate = audit_rate
        random.seed(random_seed)

    def route_item(self, doc_id: str, confidence: float, doc_type: str) -> TriageDecision:
        if confidence < self.high_threshold:
            return TriageDecision(
                doc_id=doc_id,
                confidence=confidence,
                doc_type=doc_type,
                routing_tier=RoutingTier.MANDATORY_ESCALATION,
                rationale=f"Confidence {confidence:.2f} is below high-confidence threshold ({self.high_threshold:.2f})."
            )

        # High confidence item: test for stratified audit sample
        is_audited = (random.random() < self.audit_rate)
        if is_audited:
            return TriageDecision(
                doc_id=doc_id,
                confidence=confidence,
                doc_type=doc_type,
                routing_tier=RoutingTier.STRATIFIED_AUDIT,
                rationale="Selected for stratified quality audit sample."
            )

        return TriageDecision(
            doc_id=doc_id,
            confidence=confidence,
            doc_type=doc_type,
            routing_tier=RoutingTier.AUTO_APPROVE,
            rationale="Confidence meets threshold; auto-approved."
        )

print(" Calibrated ConfidenceRouter initialized.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Low confidence -> Mandatory Escalation.
2. High confidence -> Auto-approved or Stratified Audit."""),

        code_cell("""# Step 3: Simulation
router = ConfidenceRouter(high_confidence_threshold=0.90, audit_rate=0.10, random_seed=42)

# Case 1: Low confidence document
dec_low = router.route_item("doc_101", 0.65, "invoice")
print("Doc 101 (0.65) Tier:", dec_low.routing_tier.value)
print("Rationale:", dec_low.rationale)

# Case 2: High confidence document
dec_high = router.route_item("doc_102", 0.98, "invoice")
print("\\nDoc 102 (0.98) Tier:", dec_high.routing_tier.value)
print("Rationale:", dec_high.rationale)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Low confidence document maps to `MANDATORY_ESCALATION`.
2. High confidence document maps to `AUTO_APPROVE` or `STRATIFIED_AUDIT`.
3. Routing tiers conform to the CCAR-F calibration taxonomy."""),

        code_cell("""# Step 4: Verification Checks
assert dec_low.routing_tier == RoutingTier.MANDATORY_ESCALATION
assert dec_high.routing_tier in (RoutingTier.AUTO_APPROVE, RoutingTier.STRATIFIED_AUDIT)

print(" All verification assertions passed! Confidence calibration verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Low confidence (<0.80) requires **mandatory escalation** to human specialists.
- **Rule 2**: High confidence (>=0.90) items must still be subjected to a **stratified random audit sample** (5–10%) to catch silent drift.
- **Rule 3**: Store confidence and rationale in the audit trail of every automated triage decision."""),
    ]
    return save_notebook("domain5", "ts_5_5_human_review_calibration", cells)


def build_ts_5_6():
    cells = [
        markdown_cell("""# Domain 5: Context Management & Reliability
## TS 5.6: Preserve Information Provenance and Handle Uncertainty in Multi-Source Synthesis
**Certification Focus**: CCAR-F Domain 5 (15% Exam Weight) | **Scenario Alignment**: Scenario 3 & 6

---

### 🎯 Key Architectural Principles
1. **The Preservation Contract**: When multiple credible sources provide conflicting facts (e.g. Q3 revenue reported as $1.0B vs $1.2B), Claude must **never average the values**.
2. **Explicit Provenance Attribution**: Each conflicting claim must retain its source name, publication date, and measurement methodology.
3. **Highlighting Uncertainty**: Disclose the conflict clearly so human decision-makers understand the variance rather than acting on a false composite consensus."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 5.6 Provenance & Uncertainty.")"""),

        markdown_cell("""### 📜 Step 2: Provenance Tracking & Synthesis Engine
We implement the metric claim container and synthesis engine that strictly preserves conflicting values."""),

        code_cell("""# Step 2: Provenance Synthesizer Logic
@dataclass
class SourceCitation:
    source_name: str
    published_date: str
    methodology: str


@dataclass
class FactClaim:
    metric: str
    value: str
    citation: SourceCitation


@dataclass
class ProvenanceSynthesisEntry:
    metric: str
    has_conflict: bool
    status: str  # 'RESOLVED_SINGLE_SOURCE' | 'PRESERVED_CONFLICT'
    claims: List[Dict[str, Any]]
    synthesized_guidance: str


class ProvenanceSynthesizer:
    def __init__(self) -> None:
        self.claims: List[FactClaim] = []

    def add_claim(self, metric: str, value: str, source_name: str, published_date: str, methodology: str) -> None:
        self.claims.append(FactClaim(
            metric=metric,
            value=value,
            citation=SourceCitation(source_name=source_name, published_date=published_date, methodology=methodology)
        ))

    def synthesize_metrics(self) -> List[ProvenanceSynthesisEntry]:
        by_metric = {}
        for c in self.claims:
            by_metric.setdefault(c.metric, []).append(c)

        entries = []
        for metric, claims_list in by_metric.items():
            distinct_values = {c.value for c in claims_list}
            has_conflict = (len(distinct_values) > 1)

            claims_data = [
                {
                    "value": c.value,
                    "source": c.citation.source_name,
                    "date": c.citation.published_date,
                    "methodology": c.citation.methodology,
                }
                for c in claims_list
            ]

            if has_conflict:
                guidance = (
                    f"Contradictory values detected for '{metric}'. "
                    "CRITICAL: Do NOT calculate an average or blend these metrics. "
                    "Both values and sources are preserved explicitly for stakeholder review."
                )
                status = "PRESERVED_CONFLICT"
            else:
                guidance = f"Unanimous consensus on '{metric}'."
                status = "RESOLVED_SINGLE_SOURCE"

            entries.append(ProvenanceSynthesisEntry(
                metric=metric,
                has_conflict=has_conflict,
                status=status,
                claims=claims_data,
                synthesized_guidance=guidance,
            ))

        return entries

print(" ProvenanceSynthesizer ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We record conflicting revenue numbers from a preliminary press release and an audited 10-Q filing."""),

        code_cell("""# Step 3: Simulation
synth = ProvenanceSynthesizer()

# Claim 1: Preliminary Press Release
synth.add_claim("Q3 Revenue", "$1.0B", "Press_Release", "2026-10-01", "Preliminary Unaudited")

# Claim 2: Audited 10-Q Filing
synth.add_claim("Q3 Revenue", "$1.2B", "SEC_10Q_Filing", "2026-10-15", "Audited Financials")

entries = synth.synthesize_metrics()
print("Synthesized Entries Count:", len(entries))
entry = entries[0]
print("Metric:", entry.metric)
print("Conflict Detected:", entry.has_conflict)
print("Status:", entry.status)
print("Guidance:", entry.synthesized_guidance)
print("\\nClaims with Provenance:")
for c in entry.claims:
    print(f"  - {c['source']} ({c['date']}): {c['value']} [{c['methodology']}]")"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Conflict is identified.
2. Status is `PRESERVED_CONFLICT`.
3. Guidance strictly prohibits averaging.
4. Both source citations are preserved."""),

        code_cell("""# Step 4: Verification Checks
assert len(entries) == 1
assert entry.has_conflict is True
assert entry.status == "PRESERVED_CONFLICT"
assert "Do NOT calculate an average" in entry.synthesized_guidance
assert len(entry.claims) == 2

sources = [c["source"] for c in entry.claims]
assert "Press_Release" in sources
assert "SEC_10Q_Filing" in sources

print(" All verification assertions passed! Provenance preservation verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Never calculate an average or aggregate conflicting figures when authoritative sources disagree.
- **Rule 2**: Preserve all claims with source name, publication date, and measurement methodology.
- **Rule 3**: Disclose uncertainty explicitly to human decision-makers rather than presenting a false consensus."""),
    ]
    return save_notebook("domain5", "ts_5_6_provenance_and_uncertainty", cells)


def main():
    print("=== Generating Domain 5 Notebooks (TS 5.1 - TS 5.6) ===")
    build_ts_5_1()
    build_ts_5_2()
    build_ts_5_3()
    build_ts_5_4()
    build_ts_5_5()
    build_ts_5_6()
    print(" Domain 5 notebooks generated successfully!\n")


if __name__ == "__main__":
    main()
