"""
Domain 2 Notebook Generator: Tool Design & MCP Integration (TS 2.1 - TS 2.5).
Generates comprehensive Jupyter notebooks with step-by-step walkthroughs,
offline simulations, and automated verification checks.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.notebook_builder import code_cell, markdown_cell, save_notebook


def build_ts_2_1():
    cells = [
        markdown_cell("""# Domain 2: Tool Design & MCP Integration
## TS 2.1: Design Effective Tool Interfaces with Clear Descriptions and Boundaries
**Certification Focus**: CCAR-F Domain 2 (18% Exam Weight) | **Scenario Alignment**: Scenario 1 (Customer Support Resolution Agent)

---

### 🎯 Key Architectural Principles
1. **Tool Descriptions as Primary Routers**: Claude relies on tool descriptions to decide which tool to call. Ambiguous descriptions cause misrouting between overlapping tools.
2. **Explicit Negative Boundaries**: When two tools have overlapping domains (e.g. `get_customer` vs `lookup_order`), explicitly include `BOUNDARY:` instructions specifying when **NOT** to call the tool.
3. **Parameter Constraints & Formatting**: Specify exact string formats (e.g. `'CUST-XXXX'`, `'ORD-XXXX'`) and provide concrete example queries.
4. **Forced Tool Choice**: Using `tool_choice: {"type": "tool", "name": "get_customer"}` to guarantee customer identity verification precedes any financial lookups."""),

        code_cell("""# Step 1: Environment & Setup
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 2.1 Tool Interface Design.")"""),

        markdown_cell("""### 🛠️ Step 2: Differentiated Tool Declarations with Boundaries
Notice the explicit `BOUNDARY:` directives in both tool descriptions to eliminate misrouting."""),

        code_cell("""# Step 2: Production Tool Schemas
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
                    "description": "Order identifier matching format 'ORD-XXXX'.",
                }
            },
            "required": ["order_id"],
        },
    },
]

# Mock Database
CUSTOMER_DB = {"alice@example.com": {"customer_id": "CUST-101", "name": "Alice Smith", "tier": "Gold"}}
ORDER_DB = {"ORD-9821": {"order_id": "ORD-9821", "customer_id": "CUST-101", "carrier": "FedEx", "status": "In Transit"}}

def dispatch_tool(tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "get_customer":
        ident = inputs.get("identifier", "").strip().lower()
        cust = CUSTOMER_DB.get(ident)
        return {"found": True, "customer": cust} if cust else {"found": False, "isError": True, "errorCategory": "validation"}
    elif tool_name == "lookup_order":
        oid = inputs.get("order_id", "").strip().upper()
        ord_rec = ORDER_DB.get(oid)
        return {"found": True, "order": ord_rec} if ord_rec else {"found": False, "isError": True, "errorCategory": "validation"}
    return {"isError": True, "message": f"Unknown tool: {tool_name}"}

print(" Tool schemas and mock dispatch engine ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We demonstrate how negative boundaries and forced tool choices direct execution cleanly."""),

        code_cell("""# Step 3: Simulation
# Test 1: Customer identity retrieval
res_cust = dispatch_tool("get_customer", {"identifier": "alice@example.com"})
print("Customer Lookup Result:", res_cust)

# Test 2: Order tracking retrieval
res_order = dispatch_tool("lookup_order", {"order_id": "ORD-9821"})
print("Order Lookup Result:", res_order)

# Test 3: Forced tool choice representation
forced_choice = {"type": "tool", "name": "get_customer"}
print("\\nForced Tool Choice configuration payload:", forced_choice)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Both tool descriptions contain explicit negative boundary instructions.
2. Parameter descriptions specify regex/format conventions.
3. Both tool lookups retrieve accurate data."""),

        code_cell("""# Step 4: Verification Checks
get_cust_desc = next(t["description"] for t in TOOLS if t["name"] == "get_customer")
lookup_ord_desc = next(t["description"] for t in TOOLS if t["name"] == "lookup_order")

assert "BOUNDARY: Do NOT call this tool for order tracking" in get_cust_desc
assert "BOUNDARY: Do NOT call this tool for general user profile lookups" in lookup_ord_desc
assert "CUST-XXXX" in get_cust_desc or "CUST-XXXX" in str(TOOLS)
assert "ORD-XXXX" in lookup_ord_desc or "ORD-XXXX" in str(TOOLS)

assert res_cust["found"] is True
assert res_cust["customer"]["customer_id"] == "CUST-101"
assert res_order["order"]["carrier"] == "FedEx"

print(" All verification assertions passed! Tool interfaces verified.")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Tool descriptions must define explicit **negative boundaries** (`BOUNDARY: Do NOT call this tool when...`).
- **Rule 2**: Specify exact parameter format constraints (`CUST-XXXX`) and provide concrete query examples.
- **Rule 3**: Use forced `tool_choice` (`{"type": "tool", "name": "..."}`) when a step is non-negotiable."""),
    ]
    return save_notebook("domain2", "ts_2_1_tool_interface_design", cells)


