"""
Domain 4 Notebook Generator: Prompt Engineering & Structured Output (TS 4.1 - TS 4.6).
Generates comprehensive Jupyter notebooks with step-by-step walkthroughs,
offline simulations, and automated verification checks.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.notebook_builder import code_cell, markdown_cell, save_notebook


def build_ts_4_1():
    cells = [
        markdown_cell("""# Domain 4: Prompt Engineering & Structured Output
## TS 4.1: Design Prompts with Explicit Criteria to Reduce False Positives
**Certification Focus**: CCAR-F Domain 4 (20% Exam Weight) | **Scenario Alignment**: Scenario 6 (Structured Data Extraction & Auditing)

---

### 🎯 Key Architectural Principles
1. **Explicit Negative Boundaries**: Vague instructions ("flag anything suspicious") lead to unacceptably high false-positive rates. Prompts must define explicit negative boundary criteria (e.g. mock test keys, fixture data, dummy placeholders).
2. **Two-Pass Deterministic Classification**:
   - Pass 1: Pattern detection against explicit threat rubrics.
   - Pass 2: Negative boundary filter (checking file paths for `test_`, `fixture`, and token substrings like `mock_`, `dummy`).
3. **Severity Calibration**: Classify findings by severity (`CRITICAL`, `HIGH`, `INFO`) based on evidence grounding rather than qualitative guesswork."""),

        code_cell("""# Step 1: Environment & Setup
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 4.1 Explicit Criteria Classification.")"""),

        markdown_cell("""### 🔍 Step 2: Explicit Criteria Classifier Implementation
The classifier tests patterns against positive threat regexes and filters out matches that hit negative boundary criteria."""),

        code_cell("""# Step 2: Classifier Implementation
@dataclass
class VulnerabilityFinding:
    category: str
    severity: str
    target: str
    evidence: str
    reasoning: str


class ExplicitCriteriaClassifier:
    CATEGORIES = {
        "HARDCODED_SECRET": {
            "severity": "CRITICAL",
            "regex": r"(sk-ant-[a-zA-Z0-9_-]{20,}|AKIA[0-9A-Z]{16})",
            "negative_boundaries": [r"mock_", r"test_", r"dummy", r"placeholder"]
        },
        "SQL_INJECTION": {
            "severity": "HIGH",
            "regex": r"execute\s*\(\s*f.*SELECT.*?\{",
            "negative_boundaries": ["param", ":val", "?"]
        }
    }

    def evaluate_snippet(self, file_path: str, code_content: str) -> List[VulnerabilityFinding]:
        findings = []
        is_test_file = "test" in file_path.lower() or "fixture" in file_path.lower()

        for category_name, rule in self.CATEGORIES.items():
            pattern = rule["regex"]
            matches = list(re.finditer(pattern, code_content))

            for match in matches:
                matched_str = match.group(0)
                # Check negative boundary criteria
                is_negative_boundary = any(re.search(b, matched_str, re.IGNORECASE) for b in rule["negative_boundaries"])

                # If found in a test file and has test markers -> filter out false positive
                if is_test_file and is_negative_boundary:
                    continue

                # If found in a test file but looks like a REAL production secret -> flag
                findings.append(VulnerabilityFinding(
                    category=category_name,
                    severity=rule["severity"],
                    target=file_path,
                    evidence=matched_str,
                    reasoning=f"Matched threat pattern {pattern} without negative boundary exemption."
                ))

        return findings

print(" ExplicitCriteriaClassifier initialized.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Test file with dummy/mock token -> filtered out (0 findings).
2. Production file with live API token -> flagged as CRITICAL."""),

        code_cell("""# Step 3: Simulation
classifier = ExplicitCriteriaClassifier()

# Case A: Mock token in test file (Negative boundary filter applies!)
test_snippet = 'mock_api_key = "sk-ant-test_mock_dummy_credentials_0123456789"'
findings_test = classifier.evaluate_snippet("tests/test_auth.py", test_snippet)
print("Findings in tests/test_auth.py:", len(findings_test))

# Case B: Real live token in production code
prod_snippet = 'anthropic_key = "sk-ant-live0123456789abcdef0123456789"'
findings_prod = classifier.evaluate_snippet("src/config.py", prod_snippet)
print("Findings in src/config.py:", len(findings_prod))
if findings_prod:
    print("Finding Detail:", findings_prod[0])"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Mock keys in test files produce 0 false positives.
2. Real keys in production files trigger CRITICAL findings."""),

        code_cell("""# Step 4: Verification Checks
assert len(findings_test) == 0, "Negative boundary criteria must filter out mock test keys!"
assert len(findings_prod) == 1
assert findings_prod[0].severity == "CRITICAL"
assert findings_prod[0].category == "HARDCODED_SECRET"

print(" All verification assertions passed! Explicit criteria verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Provide explicit **negative boundary criteria** in classification prompts to eliminate false positives on test fixtures.
- **Rule 2**: Avoid qualitative instructions like "be conservative" or "flag anything suspicious".
- **Rule 3**: Combine pattern matching with context-aware exemptions (test file + mock marker)."""),
    ]
    return save_notebook("domain4", "ts_4_1_explicit_criteria_classification", cells)


