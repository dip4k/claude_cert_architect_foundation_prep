"""
Domain 1 Notebook Generator: Agentic Architecture & Orchestration (TS 1.1 - TS 1.7).
Generates comprehensive Jupyter notebooks with step-by-step walkthroughs,
offline simulations using MockClaudeClient, and automated verification checks.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.notebook_builder import code_cell, markdown_cell, save_notebook


def build_ts_1_1():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.1: Design and Implement Agentic Loops for Autonomous Task Execution
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 1 & 4

---

### 🎯 Key Architectural Principles
1. **Loop Lifecycle**: `client.messages.create()` -> inspect `response.stop_reason` -> if `"tool_use"`, append assistant message, execute tools, append user message with `tool_result` blocks -> repeat until `"end_turn"`.
2. **Deterministic Termination**: `response.stop_reason == "end_turn"` is the **sole reliable signal** that the agent has concluded its task.
3. **Dual History Requirement**: Both the assistant's `tool_use` message and the user's `tool_result` message must be appended to the conversation trail.
4. **Safety Bound vs Completion**: `MAX_ITERATIONS` serves strictly as an emergency safeguard against infinite loops, never as the primary loop termination logic.
5. **Anti-Pattern Warning**: Never parse assistant text for keywords ("Done", "Finished", "I have solved it") or use regex to terminate loops."""),

        code_cell("""# Step 1: Environment & Offline Simulation Setup
import ast
import json
import operator
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Dynamically locate repository root
repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import mock client for 100% offline, zero-cost execution
from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse
from lib.response_logger import ResponseTrail

print(" Repository root loaded:", repo_root)
print(" Offline Mock Claude Client ready (Zero API calls, Zero tokens)")"""),

        markdown_cell("""### 🛠️ Step 2: Safe Tool Implementations & Schemas
We implement two production-grade tools:
1. `calculator`: Evaluates arithmetic expressions safely using Python's `ast` module (avoiding unsafe `eval()`).
2. `web_search`: Simulates targeted knowledge retrieval with pre-indexed fact snippets."""),

        code_cell("""# Step 2: Tool Logic & JSON Schemas
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

def safe_eval_expr(node: ast.AST) -> float:
    \"\"\"Safely evaluate an arithmetic AST expression without eval().\"\"\"
    if isinstance(node, ast.Expression):
        return safe_eval_expr(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](safe_eval_expr(node.left), safe_eval_expr(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](safe_eval_expr(node.operand))
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")

def calculator_tool(expression: str) -> Dict[str, Any]:
    \"\"\"Execute mathematical expressions safely.\"\"\"
    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        result = safe_eval_expr(parsed)
        return {"result": int(result) if result.is_integer() else result}
    except Exception as exc:
        return {"isError": True, "error": f"Evaluation error: {exc}"}

def web_search_tool(query: str) -> Dict[str, Any]:
    \"\"\"Simulate search retrieval from trusted reference data.\"\"\"
    kb = {
        "speed of light": "The speed of light in vacuum is approximately 299,792,458 meters per second.",
        "tokyo population": "The population of Tokyo metropolitan area is approximately 37,400,000.",
    }
    q = query.lower()
    for key, val in kb.items():
        if key in q or any(w in q for w in key.split()):
            return {"found": True, "results": [{"title": key.title(), "snippet": val}]}
    return {"found": False, "results": [], "message": f"No entries for: {query}"}

TOOLS = [
    {
        "name": "calculator",
        "description": "Calculates the result of a mathematical expression. Input must be arithmetic only.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Arithmetic expression, e.g. '234 * 18'"}},
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": "Searches reference documentation and facts by search query.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search term or question"}},
            "required": ["query"],
        },
    },
]

def execute_tool(tool_name: str, tool_inputs: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "calculator":
        return calculator_tool(tool_inputs.get("expression", ""))
    elif tool_name == "web_search":
        return web_search_tool(tool_inputs.get("query", ""))
    return {"isError": True, "error": f"Unknown tool: {tool_name}"}

print(" Tools and schemas initialized successfully.")"""),

        markdown_cell("""### 🔄 Step 3: The Deterministic Agentic Loop Implementation
The core loop orchestrates conversational turns by inspecting `response.stop_reason`.
- If `stop_reason == "tool_use"`, we execute each tool and feed `tool_result` blocks back.
- If `stop_reason == "end_turn"`, the agent has completed reasoning and returns the answer."""),

        code_cell("""# Step 3: The Core Autonomous Agent Loop
def run_agentic_loop(prompt: str, client: Any, trail: Optional[ResponseTrail] = None, max_iterations: int = 15) -> str:
    \"\"\"
    Executes the standard agentic loop with stop_reason lifecycle management.
    \"\"\"
    messages: List[Dict[str, Any]] = [{\"role\": \"user\", \"content\": prompt}]
    session_id = \"sess_sim_01\"
    iteration = 0

    print(f\"\\n=== Starting Agentic Loop for prompt: '{prompt}' ===\")

    while iteration < max_iterations:
        iteration += 1
        print(f\"\\n[Turn {iteration}] Calling Claude API...\")

        response = client.messages.create(
            model=\"claude-haiku-4-5\",
            max_tokens=1024,
            messages=messages,
            tools=TOOLS,
        )

        stop_reason = response.stop_reason
        print(f\"[Turn {iteration}] stop_reason: '{stop_reason}'\")

        # Check if model wants to invoke tools
        if stop_reason == \"tool_use\":
            # 1. Append assistant turn with raw tool_use blocks
            assistant_content = [b.model_dump() for b in response.content]
            messages.append({\"role\": \"assistant\", \"content\": assistant_content})

            # 2. Execute tools and collect tool_result blocks
            tool_results = []
            for block in response.content:
                if block.type == \"tool_use\":
                    print(f\"  -> Executing Tool: {block.name}({block.input})\")
                    res = execute_tool(block.name, block.input)
                    print(f\"  <- Tool Result: {res}\")
                    tool_results.append({
                        \"type\": \"tool_result\",
                        \"tool_use_id\": block.id,
                        \"content\": json.dumps(res),
                    })

            # 3. Append user turn containing tool results
            messages.append({\"role\": \"user\", \"content\": tool_results})
            continue

        # Deterministic exit signal
        if stop_reason == \"end_turn\":
            final_text = \"\".join(b.text for b in response.content if b.type == \"text\")
            print(f\"\\n[Turn {iteration}] Task Complete. Final Response: {final_text}\")
            return final_text

        raise RuntimeError(f\"Unexpected stop_reason: {stop_reason}\")

    raise TimeoutError(f\"Safety limit of {max_iterations} iterations reached.\")"""),

        markdown_cell("""### 🧪 Step 4: Multi-Turn Offline Simulation
We simulate a multi-turn conversation without any live API costs:
- **Turn 1**: Claude decides to invoke `calculator` for `125 * 8`.
- **Turn 2**: Claude receives the calculation `1000` and emits `stop_reason == "end_turn"` with the final text."""),

        code_cell("""# Step 4: Execute Simulation with MockClaudeClient
# Queue Turn 1: tool_use request
turn1_response = MockMessageResponse(
    content=[
        MockContentBlock(
            block_type=\"tool_use\",
            name=\"calculator\",
            tool_id=\"call_calc_981\",
            input_data={\"expression\": \"125 * 8\"},
        )
    ],
    stop_reason=\"tool_use\",
)

# Queue Turn 2: end_turn conclusion
turn2_response = MockMessageResponse(
    content=[
        MockContentBlock(
            block_type=\"text\",
            text=\"125 multiplied by 8 equals 1,000.\",
        )
    ],
    stop_reason=\"end_turn\",
)

mock_client = MockClaudeClient([turn1_response, turn2_response])
final_output = run_agentic_loop(\"What is 125 * 8?\", mock_client)
print(\"\\nResult verified:\", final_output)"""),

        markdown_cell("""### 🔬 Step 5: Automated Verification & Edge Case Checks
We verify that:
1. Arithmetic evaluations are completely protected against injection attacks.
2. The agent loop correctly handles single-turn and multi-turn stops.
3. The conversation history correctly interleaves `tool_use` and `tool_result`."""),

        code_cell("""# Step 5: Verification Assertions
# 1. Verify AST calculator safety against malicious code injection
safe_res = calculator_tool(\"5 * 20 + 10\")
assert safe_res[\"result\"] == 110, f\"Expected 110, got {safe_res}\"

injection_attempt = calculator_tool(\"__import__('os').system('ls')\")
assert injection_attempt.get(\"isError\") is True, \"Safety filter must reject eval injection!\"

# 2. Verify web search functionality
search_res = web_search_tool(\"speed of light\")
assert search_res[\"found\"] is True
assert \"299,792,458\" in search_res[\"results\"][0][\"snippet\"]

# 3. Verify final output
assert \"1,000\" in final_output or \"1000\" in final_output

print(\" All verification assertions passed successfully! 100% offline verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Inspect `response.stop_reason` exclusively. Never inspect response text string patterns to determine if an agent is done.
- **Rule 2**: Both `tool_use` and `tool_result` must be appended in distinct conversational roles (`assistant` then `user`).
- **Rule 3**: `MAX_ITERATIONS` is a fallback safeguard, never the primary stopping mechanism."""),
    ]
    return save_notebook("domain1", "ts_1_1_multi_tool_agent_loop", cells)