def build_ts_2_2():
    cells = [
        markdown_cell("""# Domain 2: Tool Design & MCP Integration
## TS 2.2: Implement Structured Error Responses for MCP Tools
**Certification Focus**: CCAR-F Domain 2 (18% Exam Weight) | **Scenario Alignment**: Scenario 1 & 4

---

### 🎯 Key Architectural Principles
1. **The MCP `isError: True` Pattern**: Tool errors should set `isError: true` within the tool result payload rather than throwing uncaught HTTP 500 exceptions.
2. **Error Taxonomy**:
   - `"transient"`: Network timeouts, temporary rate limits -> `isRetryable: true`
   - `"validation"`: Malformed SKU, invalid format -> `isRetryable: false`
   - `"business"`: Policy limit violations (e.g. refund > $500) -> `isRetryable: false`, with user-friendly guidance
   - `"permission"`: Insufficient role/privileges -> `isRetryable: false`
3. **Valid Empty Results vs Access Failures**: A database query that successfully finds 0 matching rows is **not an error** (`isError: false, stock_count: 0, is_empty_result: true`). Returning errors for empty results causes the agent to misdiagnose system health."""),

        code_cell("""# Step 1: Environment & Setup
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 2.2 MCP Structured Errors.")"""),

        markdown_cell("""### 🚨 Step 2: Structured Error Helper & Tool Implementations
We implement `create_mcp_error` and tools demonstrating transient, validation, business, and empty result states."""),

        code_cell("""# Step 2: MCP Error Helper & Tools
def create_mcp_error(category: str, message: str, is_retryable: bool, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    \"\"\"Formats an MCP structured error response conforming to certification standards.\"\"\"
    return {
        \"isError\": True,
        \"errorCategory\": category,  # 'transient' | 'validation' | 'business' | 'permission'
        \"isRetryable\": is_retryable,
        \"message\": message,
        \"details\": details or {},
    }

def query_inventory(sku: str, simulate_mode: Optional[str] = None) -> Dict[str, Any]:
    \"\"\"Simulates warehouse inventory lookups with structured error handling.\"\"\"
    if simulate_mode == \"timeout\":
        return create_mcp_error(\"transient\", \"Warehouse database connection timed out after 3000ms.\", is_retryable=True)
    if not sku.startswith(\"SKU-\"):
        return create_mcp_error(\"validation\", f\"Invalid SKU format '{sku}'. Expected format: SKU-XXXX.\", is_retryable=False)
    if sku == \"SKU-99999\":
        # Valid empty result: NOT an error!
        return {\"isError\": False, \"sku\": sku, \"stock_count\": 0, \"is_empty_result\": True}
    return {\"isError\": False, \"sku\": sku, \"stock_count\": 42, \"is_empty_result\": False}

def issue_refund(customer_id: str, amount: float) -> Dict[str, Any]:
    \"\"\"Simulates refund processing with business policy bounds.\"\"\"
    if amount > 500.0:
        return create_mcp_error(
            \"business\",
            f\"Refund amount ${amount:.2f} exceeds automated policy threshold ($500.00). Escalate to manager.\",
            is_retryable=False,
            details={\"customer_id\": customer_id, \"threshold\": 500.0, \"requested\": amount}
        )
    return {\"isError\": False, \"customer_id\": customer_id, \"refund_amount\": amount, \"status\": \"success\"}

print(\" Structured error engine ready.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We test all 4 primary error/result categories:
1. **Transient Timeout**: Retryable.
2. **Malformed SKU**: Non-retryable validation error.
3. **Valid Empty Result**: Success with 0 items (isError: False).
4. **Policy Cap Breach**: Business rule violation."""),

        code_cell("""# Step 3: Simulation
# 1. Transient Error
res_transient = query_inventory(\"SKU-101\", simulate_mode=\"timeout\")
print(\"Transient Error Result:\", res_transient)

# 2. Validation Error
res_validation = query_inventory(\"INVALID_FORMAT_SKU\")
print(\"\\nValidation Error Result:\", res_validation)

# 3. Valid Empty Result (isError: False!)
res_empty = query_inventory(\"SKU-99999\")
print(\"\\nValid Empty Result:\", res_empty)

# 4. Business Rule Violation
res_business = issue_refund(\"CUST-100\", 650.0)
print(\"\\nBusiness Rule Error Result:\", res_business)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Transient errors have `isRetryable == True`.
2. Validation errors have `isRetryable == False`.
3. Valid empty results have `isError == False`.
4. Business errors have `isRetryable == False` and include details."""),

        code_cell("""# Step 4: Verification Checks
assert res_transient[\"isError\"] is True
assert res_transient[\"errorCategory\"] == \"transient\"
assert res_transient[\"isRetryable\"] is True

assert res_validation[\"isError\"] is True
assert res_validation[\"errorCategory\"] == \"validation\"
assert res_validation[\"isRetryable\"] is False

assert res_empty[\"isError\"] is False
assert res_empty[\"stock_count\"] == 0
assert res_empty[\"is_empty_result\"] is True

assert res_business[\"isError\"] is True
assert res_business[\"errorCategory\"] == \"business\"
assert res_business[\"isRetryable\"] is False

print(\" All verification assertions passed! MCP error taxonomy verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Always return structured errors using `isError: true` with an explicit `errorCategory`.
- **Rule 2**: Mark `isRetryable: true` ONLY for transient infrastructure failures (timeouts, rate limits).
- **Rule 3**: Never return an error for valid empty query results (0 matches). Return `isError: false` and `stock_count: 0`."""),
    ]
    return save_notebook("domain2", "ts_2_2_mcp_structured_errors", cells)