def build_ts_4_2():
    cells = [
        markdown_cell("""# Domain 4: Prompt Engineering & Structured Output
## TS 4.2: Apply Few-Shot Prompting and Multi-Instance Architectures
**Certification Focus**: CCAR-F Domain 4 (20% Exam Weight) | **Scenario Alignment**: Scenario 6 (Structured Data Extraction & Auditing)

---

### 🎯 Key Architectural Principles
1. **Few-Shot Examples with `<thinking>` Blocks**: High-performing few-shot prompts do not merely show input and output; they provide explicit `<thinking>` demonstrations showing how Claude should reason through edge cases.
2. **Multi-Instance Architecture**: To achieve unbiased code reviews or audit assessments, dispatch tasks to **independent reviewer instances** with clean, isolated conversational contexts.
3. **Consensus & Voting**: Aggregating independent verdicts without shared memory eliminates sequential anchoring bias and produces reliable consensus."""),

        code_cell("""# Step 1: Environment & Setup
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 4.2 Few-Shot & Multi-Instance.")"""),

        markdown_cell("""### 📚 Step 2: Few-Shot Prompt Block & Multi-Instance Pipeline
We implement the few-shot template with thinking blocks and the multi-instance aggregator."""),

        code_cell("""# Step 2: Few-Shot & Multi-Instance Logic
@dataclass
class FewShotExample:
    input_text: str
    thinking: str
    output_json: Dict[str, Any]

FEW_SHOT_EXTRACTION_EXAMPLES = [
    FewShotExample(
        input_text="Invoice from CloudHost Inc: 1x Server $100, 2x IP Addr $10, Stated Total $120.",
        thinking=(
            "1. Server: 1 * 100 = 100. "
            "2. IP: 2 * 10 = 20. "
            "3. Calculated sum = 120. Stated total = 120. Arithmetic matches perfectly."
        ),
        output_json={"vendor": "CloudHost Inc", "calculated_total": 120.0, "status": "VALID"}
    ),
    FewShotExample(
        input_text="Receipt: Lunch $45, Tip $10, Total stated $60.",
        thinking=(
            "1. Lunch = 45, Tip = 10. "
            "2. Expected total = 55. Stated total = 60. Math mismatch of $5. Flag arithmetic anomaly."
        ),
        output_json={"vendor": "Unknown", "calculated_total": 55.0, "status": "ARITHMETIC_MISMATCH"}
    ),
]

def render_few_shot_prompt_block(examples: List[FewShotExample]) -> str:
    \"\"\"Renders input, thinking, and output blocks for few-shot guidance.\"\"\"
    parts = [\"### FEW-SHOT REASONING EXAMPLES\"]
    for i, ex in enumerate(examples, start=1):
        parts.append(
            f\"--- EXAMPLE {i} ---\\n\"
            f\"<input>\\n{ex.input_text}\\n</input>\\n\"
            f\"<thinking>\\nArchitectural Reasoning: {ex.thinking}\\n</thinking>\\n\"
            f\"<output>\\n{json.dumps(ex.output_json, indent=2)}\\n</output>\"
        )
    return \"\\n\\n\".join(parts)


class MultiInstanceReviewPipeline:
    @staticmethod
    def prepare_reviewer_payload(code_snippet: str, review_checklist: List[str]) -> Dict[str, Any]:
        \"\"\"Creates an isolated reviewer prompt ensuring no shared conversational state.\"\"\"
        checklist_str = \"\\n\".join(f\"- {item}\" for item in review_checklist)
        return {
            \"role\": \"user\",
            \"content\": (
                \"You are an independent, isolated code auditor. \"
                \"Evaluate this code strictly against the checklist without assuming prior context:\\n\"
                f\"CHECKLIST:\\n{checklist_str}\\n\\n\"
                f\"CODE:\\n{code_snippet}\"
            )
        }

    @staticmethod
    def aggregate_independent_reviews(verdicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        \"\"\"Aggregates verdicts across independent instances via majority consensus.\"\"\"
        approvals = sum(1 for v in verdicts if v.get(\"approved\", False))
        consensus_approved = (approvals >= len(verdicts) / 2)
        return {
            \"total_instances\": len(verdicts),
            \"approvals\": approvals,
            \"consensus_approved\": consensus_approved,
        }

print(\" Few-shot and Multi-instance engines ready.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Render few-shot prompt block with `<thinking>` tags.
2. Simulate 3 independent reviewer instances and aggregate consensus."""),

        code_cell("""# Step 3: Simulation
# 1. Render few-shot prompt block
prompt_block = render_few_shot_prompt_block(FEW_SHOT_EXTRACTION_EXAMPLES)
print(prompt_block[:350] + \"\\n... [truncated]\")

# 2. Multi-instance independent reviews
reviewer_verdicts = [
    {\"instance_id\": \"inst_1\", \"approved\": True, \"findings\": []},
    {\"instance_id\": \"inst_2\", \"approved\": True, \"findings\": []},
    {\"instance_id\": \"inst_3\", \"approved\": False, \"findings\": [\"Minor typing issue\"]},
]
consensus = MultiInstanceReviewPipeline.aggregate_independent_reviews(reviewer_verdicts)
print(\"\\nMulti-Instance Consensus Result:\", consensus)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Few-shot prompt includes explicit `<thinking>` blocks.
2. Independent instance payloads do not share history.
3. Majority consensus correctly resolves 2 approvals out of 3 as approved."""),

        code_cell("""# Step 4: Verification Checks
assert \"<thinking>\" in prompt_block
assert \"Architectural Reasoning:\" in prompt_block
assert \"<output>\" in prompt_block

payload = MultiInstanceReviewPipeline.prepare_reviewer_payload(\"x = 1\", [\"Check style\"])
assert \"independent, isolated code auditor\" in payload[\"content\"]

assert consensus[\"consensus_approved\"] is True
assert consensus[\"approvals\"] == 2
assert consensus[\"total_instances\"] == 3

print(\" All verification assertions passed! Few-shot & multi-instance verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Include explicit `<thinking>` blocks in few-shot demonstrations to anchor Claude's reasoning chain.
- **Rule 2**: Use independent instances without shared memory to eliminate confirmation and sequential review bias.
- **Rule 3**: Combine independent instance outputs using majority-voting consensus."""),
    ]
    return save_notebook("domain4", "ts_4_2_few_shot_and_multi_instance", cells)