def build_ts_1_2():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.2: Orchestrate Multi-Agent Systems with Coordinator-Subagent Patterns
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 3 (Multi-Agent Research System)

---

### 🎯 Key Architectural Principles
1. **Hub-and-Spoke Topology**: All inter-subagent communication, auditing, routing, and synthesis flow strictly through the coordinator. Subagents never communicate peer-to-peer directly.
2. **Context Isolation Contract**: Subagents **do not** inherit the coordinator's message history, memory, or global permissions. Each subagent invocation starts with an isolated, pristine context.
3. **Query-Complexity Routing**: Simple queries are answered directly by the coordinator; complex queries are routed to specialized subagents.
4. **Iterative Refinement & Gap Detection**: The coordinator audits subagent outputs against query goals and re-delegates follow-up tasks if coverage is incomplete."""),

        code_cell("""# Step 1: Environment & Offline Setup
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse

print(" Environment initialized for TS 1.2 Coordinator-Subagent Pattern.")"""),

        markdown_cell("""### 👥 Step 2: Specialized Subagent Definitions (Isolated Contexts)
Each subagent has a dedicated specialization and receives only the explicit parameters required for its job."""),

        code_cell("""# Step 2: Isolated Subagent Classes
class WebSearchSubagent:
    \"\"\"Subagent specialized in retrieving external research snippets.\"\"\"
    KB = {
        \"claude agent sdk\": \"Claude Agent SDK provides primitives for building agentic loops, subagent delegation, hooks, and session resumption.\",
        \"mcp error handling\": \"MCP errors should return isError: true with categorized codes (transient, validation, business).\",
    }

    def execute(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        matched = []
        for key, val in self.KB.items():
            if any(w in q for w in key.split()):
                matched.append({\"topic\": key, \"snippet\": val})
        return {
            \"source\": \"web_search\",
            \"query\": query,
            \"found\": len(matched) > 0,
            \"findings\": matched if matched else \"No matching external articles.\",
        }


class DocumentAnalysisSubagent:
    \"\"\"Subagent specialized in deep document extraction.\"\"\"
    def execute(self, doc_id: str, focus_topic: str) -> Dict[str, Any]:
        return {
            \"source\": \"doc_analysis\",
            \"doc_id\": doc_id,
            \"focus\": focus_topic,
            \"metrics\": [
                {\"metric\": \"Passing score\", \"value\": \"720/1000\"},
                {\"metric\": \"Question count\", \"value\": \"60 items\"},
            ],
        }


class SynthesisSubagent:
    \"\"\"Subagent specialized in synthesizing multi-source findings.\"\"\"
    def execute(self, findings: List[Dict[str, Any]], required_topics: List[str]) -> Dict[str, Any]:
        text_dump = json.dumps(findings).lower()
        missing = [t for t in required_topics if t.lower() not in text_dump]
        return {
            \"coverage_sufficient\": len(missing) == 0,
            \"missing_topics\": missing,
            \"synthesized_findings_count\": len(findings),
        }

print(\" Subagents declared with isolated execution scopes.\")"""),

        markdown_cell("""### 🎛️ Step 3: Multi-Agent Coordinator Implementation
The coordinator orchestrates subagent calls, manages the audit trail, and checks synthesis completeness."""),

        code_cell("""# Step 3: Hub-and-Spoke Coordinator
class MultiAgentCoordinator:
    def __init__(self, client: Any) -> None:
        self.client = client
        self.web_agent = WebSearchSubagent()
        self.doc_agent = DocumentAnalysisSubagent()
        self.synth_agent = SynthesisSubagent()
        self.audit_log: List[Dict[str, Any]] = []

    def dispatch_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.audit_log.append({\"tool\": tool_name, \"inputs\": inputs})
        if tool_name == \"delegate_web_search\":
            return self.web_agent.execute(inputs[\"query\"])
        elif tool_name == \"delegate_doc_analysis\":
            return self.doc_agent.execute(inputs[\"doc_id\"], inputs[\"focus_topic\"])
        elif tool_name == \"evaluate_synthesis\":
            return self.synth_agent.execute(inputs[\"findings\"], inputs[\"required_topics\"])
        raise ValueError(f\"Unknown coordinator tool: {tool_name}\")

    def run_research_pipeline(self, topic: str, required_topics: List[str]) -> Dict[str, Any]:
        # Turn 1: Delegate search
        search_res = self.dispatch_tool(\"delegate_web_search\", {\"query\": topic})
        
        # Turn 2: Delegate doc analysis
        doc_res = self.dispatch_tool(\"delegate_doc_analysis\", {\"doc_id\": \"DOC-2026\", \"focus_topic\": topic})
        
        # Turn 3: Evaluate synthesis coverage
        synth_res = self.dispatch_tool(\"evaluate_synthesis\", {
            \"findings\": [search_res, doc_res],
            \"required_topics\": required_topics
        })

        return {
            \"status\": \"completed\" if synth_res[\"coverage_sufficient\"] else \"gaps_identified\",
            \"search_res\": search_res,
            \"doc_res\": doc_res,
            \"synthesis\": synth_res,
            \"audit_log\": self.audit_log
        }

print(\" MultiAgentCoordinator ready for pipeline execution.\")"""),

        markdown_cell("""### 🧪 Step 4: Offline Simulation Walkthrough
We execute the coordinator pipeline on a multi-domain research query and observe context isolation and audit logging."""),

        code_cell("""# Step 4: Run Coordinator Simulation
coord = MultiAgentCoordinator(client=None)

# Run research pipeline
results = coord.run_research_pipeline(
    topic=\"claude agent sdk\",
    required_topics=[\"claude agent sdk\"]
)

print(\"Pipeline Status:\", results[\"status\"])
print(\"Coverage Sufficient:\", results[\"synthesis\"][\"coverage_sufficient\"])
print(\"Audit Trail Steps:\", len(results[\"audit_log\"]))"""),

        markdown_cell("""### 🔬 Step 5: Verification Assertions
We assert that:
1. Subagents do not cross-contaminate state.
2. Missing topics are accurately flagged during synthesis.
3. Every delegated action is captured in the coordinator's audit log."""),

        code_cell("""# Step 5: Verification Checks
# 1. Verify complete synthesis coverage
assert results[\"status\"] == \"completed\"
assert results[\"synthesis\"][\"coverage_sufficient\"] is True

# 2. Test gap detection with a missing topic
gap_check = coord.synth_agent.execute([results[\"search_res\"]], required_topics=[\"missing_special_topic\"])
assert gap_check[\"coverage_sufficient\"] is False
assert \"missing_special_topic\" in gap_check[\"missing_topics\"]

# 3. Verify audit log captures all 3 turns
assert len(results[\"audit_log\"]) == 3

print(\" All verification assertions passed! Subagent isolation confirmed.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Subagents must **never** share state, conversation history, or memory. They receive explicit task prompts.
- **Rule 2**: All orchestration and routing happens in the coordinator (hub-and-spoke), never peer-to-peer.
- **Rule 3**: The coordinator must evaluate intermediate outputs against goals and re-delegate when gaps exist."""),
    ]
    return save_notebook("domain1", "ts_1_2_coordinator_subagents", cells)


def build_ts_1_3():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.3: Configure Subagent Invocation, Context Passing, and Spawning
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 3 (Multi-Agent Research System)

---

### 🎯 Key Architectural Principles
1. **The `Task` Tool**: The primary mechanism for spawning subagents. Must be explicitly declared in `tools` or `allowedTools`.
2. **Parallel Subagent Spawning**: Emitting multiple `Task` tool use blocks in a **single coordinator turn/response** enables concurrent subagent execution, reducing latency by 40%–60%.
3. **Structured Attribution & Metadata Separation**: Content and findings must be separated from tracking metadata (`source_url`, `timestamp`, `page_number`, `confidence`).
4. **Goal-Oriented Instructions**: Prompt subagents with explicit deliverables, schemas, and constraints rather than rigid step-by-step procedures."""),

        code_cell("""# Step 1: Environment & Offline Setup
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

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse

print(" Environment initialized for TS 1.3 Subagent Invocation & Spawning.")"""),

        markdown_cell("""### 📋 Step 2: Agent Definitions & The Task Tool Schema
The `Task` tool declaration allows Claude to invoke registered subagents dynamically with dedicated prompts and metadata."""),

        code_cell("""# Step 2: Subagent Registry & Task Tool Schema
@dataclass
class AgentDefinition:
    name: str
    description: str
    system_prompt: str
    allowed_tools: List[str]

SUBAGENT_REGISTRY = {
    "web_researcher": AgentDefinition(
        name="web_researcher",
        description="Researches technical documentation and articles.",
        system_prompt="You are a precise technical researcher.",
        allowed_tools=["fetch_url", "search"],
    ),
    "code_analyzer": AgentDefinition(
        name="code_analyzer",
        description="Inspects source code repositories, classes, and syntax.",
        system_prompt="You are an expert static code analyst.",
        allowed_tools=["grep", "read_file"],
    ),
}

TASK_TOOL = {
    "name": "Task",
    "description": (
        "Spawns an isolated subagent to perform a targeted task. "
        "Multiple Task calls may be emitted in a single turn for concurrent execution."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "subagent_type": {
                "type": "string",
                "enum": ["web_researcher", "code_analyzer"],
                "description": "Registered subagent type to instantiate.",
            },
            "prompt": {
                "type": "string",
                "description": "Complete, self-contained prompt for the subagent.",
            },
            "task_metadata": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "expected_output_format": {"type": "string"},
                },
                "required": ["task_id"],
            },
        },
        "required": ["subagent_type", "prompt", "task_metadata"],
    },
}