def build_ts_2_3():
    cells = [
        markdown_cell("""# Domain 2: Tool Design & MCP Integration
## TS 2.3: Distribute Tools Appropriately and Configure Tool Choice
**Certification Focus**: CCAR-F Domain 2 (18% Exam Weight) | **Scenario Alignment**: Scenario 4 (Developer Productivity with Claude)

---

### 🎯 Key Architectural Principles
1. **Principle of Least Privilege**: Limit each agent's tool suite to 4–5 specialized tools. Giving agents 20+ tools degrades tool selection accuracy and increases token cost.
2. **Tool Choice Configuration**:
   - `"auto"`: Model freely decides whether to invoke tools or respond directly with text.
   - `"any"`: Model **must** call a tool, but selects which one.
   - `{"type": "tool", "name": "..."}`: Model is strictly forced to call a specific named tool.
3. **Role-Based Tool Distribution**: Coordinator agents receive delegation tools (`Task`), whereas worker agents receive domain-specific tools (`read_file`, `calculator`)."""),

        code_cell("""# Step 1: Environment & Setup
import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 2.3 Tool Distribution & Choice.")"""),

        markdown_cell("""### 🎛️ Step 2: Tool Choice Resolver & Built-in Tools Engine
We implement the tool choice configuration parser and built-in search engine."""),

        code_cell("""# Step 2: Tool Choice Resolver Logic
def resolve_tool_choice_mode(mode_str: str, specific_tool_name: Optional[str] = None) -> Any:
    \"\"\"Resolves user configuration into the official Anthropic tool_choice parameter.\"\"\"
    normalized = mode_str.lower().strip()
    if normalized == \"auto\":
        return \"auto\"
    elif normalized == \"any\":
        return {\"type\": \"any\"}
    elif normalized == \"forced\":
        if not specific_tool_name:
            raise ValueError(\"Forced mode requires specific_tool_name\")
        return {\"type\": \"tool\", \"name\": specific_tool_name}
    raise ValueError(f\"Unknown tool_choice mode: {mode_str}\")


class BuiltinToolsEngine:
    \"\"\"Simulates developer productivity tools (Glob, Grep) over a directory.\"\"\"
    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def glob_files(self, pattern: str) -> List[str]:
        matches = []
        ignore_dirs = {\".git\", \".venv\", \"venv\", \"__pycache__\", \".pytest_cache\", \".mypy_cache\", \".ruff_cache\"}
        for dirpath, dirnames, filenames in os.walk(str(self.root)):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(\".venv\")]
            rel_dir = os.path.relpath(dirpath, str(self.root)).replace(\"\\\\\", \"/\")
            for fname in filenames:
                rel = f\"{rel_dir}/{fname}\" if rel_dir != \".\" else fname
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(fname, pattern):
                    matches.append(rel)
        return sorted(matches)

    def grep_content(self, regex_pattern: str, file_pattern: str = \"*\") -> List[Dict[str, Any]]:
        results = []
        compiled = re.compile(regex_pattern)
        for rel_path in self.glob_files(file_pattern):
            full_path = self.root / rel_path
            try:
                lines = full_path.read_text(encoding=\"utf-8\").splitlines()
                for line_no, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        results.append({\"file\": rel_path, \"line\": line_no, \"content\": line.strip()})
            except Exception:
                continue
        return results

print(\" ToolChoice resolver and BuiltinToolsEngine ready.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We test tool_choice resolution modes and simulate file exploration with glob and grep."""),

        code_cell("""# Step 3: Simulation
# 1. Test tool_choice modes
mode_auto = resolve_tool_choice_mode(\"auto\")
mode_any = resolve_tool_choice_mode(\"any\")
mode_forced = resolve_tool_choice_mode(\"forced\", \"security_audit\")

print(\"tool_choice 'auto':\", mode_auto)
print(\"tool_choice 'any':\", mode_any)
print(\"tool_choice 'forced':\", mode_forced)

# 2. Test BuiltinToolsEngine on repository files
engine = BuiltinToolsEngine(repo_root)
py_files = engine.glob_files(\"*.md\")
print(f\"\\nGlobbed Markdown files in repo root: {len(py_files)} files found.\")

# Grep for CCAR-F mentions in markdown files
grep_res = engine.grep_content(\"CCAR-F\", \"*.md\")
print(f\"Grep matched 'CCAR-F' in {len(grep_res)} line(s).\")"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. `resolve_tool_choice_mode` outputs the exact Anthropic schema.
2. Glob and grep correctly locate files and strings."""),

        code_cell("""# Step 4: Verification Checks
assert mode_auto == \"auto\"
assert mode_any == {\"type\": \"any\"}
assert mode_forced == {\"type\": \"tool\", \"name\": \"security_audit\"}

assert len(py_files) > 0
assert len(grep_res) > 0

print(\" All verification assertions passed! Tool distribution verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Assign focused tool sets (4–5 tools per subagent) conforming to least privilege.
- **Rule 2**: Use `tool_choice: {"type": "tool", "name": "..."}` to force mandatory verification steps.
- **Rule 3**: Combine Glob (file discovery) and Grep (symbol search) for token-efficient codebase exploration."""),
    ]
    return save_notebook("domain2", "ts_2_3_tool_distribution_and_choice", cells)