def build_ts_4_3():
    cells = [
        markdown_cell("""# Domain 4: Prompt Engineering & Structured Output
## TS 4.3: Enforce Structured Output Using Tool Use and JSON Schemas
**Certification Focus**: CCAR-F Domain 4 (20% Exam Weight) | **Scenario Alignment**: Scenario 6 (Structured Data Extraction & Auditing)

---

### 🎯 Key Architectural Principles
1. **Tool Use for Structured Output**: Invoking a dummy/extraction tool (e.g. `extract_invoice`) with a strict `input_schema` is significantly more reliable than asking Claude to emit raw JSON in message text.
2. **Programmatic Validation**: Model-extracted payloads must be verified by deterministic Python code (cross-checking arithmetic, validating mandatory conditional fields).
3. **Validation Retry Loop**: When validation detects errors (e.g. arithmetic discrepancies), the specific errors are returned to Claude in a retry turn, enabling precise self-correction."""),

        code_cell("""# Step 1: Environment & Setup
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse

print(" Environment initialized for TS 4.3 Structured Output via Tool Calling.")"""),

        markdown_cell("""### 📐 Step 2: Extraction Schema & Programmatic Validator
We define the extraction schema and the validation logic enforcing arithmetic consistency and category constraints."""),

        code_cell("""# Step 2: Schema & Validation Logic
EXTRACTION_TOOL = {
    "name": "extract_invoice",
    "description": "Extracts structured invoice fields and line items from document text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "vendor_name": {"type": "string"},
            "purchase_category": {"type": "string", "enum": ["hardware", "software_subscription", "other"]},
            "other_category_detail": {"type": ["string", "null"]},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "unit_price": {"type": "number"},
                        "total": {"type": "number"},
                    },
                    "required": ["description", "quantity", "unit_price", "total"],
                },
            },
            "stated_total": {"type": "number"},
        },
        "required": ["invoice_number", "vendor_name", "purchase_category", "line_items", "stated_total"],
    },
}

def validate_extraction(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    \"\"\"Validates mathematical consistency and conditional field rules.\"\"\"
    errors = []
    
    # 1. Arithmetic validation
    items = data.get("line_items", [])
    calc_sum = sum(item.get("total", 0.0) for item in items)
    stated = data.get("stated_total", 0.0)
    if abs(calc_sum - stated) > 0.01:
        errors.append(f"Arithmetic Mismatch: Sum of line items ({calc_sum:.2f}) does not match stated invoice total ({stated:.2f}).")

    # 2. Conditional category validation
    cat = data.get("purchase_category")
    if cat == "other" and not data.get("other_category_detail"):
        errors.append("Validation Error: 'other_category_detail' must be provided when purchase_category is 'other'.")

    return len(errors) == 0, errors

print(" Extraction schema and programmatic validator ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We test:
1. Mismatched arithmetic -> Caught by validator.
2. Missing conditional category detail -> Caught by validator.
3. Correct payload -> Passes validation."""),

        code_cell("""# Step 3: Simulation
# 1. Invalid payload (math mismatch)
invalid_payload = {
    \"invoice_number\": \"INV-001\",
    \"vendor_name\": \"Acme Corp\",
    \"purchase_category\": \"hardware\",
    \"line_items\": [{\"description\": \"Monitor\", \"quantity\": 1, \"unit_price\": 200.0, \"total\": 200.0}],
    \"stated_total\": 350.0,  # Mismatch!
}
ok1, errors1 = validate_extraction(invalid_payload)
print(\"Math Mismatch Valid:\", ok1)
print(\"Errors Detected:\", errors1)

# 2. Valid payload
valid_payload = {
    \"invoice_number\": \"INV-002\",
    \"vendor_name\": \"Cloud Services\",
    \"purchase_category\": \"software_subscription\",
    \"line_items\": [{\"description\": \"API Subscription\", \"quantity\": 1, \"unit_price\": 100.0, \"total\": 100.0}],
    \"stated_total\": 100.0,
}
ok2, errors2 = validate_extraction(valid_payload)
print(\"\\nValid Payload Result:\", ok2)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Validator catches arithmetic discrepancy.
2. Validator catches missing `other_category_detail`.
3. Valid invoice passes without errors."""),

        code_cell("""# Step 4: Verification Checks
assert ok1 is False
assert any(\"does not match stated invoice total\" in e for e in errors1)

assert ok2 is True
assert len(errors2) == 0

# Check conditional other category
bad_cat = {\"purchase_category\": \"other\", \"other_category_detail\": None, \"line_items\": [], \"stated_total\": 0.0}
ok_cat, err_cat = validate_extraction(bad_cat)
assert ok_cat is False
assert any(\"other_category_detail\" in e for e in err_cat)

print(\" All verification assertions passed! Structured output validation verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Use **tool calling schemas** for guaranteed JSON structure instead of parsing markdown JSON blocks.
- **Rule 2**: Programmatically validate extracted math (sum of line items vs stated total).
- **Rule 3**: Feed specific programmatic validation errors back into Claude for targeted self-correction."""),
    ]
    return save_notebook("domain4", "ts_4_3_structured_output_tool_use", cells)