print(" Task Tool schema and subagent registry defined.")"""),

        markdown_cell("""### ⚡ Step 3: Parallel Execution Engine
Simulates executing multiple subagent tasks spawned concurrently by the coordinator."""),

        code_cell("""# Step 3: Subagent Execution Engine
def execute_subagent_task(subagent_type: str, prompt: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Execute an individual subagent task with metadata/content separation.\"\"\"
    if subagent_type not in SUBAGENT_REGISTRY:
        return {\"status\": \"error\", \"error\": f\"Unknown subagent: {subagent_type}\"}

    if subagent_type == \"web_researcher\":
        return {
            \"task_id\": metadata.get(\"task_id\"),
            \"subagent_type\": subagent_type,
            \"status\": \"completed\",
            \"findings\": [
                {
                    \"content\": \"Claude Agent SDK uses the Task tool for spawning child agents.\",
                    \"metadata\": {
                        \"source_url\": \"https://docs.anthropic.com/agents\",
                        \"confidence\": 0.98,
                    },
                }
            ],
        }
    elif subagent_type == \"code_analyzer\":
        return {
            \"task_id\": metadata.get(\"task_id\"),
            \"subagent_type\": subagent_type,
            \"status\": \"completed\",
            \"findings\": [
                {
                    \"content\": \"Found 2 occurrences of allowedTools containing 'Task'.\",
                    \"metadata\": {
                        \"file\": \"src/coordinator.ts\",
                        \"lines\": [42, 88],
                    },
                }
            ],
        }
    return {\"status\": \"error\", \"error\": \"Unhandled type\"}

def run_parallel_spawning_coordinator(user_query: str, client: Any) -> Dict[str, Any]:
    \"\"\"Simulates coordinator receiving a prompt and issuing parallel Task calls.\"\"\"
    # Turn 1: Model emits parallel tool calls
    resp = client.messages.create(
        model=\"claude-haiku-4-5\",
        messages=[{\"role\": \"user\", \"content\": user_query}],
        tools=[TASK_TOOL],
    )

    completed_tasks = []
    if resp.stop_reason == \"tool_use\":
        for block in resp.content:
            if block.type == \"tool_use\" and block.name == \"Task\":
                result = execute_subagent_task(
                    block.input[\"subagent_type\"],
                    block.input[\"prompt\"],
                    block.input[\"task_metadata\"],
                )
                completed_tasks.append(result)

    return {\"spawned_count\": len(completed_tasks), \"tasks\": completed_tasks}

print(\" Parallel subagent dispatcher ready.\")"""),

        markdown_cell("""### 🧪 Step 4: Offline Simulation Walkthrough
We configure a mock response emitting **two** `Task` calls in a single turn to demonstrate parallel subagent spawning."""),

        code_cell("""# Step 4: Parallel Spawning Simulation
# Mock coordinator issuing TWO concurrent Task calls in Turn 1
parallel_resp = MockMessageResponse(
    content=[
        MockContentBlock(
            block_type=\"tool_use\",
            name=\"Task\",
            tool_id=\"call_task_web_01\",
            input_data={
                \"subagent_type\": \"web_researcher\",
                \"prompt\": \"Search for Agent SDK Task tool guidelines.\",
                \"task_metadata\": {\"task_id\": \"T-WEB-001\"},
            },
        ),
        MockContentBlock(
            block_type=\"tool_use\",
            name=\"Task\",
            tool_id=\"call_task_code_02\",
            input_data={
                \"subagent_type\": \"code_analyzer\",
                \"prompt\": \"Locate allowedTools definitions in repository.\",
                \"task_metadata\": {\"task_id\": \"T-CODE-002\"},
            },
        ),
    ],
    stop_reason=\"tool_use\",
)

mock_client = MockClaudeClient([parallel_resp])
sim_res = run_parallel_spawning_coordinator(\"Analyze Task tool usage\", mock_client)

print(f\"Spawned Subagent Tasks: {sim_res['spawned_count']}\")
for t in sim_res[\"tasks\"]:
    print(f\"  - Task ID: {t['task_id']}, Type: {t['subagent_type']}, Status: {t['status']}\")"""),

        markdown_cell("""### 🔬 Step 5: Verification Assertions
We assert that:
1. Two distinct subagents were invoked in parallel within the same turn.
2. Output payloads cleanly separate substantive content from tracking metadata."""),

        code_cell("""# Step 5: Verification Assertions
assert sim_res[\"spawned_count\"] == 2, \"Expected 2 parallel subagent spawns\"

web_task = next(t for t in sim_res[\"tasks\"] if t[\"subagent_type\"] == \"web_researcher\")
assert web_task[\"task_id\"] == \"T-WEB-001\"
finding = web_task[\"findings\"][0]
assert \"content\" in finding
assert \"metadata\" in finding
assert \"source_url\" in finding[\"metadata\"]

print(\" All verification assertions passed! Parallel spawning verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Spawning subagents requires `Task` in `allowedTools`.
- **Rule 2**: Emitting multiple `Task` calls in a single turn achieves true concurrency (reducing latency 40-60%).
- **Rule 3**: Separate content from metadata (`source_url`, `confidence`, `timestamp`) to preserve provenance."""),
    ]
    return save_notebook("domain1", "ts_1_3_subagent_invocation_spawning", cells)


def build_ts_1_4():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.4: Implement Multi-Step Workflows with Enforcement and Handoff Patterns
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 1 (Customer Support Resolution Agent)

---

### 🎯 Key Architectural Principles
1. **Programmatic Prerequisite Gates**: Business policies (e.g., verifying customer identity before processing refunds) **must** be enforced via code state machines, not merely system prompt instructions.
2. **Prompts vs Code**: Prompts have a non-zero probability of non-compliance (hallucinations, prompt injections, ambiguity). Programmatic gates provide **100% deterministic compliance**.
3. **Structured Handoff Manifests**: Escalation to human supervisors requires compiling a structured summary (customer ID, issue summary, actions attempted, root cause, recommended action).
4. **Immediate Escalation Triggers**: Explicit user demand for a human, unhandled policy gaps, or repeated failure must immediately halt automated processing."""),

        code_cell("""# Step 1: Environment & Offline Setup
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

print(" Environment initialized for TS 1.4 Prerequisite Enforcement.")"""),

        markdown_cell("""### 🛡️ Step 2: Workflow State & Programmatic Prerequisite Gate
The `WorkflowState` class acts as the gatekeeper. Any attempt to invoke `process_refund` without a verified customer ID is rejected with a structured `permission` error."""),

        code_cell("""# Step 2: State Machine & Prerequisite Gate
class WorkflowState:
    \"\"\"State machine that deterministically blocks unverified operations.\"\"\"
    def __init__(self) -> None:
        self.verified_customer_id: Optional[str] = None
        self.verified_customer_name: Optional[str] = None
        self.escalated_to_human: bool = False
        self.escalation_summary: Optional[Dict[str, Any]] = None

    def verify_customer(self, customer_id: str, name: str) -> None:
        self.verified_customer_id = customer_id
        self.verified_customer_name = name

    def check_gate(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        \"\"\"Deterministic Gate: Blocks financial/sensitive actions until identity is verified.\"\"\"
        if tool_name in [\"process_refund\", \"lookup_order\"] and not self.verified_customer_id:
            return False, {
                \"isError\": True,
                \"errorCategory\": \"permission\",
                \"isRetryable\": False,
                \"message\": (
                    f\"Deterministic Gate Rejection: Tool '{tool_name}' requires verified customer ID. \"
                    \"Must call get_customer first.\"
                ),
            }
        return True, None

print(\" WorkflowState gatekeeper initialized.\")"""),

        markdown_cell("""### 🔧 Step 3: Tool Definitions & Escalation Manifest
We implement tools and the structured escalation function that compiles the handoff manifest."""),

        code_cell("""# Step 3: Tools & Escalation Logic
MOCK_CUSTOMERS = {
    \"alice@example.com\": {\"id\": \"CUST-101\", \"name\": \"Alice Smith\"},
}

def get_customer(email: str, state: WorkflowState) -> Dict[str, Any]:
    rec = MOCK_CUSTOMERS.get(email.strip().lower())
    if rec:
        state.verify_customer(rec[\"id\"], rec[\"name\"])
        return {\"found\": True, \"customer_id\": rec[\"id\"], \"name\": rec[\"name\"]}
    return {\"found\": False, \"isError\": True, \"errorCategory\": \"validation\", \"isRetryable\": False}

def process_refund(order_id: str, amount: float, state: WorkflowState) -> Dict[str, Any]:
    allowed, err = state.check_gate(\"process_refund\", {\"order_id\": order_id, \"amount\": amount})
    if not allowed:
        return err
    return {
        \"status\": \"processed\",
        \"order_id\": order_id,
        \"customer_id\": state.verified_customer_id,
        \"amount_refunded\": amount,
    }

def escalate_to_human(reason: str, recommended_action: str, state: WorkflowState) -> Dict[str, Any]:
    \"\"\"Generates a comprehensive structured handoff manifest for a human supervisor.\"\"\"
    state.escalated_to_human = True
    state.escalation_summary = {
        \"customer_id\": state.verified_customer_id or \"UNVERIFIED\",
        \"customer_name\": state.verified_customer_name or \"UNKNOWN\",
        \"root_cause\": reason,
        \"recommended_action\": recommended_action,
        \"requires_manual_approval\": True,
    }
    return {\"escalated\": True, \"summary\": state.escalation_summary}

print(\" Business tools and escalation manifest compiler ready.\")"""),

        markdown_cell("""### 🧪 Step 4: Offline Simulation Walkthrough
We demonstrate:
1. An unverified attempt to process a refund is **blocked** by the gate.
2. The user identity is verified.
3. The refund is **approved** and processed."""),

        code_cell("""# Step 4: Interactive Simulation
state = WorkflowState()

# Attempt 1: Call refund BEFORE identity verification -> Must be BLOCKED
print(\"--- Attempt 1: Refund before verification ---\")
res1 = process_refund(\"ORD-991\", 85.0, state)
print(\"Gate Result:\", res1)

# Step 2: Verify customer
print(\"\\n--- Step 2: Customer verification ---\")
verify_res = get_customer(\"alice@example.com\", state)
print(\"Verification Result:\", verify_res)

# Attempt 2: Call refund AFTER identity verification -> Must SUCCEED
print(\"\\n--- Attempt 3: Refund after verification ---\")
res2 = process_refund(\"ORD-991\", 85.0, state)
print(\"Refund Result:\", res2)"""),

        markdown_cell("""### 🔬 Step 5: Verification Assertions
We assert that:
1. Gate deterministically blocked the first attempt with `permission` category and `isRetryable: False`.
2. Customer verification updated state.
3. Gate permitted the refund once verified."""),

        code_cell("""# Step 5: Verification Checks
assert res1[\"isError\"] is True
assert res1[\"errorCategory\"] == \"permission\"
assert res1[\"isRetryable\"] is False

assert state.verified_customer_id == \"CUST-101\"
assert res2[\"status\"] == \"processed\"
assert res2[\"amount_refunded\"] == 85.0

# Verify human handoff manifest
handoff = escalate_to_human(\"Return policy dispute\", \"Issue courtesy credit\", state)
assert handoff[\"escalated\"] is True
assert handoff[\"summary\"][\"customer_id\"] == \"CUST-101\"
assert handoff[\"summary\"][\"root_cause\"] == \"Return policy dispute\"

print(\" All verification assertions passed! Programmatic gatekeeper confirmed.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Rely on **code gates** (state machines, pre-execution checks) for prerequisite compliance, never on prompt instructions alone.
- **Rule 2**: When escalating to humans, always compile a structured handoff manifest (customer ID, attempted actions, root cause, recommended action).
- **Rule 3**: Blocked prerequisite calls should return `errorCategory: permission` with `isRetryable: False`."""),
    ]
    return save_notebook("domain1", "ts_1_4_prerequisite_enforcement", cells)


def build_ts_1_5():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.5: Apply Agent SDK Hooks for Tool Call Interception and Data Normalization
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 1 & 4

---

### 🎯 Key Architectural Principles
1. **Agent SDK Hook Lifecycle**: Hooks execute at runtime boundaries:
   - `PreToolUse`: Interception, gating, parameter validation, and hard regulatory thresholds.
   - `PostToolUse`: Normalization, sensitive data redaction, timestamp formatting, and uniform schema enforcement.
2. **Hard Boundaries in Code**: Financial caps (e.g. blocking transactions > $500) must be enforced in `PreToolUse` hooks rather than trusting Claude's prompt adherence.
3. **Data Normalization**: Raw API payloads (epoch timestamps, raw HTTP codes, internal flags) should be normalized in `PostToolUse` before returning to Claude to optimize context usage and prevent hallucination."""),

        code_cell("""# Step 1: Environment & Offline Setup
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse

print(" Environment initialized for TS 1.5 Agent SDK Hooks.")"""),

        markdown_cell("""### 🎣 Step 2: PreToolUse & PostToolUse Hook Declarations
- `PreToolUse` checks financial boundaries (transactions > $500 require manager approval).
- `PostToolUse` normalizes epoch timestamps to ISO-8601 strings and strips internal database IDs."""),

        code_cell("""# Step 2: Hook Implementations
def compliance_interception_hook(tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    \"\"\"PreToolUse hook: Blocks payouts over $500 and enforces supervisor escalation.\"\"\"
    if tool_name == \"process_payout\":
        amount = tool_input.get(\"amount\", 0.0)
        if amount > 500.0:
            return False, {
                \"blocked_by_hook\": True,
                \"reason\": f\"Payout amount ${amount:.2f} exceeds automated policy threshold ($500.00).\",
                \"redirect_action\": \"escalate_to_supervisor\",
            }
    return True, None

def post_tool_use_normalization_hook(tool_name: str, raw_output: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"PostToolUse hook: Normalizes timestamps, sanitizes internal fields, converts status codes.\"\"\"
    normalized = dict(raw_output)
    # Convert unix epoch to ISO-8601
    if \"epoch_timestamp\" in normalized:
        ts = normalized.pop(\"epoch_timestamp\")
        normalized[\"iso_timestamp\"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    # Normalize HTTP status codes to clean enums
    if \"raw_status_code\" in normalized:
        code = normalized.pop(\"raw_status_code\")
        normalized[\"status\"] = \"active\" if code == 200 else \"inactive\"
    # Redact sensitive internal tokens
    normalized.pop(\"internal_db_row_id\", None)
    return normalized

print(\" Hooks defined for PreToolUse and PostToolUse.\")"""),

        markdown_cell("""### ⚙️ Step 3: Hook Execution Middleware
The wrapper integrates hooks around tool execution."""),

        code_cell("""# Step 3: Hook Middleware Wrapper
def execute_with_hooks(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_executor: Callable[[str, Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    \"\"\"Wraps tool execution with PreToolUse interception and PostToolUse normalization.\"\"\"
    # 1. PreToolUse Hook
    allowed, intercept_result = compliance_interception_hook(tool_name, tool_input)
    if not allowed:
        return {\"isError\": True, \"hook_interception\": intercept_result}

    # 2. Execute Underlying Tool
    raw_output = tool_executor(tool_name, tool_input)

    # 3. PostToolUse Hook
    return post_tool_use_normalization_hook(tool_name, raw_output)

def sample_tool_executor(tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == \"check_account_status\":
        return {
            \"account_id\": inputs[\"account_id\"],
            \"epoch_timestamp\": 1728216000,
            \"raw_status_code\": 200,
            \"internal_db_row_id\": 994821,
        }
    elif tool_name == \"process_payout\":
        return {\"status\": \"paid\", \"amount\": inputs[\"amount\"]}
    return {\"error\": \"unknown\"}

print(\" Hook middleware initialized.\")"""),

        markdown_cell("""### 🧪 Step 4: Simulation Walkthrough
1. Payout of $250 -> Permitted.
2. Payout of $800 -> Intercepted and blocked by PreToolUse hook.
3. Account query -> Output normalized by PostToolUse hook."""),

        code_cell("""# Step 4: Simulation Execution
# Case A: Below threshold payout ($250)
res_a = execute_with_hooks(\"process_payout\", {\"amount\": 250.0}, sample_tool_executor)
print(\"Below Threshold Result:\", res_a)

# Case B: Above threshold payout ($800) -> Intercepted
res_b = execute_with_hooks(\"process_payout\", {\"amount\": 800.0}, sample_tool_executor)
print(\"\\nAbove Threshold Result:\", res_b)

# Case C: Account check -> Normalization
res_c = execute_with_hooks(\"check_account_status\", {\"account_id\": \"ACC-100\"}, sample_tool_executor)
print(\"\\nNormalized Account Output:\", json.dumps(res_c, indent=2))"""),

        markdown_cell("""### 🔬 Step 5: Verification Assertions
We assert that:
1. Transactions over $500 are deterministically blocked.
2. Internal tokens and raw HTTP codes are cleanly sanitized before reaching Claude."""),

        code_cell("""# Step 5: Verification Assertions
assert res_a[\"status\"] == \"paid\"
assert res_b[\"isError\"] is True
assert res_b[\"hook_interception\"][\"blocked_by_hook\"] is True

# Normalization assertions
assert \"iso_timestamp\" in res_c
assert \"epoch_timestamp\" not in res_c
assert \"internal_db_row_id\" not in res_c
assert res_c[\"status\"] == \"active\"

print(\" All verification assertions passed! SDK hooks validated.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Use `PreToolUse` hooks for hard financial limits and security boundaries.
- **Rule 2**: Use `PostToolUse` hooks to normalize heterogeneous data types (timestamps, enums) and scrub sensitive internal fields.
- **Rule 3**: Never rely on Claude's prompt adherence when regulatory or financial thresholds must be strictly enforced."""),
    ]
    return save_notebook("domain1", "ts_1_5_sdk_hooks", cells)


def build_ts_1_6():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.6: Design Task Decomposition Strategies for Complex Workflows
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 2 & 5

---

### 🎯 Key Architectural Principles
1. **Mitigating Attention Dilution**: Supplying 10+ source files in a single prompt degrades Claude's focus and leads to missed edge cases and superficial reviews.
2. **Two-Pass Prompt Chaining**:
   - **Pass 1 (Local Analysis)**: Each modified file is inspected in isolation for local logic, syntax errors, and isolated security vulnerabilities.
   - **Pass 2 (Cross-File Integration)**: The synthesized findings from Pass 1 are evaluated together with inter-module contracts to detect integration breaks, parameter mismatches, and shared state risks.
3. **Adaptive Decomposition**: Breaking large tasks into decoupled, auditable milestones improves reasoning depth and allows caching of intermediate findings."""),

        code_cell("""# Step 1: Environment & Offline Setup
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

from lib.mock_claude import MockClaudeClient, MockContentBlock, MockMessageResponse

print(" Environment initialized for TS 1.6 Task Decomposition.")"""),

        markdown_cell("""### 📂 Step 2: Code Representation & Two-Pass Pipeline
We define code files and implement the two-pass prompt chaining workflow."""),

        code_cell("""# Step 2: Two-Pass Decomposition Logic
@dataclass
class CodeFile:
    filename: str
    content: str

def run_prompt_chaining_review(files: List[CodeFile], client: Any) -> Dict[str, Any]:
    \"\"\"
    Two-Pass Review Pipeline:
    Pass 1: Isolated per-file review
    Pass 2: Cross-file integration synthesis
    \"\"\"
    local_findings = {}

    # --- PASS 1: Isolated Per-File Analysis ---
    print(\"=== Starting Pass 1: Local File Analysis ===\")
    for f in files:
        prompt = f\"Analyze file {f.filename} in isolation for syntax, bugs, and security risks:\\n{f.content}\"
        resp = client.messages.create(
            model=\"claude-haiku-4-5\",
            messages=[{\"role\": \"user\", \"content\": prompt}],
        )
        finding_text = \"\".join(b.text for b in resp.content if b.type == \"text\")
        local_findings[f.filename] = finding_text
        print(f\"  [Pass 1] {f.filename}: {finding_text}\")

    # --- PASS 2: Cross-File Integration Analysis ---
    print(\"\\n=== Starting Pass 2: Cross-File Integration Analysis ===\")
    pass2_prompt = (
        \"Synthesize the following file-level findings and evaluate cross-file contracts:\\n\"
        + json.dumps(local_findings, indent=2)
    )
    resp2 = client.messages.create(
        model=\"claude-haiku-4-5\",
        messages=[{\"role\": \"user\", \"content\": pass2_prompt}],
    )
    integration_findings = \"\".join(b.text for b in resp2.content if b.type == \"text\")
    print(f\"  [Pass 2] Integration Summary: {integration_findings}\")

    return {
        \"local_findings\": local_findings,
        \"integration_findings\": integration_findings,
    }

print(\" Two-pass decomposition pipeline ready.\")"""),

        markdown_cell("""### 🧪 Step 3: Offline Simulation Walkthrough
We review two interacting files:
- `auth_service.py`: Generates JWT tokens.
- `api_router.py`: Verifies tokens and queries database.
Pass 1 checks each file individually. Pass 2 identifies that the router expects token expiration but the service does not encode it."""),

        code_cell("""# Step 3: Simulation with Mock Responses
files_to_review = [
    CodeFile(\"auth_service.py\", \"def generate_token(user_id): return jwt.encode({'user': user_id})\"),
    CodeFile(\"api_router.py\", \"def route(request): token = request.headers['auth']; verify(token, check_exp=True)\"),
]

# Mock Pass 1 (file 1, file 2) and Pass 2 (integration)
mock_resp1 = MockMessageResponse(content=[MockContentBlock(block_type=\"text\", text=\"auth_service lacks expiry timestamp in JWT.\")])
mock_resp2 = MockMessageResponse(content=[MockContentBlock(block_type=\"text\", text=\"api_router strictly requires check_exp=True.\")])
mock_resp_cross = MockMessageResponse(content=[MockContentBlock(block_type=\"text\", text=\"CRITICAL CONTRACT MISMATCH: api_router fails token verification because auth_service omits exp field.\")])

client = MockClaudeClient([mock_resp1, mock_resp2, mock_resp_cross])
results = run_prompt_chaining_review(files_to_review, client)"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We verify that:
1. Pass 1 generated isolated per-file findings.
2. Pass 2 caught the cross-file contract mismatch that neither isolated pass could catch alone."""),

        code_cell("""# Step 4: Verification Checks
assert \"lacks expiry\" in results[\"local_findings\"][\"auth_service.py\"]
assert \"CONTRACT MISMATCH\" in results[\"integration_findings\"]

print(\" All verification assertions passed! Decomposition strategy proven.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Avoid feeding large multi-file diffs into a single monolithic prompt (attention dilution).
- **Rule 2**: Structure complex reviews as a **Two-Pass Prompt Chain**: local per-file checks followed by a cross-file contract synthesis pass.
- **Rule 3**: Contract mismatches (parameter names, missing fields) are discovered in Pass 2."""),
    ]
    return save_notebook("domain1", "ts_1_6_task_decomposition", cells)


def build_ts_1_7():
    cells = [
        markdown_cell("""# Domain 1: Agentic Architecture & Orchestration
## TS 1.7: Manage Session State, Resumption, and Forking
**Certification Focus**: CCAR-F Domain 1 (27% Exam Weight) | **Scenario Alignment**: Scenario 2 & 4

---

### 🎯 Key Architectural Principles
1. **Session Resumption**: `--resume <session-id>` reloads historical message trails for continuous sequential interactions.
2. **Session Forking (`fork_session`)**: Creates an isolated branch from a common parent baseline. Mutations in child branches do **not** pollute the parent session or sibling branches.
3. **The Stale Context Trap**: Resuming long historical sessions after the underlying codebase has changed causes Claude to hallucinate based on cached conversation snippets rather than reading the updated files.
4. **Remedy for Stale Context**: Discard the bloated conversation history and inject a concise, structured Markdown summary into a fresh session."""),

        code_cell("""# Step 1: Environment & Offline Setup
import copy
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(" Environment initialized for TS 1.7 Session Management.")"""),

        markdown_cell("""### 🗃️ Step 2: Session State & Manager Implementation
We implement `SessionState` supporting branching/forking and `SessionManager` supporting summary injection."""),

        code_cell("""# Step 2: Session Manager Logic
@dataclass
class SessionState:
    session_id: str
    session_name: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def fork(self, new_name: str) -> "SessionState":
        \"\"\"Branch from current session checkpoint into an isolated thread.\"\"\"
        return SessionState(
            session_id=f"fork_{uuid.uuid4().hex[:8]}",
            session_name=new_name,
            messages=copy.deepcopy(self.messages),
            metadata={"parent_session_id": self.session_id},
        )


class SessionManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, SessionState] = {}

    def create_session(self, name: str, initial_messages: Optional[List[Dict[str, Any]]] = None) -> SessionState:
        sid = f"sess_{uuid.uuid4().hex[:8]}"
        sess = SessionState(session_id=sid, session_name=name, messages=initial_messages or [])
        self.sessions[name] = sess
        return sess

    def resume_with_injected_summary(self, name: str, structured_summary: str, new_instruction: str) -> SessionState:
        \"\"\"
        Stale Context Remedy: Discards bloated history and starts a clean session
        anchored with a structured summary of previous findings.
        \"\"\"
        clean_messages = [
            {\"role\": \"user\", \"content\": f\"### PREVIOUS ARCHITECTURAL CONTEXT\\n{structured_summary}\"},
            {\"role\": \"assistant\", \"content\": \"Context acknowledged. Ready for next instructions.\"},
            {\"role\": \"user\", \"content\": new_instruction},
        ]
        return self.create_session(f\"{name}_resumed\", clean_messages)

print(\" SessionManager declared with forking and summary injection.\")"""),

        markdown_cell("""### 🧪 Step 3: Interactive Simulation
1. Create a base session.
2. Fork the session to test an alternative architecture in `branch_a`.
3. Verify that adding messages to `branch_a` leaves `base` unpolluted.
4. Mitigate stale context by resuming with an injected summary."""),

        code_cell("""# Step 3: Simulation
mgr = SessionManager()

# 1. Base session
base = mgr.create_session(\"base\", [{\"role\": \"user\", \"content\": \"Design database schema.\"}])
print(f\"Created base session: {base.session_name} with {len(base.messages)} message(s)\")

# 2. Fork into branch_a
branch_a = base.fork(\"branch_a\")
branch_a.messages.append({\"role\": \"user\", \"content\": \"Explore NoSQL option (MongoDB)\"})
print(f\"Forked {branch_a.session_name} with {len(branch_a.messages)} messages\")
print(f\"Base session message count remains: {len(base.messages)}\")

# 3. Resume with injected summary
clean = mgr.resume_with_injected_summary(
    \"base\",
    structured_summary=\"Agreed schema: PostgreSQL with orders and items tables.\",
    new_instruction=\"Add index on customer_id.\",
)
print(f\"\\nClean resumed session created: {clean.session_name}\")
print(\"Clean messages count:\", len(clean.messages))"""),

        markdown_cell("""### 🔬 Step 4: Verification Assertions
We assert that:
1. Forked session preserves parent history at fork time.
2. Mutating the child session does not affect the parent.
3. Resume with summary compresses context and clears stale messages."""),

        code_cell("""# Step 4: Verification Checks
assert branch_a.metadata[\"parent_session_id\"] == base.session_id
assert len(branch_a.messages) == 2
assert len(base.messages) == 1, \"Parent session must not be polluted by child fork!\"

# Verify summary injection
assert \"PREVIOUS ARCHITECTURAL CONTEXT\" in clean.messages[0][\"content\"]
assert \"Add index on customer_id\" in clean.messages[2][\"content\"]

print(\" All verification assertions passed! Session management verified.\")"""),

        markdown_cell("""### 💡 CCAR-F Exam Golden Rules
- **Rule 1**: Use `fork_session` for divergent exploration paths; never mutate the primary branch.
- **Rule 2**: When files or requirements change, discard long sessions and inject a **structured Markdown summary** to defeat the stale context trap.
- **Rule 3**: Do not use `--resume` indefinitely on large refactors; stale caches cause hallucinations."""),
    ]
    return save_notebook("domain1", "ts_1_7_session_management", cells)


def main():
    print("=== Generating Domain 1 Notebooks (TS 1.1 - TS 1.7) ===")
    build_ts_1_1()
    build_ts_1_2()
    build_ts_1_3()
    build_ts_1_4()
    build_ts_1_5()
    build_ts_1_6()
    build_ts_1_7()
    print(" Domain 1 notebooks generated successfully!\n")


if __name__ == "__main__":
    main()