def build_ts_2_4():
    cells = [
        markdown_cell("""# Domain 2: Tool Design & MCP Integration
## TS 2.4: Integrate MCP Servers into Claude Code and Agent Workflows
**Certification Focus**: CCAR-F Domain 2 (18% Exam Weight) | **Scenario Alignment**: Scenario 4 (Developer Productivity with Claude)

---

### 🎯 Key Architectural Principles
1. **MCP Resources vs Tools**:
   - **Resources**: Read-only, cacheable reference artifacts (e.g. database schema `catalog://schema/orders`, OpenAPI catalogs). Exposing these as Resources eliminates exploratory tool calls.
   - **Tools**: Stateful operations that perform actions or execute queries with dynamic parameters.
2. **Surgical File Editing**: Editing files via string replacement requires exact, unique anchor matches.
3. **Safe Fallback to Read + Write**: If an anchor match is non-unique (ambiguous) or fails, Claude must safely fall back to reading the full file and writing the full updated file."""),

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

print(" Environment initialized for TS 2.4 MCP Server Integration.")"""),

        markdown_cell("""### 📦 Step 2: Simulated MCP Resource Catalog & Safe Edit Function
We implement an MCP service exposing resources and a safe file editing function with fallback detection."""),

        code_cell("""# Step 2: MCP Service & Safe Edit Implementation
class DeveloperMCPService:
    \"\"\"Simulates an MCP service offering read-only Resources and operational Tools.\"\"\"
    RESOURCES = {
        \"catalog://schema/orders\": {
            \"uri\": \"catalog://schema/orders\",
            \"name\": \"Orders Database Schema\",
            \"mimeType\": \"application/json\",
            \"text\": json.dumps({
                \"tables\": {
                    \"orders\": [\"id\", \"customer_id\", \"total_cents\", \"status\", \"created_at\"],
                    \"order_items\": [\"id\", \"order_id\", \"sku\", \"quantity\", \"unit_price_cents\"],
                }
            }),
        },
        \"catalog://docs/api_endpoints\": {
            \"uri\": \"catalog://docs/api_endpoints\",
            \"name\": \"API Route Catalog\",
            \"mimeType\": \"text/markdown\",
            \"text\": \"# Routes\\n- GET /api/v1/orders/{id}\\n- POST /api/v1/orders/{id}/refund\",
        },
    }

    @classmethod
    def read_resource(cls, uri: str) -> Optional[Dict[str, Any]]:
        return cls.RESOURCES.get(uri)

    @classmethod
    def list_resources(cls) -> List[Dict[str, str]]:
        return [{\"uri\": v[\"uri\"], \"name\": v[\"name\"]} for v in cls.RESOURCES.values()]


def safe_edit_file(file_content: str, old_string: str, new_string: str) -> Tuple[bool, str]:
    \"\"\"
    Safely edits file content. Detects non-unique anchors and triggers fallback to Read+Write.
    \"\"\"
    match_count = file_content.count(old_string)
    if match_count == 0:
        return False, \"Anchor string not found. Triggering Read + Write fallback.\"
    if match_count > 1:
        return False, f\"Ambiguous edit: Anchor string found {match_count} times. Triggering Read + Write fallback.\"
    
    updated_content = file_content.replace(old_string, new_string, 1)
    return True, updated_content

print(\" DeveloperMCPService and safe_edit_file ready.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Read catalog schema resource (`catalog://schema/orders`).
2. Perform unique surgical edit -> Success.
3. Attempt ambiguous edit (multiple matches) -> Triggers fallback."""),

        code_cell("""# Step 3: Simulation
# 1. Read MCP Resource
schema_res = DeveloperMCPService.read_resource(\"catalog://schema/orders\")
print(\"MCP Resource Read Result:\", json.loads(schema_res[\"text\"]))

# 2. Successful Unique Edit
code_sample = \"def calculate_tax(amount):\\n    rate = 0.05\\n    return amount * rate\\n\"
ok, new_code = safe_edit_file(code_sample, \"rate = 0.05\", \"rate = 0.08\")
print(\"\\nUnique Edit Status:\", ok)
print(\"Updated Code:\\n\", new_code)

# 3. Ambiguous Edit (fails unique match)
ambiguous_code = \"x = 1\\nx = 1\\n\"
ok_amb, msg = safe_edit_file(ambiguous_code, \"x = 1\", \"x = 2\")
print(\"\\nAmbiguous Edit Status:\", ok_amb)
print(\"Fallback Message:\", msg)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. MCP Resources can be read by URI without tool execution.
2. Unique strings are safely replaced.
3. Ambiguous anchors cleanly reject with a Read+Write fallback notice."""),

        code_cell("""# Step 4: Verification Checks
assert schema_res is not None
assert \"orders\" in schema_res[\"text\"]

assert ok is True
assert \"rate = 0.08\" in new_code

assert ok_amb is False
assert \"Triggering Read + Write fallback\" in msg

print(\" All verification assertions passed! MCP integration validated.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Expose static database schemas and documentation as **MCP Resources**, reserving Tools for active queries and actions.
- **Rule 2**: Surgical file edits require unique anchor matching.
- **Rule 3**: If an anchor match is ambiguous, always fall back to a full **Read + Write** workflow."""),
    ]
    return save_notebook("domain2", "ts_2_4_mcp_server_integration", cells)


def build_ts_2_5():
    cells = [
        markdown_cell("""# Domain 2: Tool Design & MCP Integration
## TS 2.5: Select and Apply Built-in Tools (Read, Write, Edit, Bash, Grep, Glob) Effectively
**Certification Focus**: CCAR-F Domain 2 (18% Exam Weight) | **Scenario Alignment**: Scenario 4 (Developer Productivity with Claude)

---

### 🎯 Key Architectural Principles
1. **Incremental Codebase Discovery**:
   - **Step 1: Glob**: Match candidate file paths (`*.py`, `src/services/**`).
   - **Step 2: Grep**: Search file contents for specific symbols, function signatures, or definitions.
   - **Step 3: Read**: Read targeted slices of files (e.g. lines 10–50) rather than whole files.
2. **Avoiding Context Bloat**: Never read an entire repository upfront. Targeted reading prevents exhausting context windows.
3. **Edit Fallback Strategy**: When `edit_file` fails due to ambiguous anchors, expand the anchor context lines or fall back to full `read_file` + `write_file`."""),

        code_cell("""# Step 1: Environment & Setup
import fnmatch
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 2.5 Built-in Tools Usage.")"""),

        markdown_cell("""### 🧰 Step 2: Built-in Toolbox Engine Implementation
We implement the full suite of built-in developer tools with safe fallback handling."""),

        code_cell("""# Step 2: BuiltinToolbox Implementation
class BuiltinToolbox:
    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def glob_files(self, pattern: str) -> List[str]:
        matches = []
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        for dirpath, dirnames, filenames in os.walk(str(self.root)):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".venv")]
            rel_dir = os.path.relpath(dirpath, str(self.root)).replace("\\\\", "/")
            for fname in filenames:
                rel = f"{rel_dir}/{fname}" if rel_dir != "." else fname
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(fname, pattern):
                    matches.append(rel)
        return sorted(matches)

    def grep_search(self, regex_pattern: str, file_pattern: str = "*") -> List[Dict[str, Any]]:
        results = []
        compiled = re.compile(regex_pattern)
        for rel_path in self.glob_files(file_pattern):
            full_path = self.root / rel_path
            try:
                lines = full_path.read_text(encoding="utf-8").splitlines()
                for line_no, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        results.append({"file": rel_path, "line": line_no, "content": line.strip()})
            except Exception:
                continue
        return results

    def read_file(self, rel_path: str, offset: int = 1, limit: Optional[int] = None) -> Dict[str, Any]:
        full_path = self.root / rel_path
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}
        lines = full_path.read_text(encoding="utf-8").splitlines()
        start_idx = max(0, offset - 1)
        end_idx = len(lines) if limit is None else start_idx + limit
        slice_lines = lines[start_idx:end_idx]
        return {
            "success": True,
            "file": rel_path,
            "start_line": offset,
            "total_lines": len(lines),
            "content": "\\n".join(slice_lines),
        }

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        full_path = self.root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {"success": True, "file": rel_path}

    def edit_file(self, rel_path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        read_res = self.read_file(rel_path)
        if not read_res["success"]:
            return read_res
        content = read_res["content"]
        count = content.count(old_str)
        if count == 0:
            return {"success": False, "error": "Anchor not found."}
        if count > 1:
            return {"success": False, "error": f"Ambiguous edit: found {count} occurrences."}
        updated = content.replace(old_str, new_str, 1)
        self.write_file(rel_path, updated)
        return {"success": True, "file": rel_path}

    def execute_edit_with_fallback(self, rel_path: str, old_str: str, new_str: str, unique_context: str) -> Dict[str, Any]:
        res = self.edit_file(rel_path, old_str, new_str)
        if not res["success"]:
            # Fallback: expand anchor with surrounding unique context
            expanded_old = unique_context
            expanded_new = unique_context.replace(old_str, new_str)
            res_retry = self.edit_file(rel_path, expanded_old, expanded_new)
            if res_retry["success"]:
                return {"status": "EDIT_RETRY_SUCCESS", "details": res_retry}
            # Ultimate fallback: read full file, replace, and write
            read_full = self.read_file(rel_path)
            updated = read_full["content"].replace(old_str, new_str, 1)
            self.write_file(rel_path, updated)
            return {"status": "READ_WRITE_FALLBACK_SUCCESS"}
        return {"status": "DIRECT_EDIT_SUCCESS"}

print(" BuiltinToolbox ready.")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
We create a temporary workspace, write a file with ambiguous targets, trigger the ambiguity failure, and succeed via fallback."""),

        code_cell("""# Step 3: Simulation
with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)
    toolbox = BuiltinToolbox(tmp_path)

    # 1. Write file with repeated text
    sample_content = \"def func_a(): return 1\\ndef func_b(): return 1\\n\"
    toolbox.write_file(\"app.py\", sample_content)

    # 2. Attempt ambiguous edit
    amb_res = toolbox.edit_file(\"app.py\", \"return 1\", \"return 2\")
    print(\"Ambiguous Edit Attempt:\", amb_res)

    # 3. Execute edit with fallback (expanding context to 'def func_a(): return 1')
    fallback_res = toolbox.execute_edit_with_fallback(
        \"app.py\",
        old_str=\"return 1\",
        new_str=\"return 2\",
        unique_context=\"def func_a(): return 1\"
    )
    print(\"\\nFallback Edit Execution:\", fallback_res)

    # 4. Read updated content
    final_content = toolbox.read_file(\"app.py\")
    print(\"\\nUpdated File Content:\\n\", final_content[\"content\"])"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Ambiguous edit fails with clear error.
2. Context expansion fallback replaces only the targeted function.
3. `func_a` returns 2, and `func_b` remains returning 1."""),

        code_cell("""# Step 4: Verification Checks
assert amb_res[\"success\"] is False
assert \"Ambiguous edit\" in amb_res[\"error\"]
assert fallback_res[\"status\"] == \"EDIT_RETRY_SUCCESS\"
assert \"def func_a(): return 2\" in final_content[\"content\"]
assert \"def func_b(): return 1\" in final_content[\"content\"]

print(\" All verification assertions passed! Built-in tools verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Follow the 3-step codebase discovery workflow: **Glob -> Grep -> Read (slices)**.
- **Rule 2**: Avoid dumping whole files into context when only specific functions are needed.
- **Rule 3**: When an edit fails due to ambiguity, expand the unique context lines or fall back to Read + Write."""),
    ]
    return save_notebook("domain2", "ts_2_5_builtin_tools_usage", cells)


def main():
    print("=== Generating Domain 2 Notebooks (TS 2.1 - TS 2.5) ===")
    build_ts_2_1()
    build_ts_2_2()
    build_ts_2_3()
    build_ts_2_4()
    build_ts_2_5()
    print(" Domain 2 notebooks generated successfully!\n")


if __name__ == "__main__":
    main()