def build_ts_4_4():
    cells = [
        markdown_cell("""# Domain 4: Prompt Engineering & Structured Output
## TS 4.4: Implement Validation, Retry, and Feedback Loops for Extraction Quality
**Certification Focus**: CCAR-F Domain 4 (20% Exam Weight) | **Scenario Alignment**: Scenario 6 (Structured Data Extraction & Auditing)

---

### 🎯 Key Architectural Principles
1. **Recoverable vs Unrecoverable Extraction Errors**:
   - **Recoverable**: Arithmetic slips, missing optional detail, malformed date string -> Feed error back in retry turn.
   - **Unrecoverable**: The source document is missing foundational required data (e.g. receipt has no tax ID or no vendor) -> **Fast-fail immediately** (`ABORTED_UNRECOVERABLE`).
2. **Fast-Fail Abort Contract**: Burning retries on unrecoverable documents wastes tokens, increases latency, and risks hallucinations.
3. **Structured Validation Reports**: Always return specific error messages to Claude to guide targeted corrections."""),

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

print(" Environment initialized for TS 4.4 Validation Retry & Feedback.")"""),

        markdown_cell("""### 🔄 Step 2: Resilient Extractor Loop Implementation
We implement the validation engine distinguishing recoverable retries from unrecoverable fast-fails."""),

        code_cell("""# Step 2: Validation Loop Logic
@dataclass
class ValidationReport:
    is_valid: bool
    is_recoverable: bool
    errors: List[str]


class ExtractionValidator:
    @staticmethod
    def validate(payload: Dict[str, Any]) -> ValidationReport:
        errors = []
        # Missing essential mandatory field -> UNRECOVERABLE
        if not payload.get("tax_id"):
            return ValidationReport(
                is_valid=False,
                is_recoverable=False,
                errors=["FATAL: Mandatory Tax ID is missing entirely from source document."],
            )

        # Arithmetic check -> RECOVERABLE
        subtotal = payload.get("subtotal", 0.0)
        total = payload.get("total", 0.0)
        if subtotal > total:
            errors.append(f"Arithmetic discrepancy: subtotal ${subtotal} cannot exceed total ${total}.")

        return ValidationReport(
            is_valid=len(errors) == 0,
            is_recoverable=True,
            errors=errors,
        )


class ResilientExtractorLoop:
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    def run_validation_cycle(self, document_text: str, model_turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        retries_used = 0
        for i, turn_payload in enumerate(model_turns):
            report = ExtractionValidator.validate(turn_payload)
            if report.is_valid:
                return {"status": "SUCCESS", "retries_used": retries_used, "data": turn_payload}
            
            # Fast fail if unrecoverable!
            if not report.is_recoverable:
                return {
                    "status": "ABORTED_UNRECOVERABLE",
                    "retries_used": retries_used,
                    "reason": report.errors[0],
                }

            retries_used += 1
            if retries_used >= self.max_retries:
                return {"status": "EXHAUSTED_RETRIES", "retries_used": retries_used, "errors": report.errors}

        return {"status": "NO_TURNS_PROVIDED"}

print(" ResilientExtractorLoop initialized.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Recoverable retry: Turn 1 has math error, Turn 2 fixes it -> Success in 1 retry.
2. Unrecoverable missing tax ID -> Fast-fails immediately with 0 retries."""),

        code_cell("""# Step 3: Simulation
loop = ResilientExtractorLoop(max_retries=3)

# 1. Recoverable scenario
turns_recoverable = [
    {"subtotal": 100.0, "total": 80.0, "tax_id": "TX-99"},   # Math error
    {"subtotal": 100.0, "total": 110.0, "tax_id": "TX-99"},  # Corrected!
]
res_rec = loop.run_validation_cycle("Doc with tax TX-99", turns_recoverable)
print("Recoverable Scenario Result:", res_rec)

# 2. Unrecoverable scenario (Tax ID missing entirely)
turns_unrecoverable = [
    {"subtotal": 50.0, "total": 55.0, "tax_id": None}
]
res_unrec = loop.run_validation_cycle("Lunch receipt without tax info", turns_unrecoverable)
print("\\nUnrecoverable Scenario Result:", res_unrec)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Recoverable errors succeed with `retries_used == 1`.
2. Unrecoverable errors fast-fail with `retries_used == 0` and status `ABORTED_UNRECOVERABLE`."""),

        code_cell("""# Step 4: Verification Checks
assert res_rec["status"] == "SUCCESS"
assert res_rec["retries_used"] == 1

assert res_unrec["status"] == "ABORTED_UNRECOVERABLE"
assert res_unrec["retries_used"] == 0
assert "FATAL" in res_unrec["reason"]

print(" All verification assertions passed! Retry and fast-fail verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Distinguish **recoverable** validation errors from **unrecoverable** document gaps.
- **Rule 2**: Fast-fail immediately on unrecoverable documents; do not burn retry budgets.
- **Rule 3**: Feed specific error strings back in the retry prompt to guide Claude's correction."""),
    ]
    return save_notebook("domain4", "ts_4_4_validation_retry_feedback", cells)


def build_ts_4_5():
    cells = [
        markdown_cell("""# Domain 4: Prompt Engineering & Structured Output
## TS 4.5: Design Efficient Batch Processing Strategies with Message Batches API
**Certification Focus**: CCAR-F Domain 4 (20% Exam Weight) | **Scenario Alignment**: Scenario 6 (Structured Data Extraction & Auditing)

---

### 🎯 Key Architectural Principles
1. **The Message Batches API**:
   - **50% Cost Discount** on all input and output tokens compared to standard on-demand pricing.
   - **24-Hour SLA**: Results processed asynchronously within a 24-hour turnaround window.
   - **Non-Real-Time Workloads**: Ideal for offline backfills, nightly vulnerability scans, and large document archive migrations.
2. **Partial Failure Resubmission**: Batches may have individual failures (e.g. content policy, timeouts). The engine must filter succeeded vs failed requests by `custom_id` and resubmit **only** the failed subset."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 4.5 Message Batches API.")"""),

        markdown_cell("""### 📦 Step 2: Message Batches Engine Implementation
We implement the batch management engine with partial failure isolation and cost savings calculations."""),

        code_cell("""# Step 2: Batch Engine Logic
@dataclass
class BatchRequest:
    custom_id: str
    params: Dict[str, Any]


@dataclass
class BatchResponse:
    batch_id: str
    status: str
    total_requests: int
    succeeded: List[str]
    failed: List[str]


class MessageBatchesEngine:
    def __init__(self) -> None:
        self.batches: Dict[str, BatchResponse] = {}

    def submit_batch(self, requests: List[BatchRequest]) -> str:
        batch_id = f"batch_{len(self.batches) + 1:03d}"
        succeeded = []
        failed = []

        # Simulate batch processing
        for req in requests:
            # Simulate failure for requests over token limit
            if req.params.get("token_estimate", 0) > 100_000:
                failed.append(req.custom_id)
            else:
                succeeded.append(req.custom_id)

        self.batches[batch_id] = BatchResponse(
            batch_id=batch_id,
            status="ended",
            total_requests=len(requests),
            succeeded=succeeded,
            failed=failed,
        )
        return batch_id

    def filter_failed_for_resubmission(self, batch_id: str) -> List[str]:
        \"\"\"Extracts failed custom_ids to prevent re-running already successful requests.\"\"\"
        batch = self.batches.get(batch_id)
        return batch.failed if batch else []

    @staticmethod
    def calculate_cost_savings(total_tokens: int, base_cost_per_million: float = 3.0) -> Dict[str, float]:
        \"\"\"Message Batches API provides an exact 50% discount.\"\"\"
        standard_cost = (total_tokens / 1_000_000) * base_cost_per_million
        batch_cost = standard_cost * 0.50
        savings = standard_cost - batch_cost
        return {
            \"standard_cost\": round(standard_cost, 4),
            \"batch_cost\": round(batch_cost, 4),
            \"savings\": round(savings, 4),
            \"discount_pct\": 50.0,
        }

print(\" MessageBatchesEngine initialized.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Submit batch of requests.
2. Filter failed custom_ids for partial resubmission.
3. Calculate cost savings on 50M tokens."""),

        code_cell("""# Step 3: Simulation
engine = MessageBatchesEngine()

# 1. Submit batch with mixed token estimates
requests = [
    BatchRequest(custom_id=\"doc_001\", params={\"token_estimate\": 2500}),
    BatchRequest(custom_id=\"doc_002\", params={\"token_estimate\": 150_000}),  # Fails!
    BatchRequest(custom_id=\"doc_003\", params={\"token_estimate\": 4000}),
]
batch_id = engine.submit_batch(requests)
print(f\"Batch submitted: {batch_id}\")

# 2. Extract failed items for resubmission
failed_ids = engine.filter_failed_for_resubmission(batch_id)
print(\"Failed requests needing resubmission:\", failed_ids)

# 3. Calculate 50% cost savings on 50M tokens
savings = MessageBatchesEngine.calculate_cost_savings(50_000_000)
print(\"\\nCost Analysis on 50M Tokens:\", savings)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Succeeded and failed custom_ids are partitioned.
2. Resubmission selects only failed IDs.
3. Batch cost savings calculate to exactly 50%."""),

        code_cell("""# Step 4: Verification Checks
assert failed_ids == [\"doc_002\"]
assert savings[\"discount_pct\"] == 50.0
assert savings[\"batch_cost\"] == savings[\"standard_cost\"] / 2

print(\" All verification assertions passed! Message Batches API verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Use the **Message Batches API** for non-real-time jobs to capture the **50% cost reduction**.
- **Rule 2**: The turnaround SLA is **24 hours**.
- **Rule 3**: On partial batch failure, resubmit **only the failed custom_ids**; never re-run the entire batch."""),
    ]
    return save_notebook("domain4", "ts_4_5_message_batches_api", cells)


def build_ts_4_6():
    cells = [
        markdown_cell("""# Domain 4: Prompt Engineering & Structured Output
## TS 4.6: Design Multi-Pass Review Architectures for Code Quality
**Certification Focus**: CCAR-F Domain 4 (20% Exam Weight) | **Scenario Alignment**: Scenario 2 & 5

---

### 🎯 Key Architectural Principles
1. **The Multi-Pass Review Pattern**:
   - **Pass 1 (Local File Review)**: Inspects each source file independently for syntax bugs, bare exceptions, and unhandled errors.
   - **Pass 2 (Integration Review)**: Evaluates the whole codebase across module boundaries, focusing on call signatures, keyword argument discrepancies, and shared state.
2. **Interface Mismatches**: Local reviews cannot catch when caller `client.py` uses parameter `auth_token` while definition `api.py` specifies `bearer_token`. Pass 2 is strictly required to catch interface mismatches.
3. **Decoupled Verification**: Multi-pass review guarantees that local cleanliness does not mask systemic integration flaws."""),

        code_cell("""# Step 1: Environment & Setup
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 4.6 Multi-Pass Review Architectures.")"""),

        markdown_cell("""### 🔍 Step 2: Multi-Pass Pipeline Implementation
We implement Pass 1 (local inspection) and Pass 2 (cross-file interface consistency)."""),

        code_cell("""# Step 2: Multi-Pass Pipeline
@dataclass
class ReviewFinding:
    pass_number: int
    rule: str
    target: str
    message: str


class IndependentReviewerInstance:
    @staticmethod
    def review_file(filename: str, content: str) -> List[ReviewFinding]:
        \"\"\"Pass 1: Local isolated checks.\"\"\"
        findings = []
        if "except:" in content or "except Exception: pass" in content:
            findings.append(ReviewFinding(
                pass_number=1,
                rule="NO_BARE_EXCEPT",
                target=filename,
                message="Bare except block detected. Specific exceptions must be handled.",
            ))
        return findings


class MultiPassReviewPipeline:
    def __init__(self) -> None:
        self.reviewer = IndependentReviewerInstance()

    def run_review(self, codebase: Dict[str, str]) -> Dict[str, Any]:
        all_findings = []

        # Pass 1: Local File Reviews
        for fname, content in codebase.items():
            all_findings.extend(self.reviewer.review_file(fname, content))

        # Pass 2: Integration Signature Cross-Check
        # Check if caller uses argument name that matches callee definition
        if "auth_api.py" in codebase and "auth_client.py" in codebase:
            api_code = codebase["auth_api.py"]
            client_code = codebase["auth_client.py"]

            # If api defines 'bearer_token' but client passes 'auth_token='
            if "bearer_token:" in api_code and "auth_token=" in client_code:
                all_findings.append(ReviewFinding(
                    pass_number=2,
                    rule="INTERFACE_PARAMETER_MISMATCH",
                    target="auth_client.py -> auth_api.py",
                    message="Call site passes 'auth_token' but target function defines 'bearer_token'.",
                ))

        pass1_count = sum(1 for f in all_findings if f.pass_number == 1)
        pass2_count = sum(1 for f in all_findings if f.pass_number == 2)
        return {
            "approved": len(all_findings) == 0,
            "pass_1_local_count": pass1_count,
            "pass_2_integration_count": pass2_count,
            "findings": all_findings,
        }

print(" MultiPassReviewPipeline initialized.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We test a codebase containing:
- `auth_api.py`: Has bare except (caught in Pass 1).
- `auth_client.py`: Calls `verify_session(auth_token=...)` when API expects `bearer_token` (caught in Pass 2)."""),

        code_cell("""# Step 3: Simulation
codebase_sample = {
    \"auth_api.py\": \"def verify_session(bearer_token: str):\\n    try:\\n        pass\\n    except:\\n        return False\",
    \"auth_client.py\": \"def login():\\n    return verify_session(auth_token='jwt_xyz')\",
}

pipeline = MultiPassReviewPipeline()
report = pipeline.run_review(codebase_sample)

print(\"Review Approved:\", report[\"approved\"])
print(f\"Pass 1 Local Findings: {report['pass_1_local_count']}\")
print(f\"Pass 2 Integration Findings: {report['pass_2_integration_count']}\")
for f in report[\"findings\"]:
    print(f\"  [Pass {f.pass_number}] {f.rule} in {f.target}: {f.message}\")"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Pass 1 flags local bare except.
2. Pass 2 flags cross-module keyword argument mismatch.
3. Review fails approval."""),

        code_cell("""# Step 4: Verification Checks
assert report[\"approved\"] is False
assert report[\"pass_1_local_count\"] >= 1
assert report[\"pass_2_integration_count\"] >= 1

rules = [f.rule for f in report[\"findings\"]]
assert \"NO_BARE_EXCEPT\" in rules
assert \"INTERFACE_PARAMETER_MISMATCH\" in rules

print(\" All verification assertions passed! Multi-pass review verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Local per-file reviews (Pass 1) **cannot** detect interface mismatches between callers and callees.
- **Rule 2**: Cross-file integration reviews (Pass 2) are required to verify contract signatures and shared state.
- **Rule 3**: Combine isolated passes to prevent cognitive overload while catching multi-module regressions."""),
    ]
    return save_notebook("domain4", "ts_4_6_multi_pass_review", cells)


def main():
    print("=== Generating Domain 4 Notebooks (TS 4.1 - TS 4.6) ===")
    build_ts_4_1()
    build_ts_4_2()
    build_ts_4_3()
    build_ts_4_4()
    build_ts_4_5()
    build_ts_4_6()
    print(" Domain 4 notebooks generated successfully!\n")


if __name__ == "__main__":
    main()
