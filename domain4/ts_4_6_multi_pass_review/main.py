"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.6: Multi-instance and multi-pass review architectures
Exam Scenario 5: Claude Code for Continuous Integration

Intent: show WHY an independent reviewer beats self-review (the generator keeps its reasoning
context and tends to defend it) and how a per-file pass plus a cross-file integration pass
finds what a single pass misses. A verification pass has the model report a confidence per
finding; use it to route review (human vs auto), never to silently drop findings.

Two layers, both offline:
1. Rule-based stand-ins (IndependentReviewerInstance, MultiPassReviewPipeline).
2. A client-driven pipeline (LLMMultiPassPipeline) that works with lib.mock_claude. The mock
   scripts the model's answers, so tests prove the INPUT CONTEXT each reviewer sees, not model
   quality.

Extended thinking note: with `thinking` the only allowed tool_choice is auto/none, so a request
that forces the findings tool (any / named) must not enable thinking. Never send temperature
with thinking, and echo thinking blocks and signatures unchanged in any tool loop.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

REVIEW_MODEL = "claude-sonnet-4-5"  # integration pass / reasoning
WORKER_MODEL = "claude-haiku-4-5"  # per-file local pass
FINDING_TOOL_NAME = "report_review_finding"
MAX_TURNS = 4
MAX_TOKENS = 4000
THINKING_BUDGET = 2048
CONFIDENCE_THRESHOLD = 0.7

REVIEW_TOOL: Dict[str, Any] = {
    "name": FINDING_TOOL_NAME,
    "description": "Record one review finding.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "line": {"type": ["integer", "null"]},
            "severity": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
            "description": {"type": "string"},
            "remediation": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["file", "severity", "description", "remediation", "confidence"],
    },
}

LOCAL_SYSTEM = (
    "You are an independent code reviewer. Report only bugs and security issues in the given "
    "file. Do not report minor style. Use the report_review_finding tool for each finding."
)
INTEGRATION_SYSTEM = (
    "You are an independent integration reviewer. Compare function signatures with their call "
    "sites across files. Report mismatches via report_review_finding."
)


@dataclass
class ReviewFinding:
    pass_type: str  # "FILE_LOCAL" or "SYSTEM_INTEGRATION"
    severity: str
    target_component: str
    description: str
    suggested_remedy: str
    confidence: Optional[float] = None


# ==============================================================================
# 1. Rule-based stand-ins
# ==============================================================================


class IndependentReviewerInstance:
    """Simulates an isolated reviewer that sees only the artifact, never the author's reasoning."""

    def __init__(self, reviewer_id: str) -> None:
        self.reviewer_id = reviewer_id

    def review_local_file(self, filename: str, code: str) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        swallowed = re.search(r"except(\s+Exception)?\s*:\s*pass", code) or re.search(
            r"except(\s+Exception)?\s*:\s*\n\s*pass", code
        )
        if swallowed:
            findings.append(
                ReviewFinding(
                    "FILE_LOCAL",
                    "HIGH",
                    filename,
                    "Silent exception swallowing detected",
                    "Log the exception and re-raise or return a typed error.",
                )
            )
        if "None." in code:
            findings.append(
                ReviewFinding(
                    "FILE_LOCAL",
                    "MEDIUM",
                    filename,
                    "Potential NoneType dereference without null guard",
                    "Add an 'is not None' check.",
                )
            )
        return findings

    def review_system_contracts(self, files: Dict[str, str]) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        api_code = files.get("auth_api.py", "")
        client_code = files.get("auth_client.py", "")
        if "auth_token=" in client_code and "bearer_token:" in api_code:
            if "auth_token:" not in api_code:
                findings.append(
                    ReviewFinding(
                        "SYSTEM_INTEGRATION",
                        "CRITICAL",
                        "auth_api.py <-> auth_client.py",
                        "Client sends 'auth_token' but the server expects 'bearer_token'",
                        "Align the parameter name in the shared schema.",
                    )
                )
        return findings


def build_report(all_findings: List[ReviewFinding]) -> Dict[str, Any]:
    """Aggregate findings into the gate verdict used by both pipelines."""
    blocking = [f for f in all_findings if f.severity in ("CRITICAL", "HIGH")]
    return {
        "total_findings": len(all_findings),
        "pass_1_local_count": sum(f.pass_type == "FILE_LOCAL" for f in all_findings),
        "pass_2_integration_count": sum(f.pass_type == "SYSTEM_INTEGRATION" for f in all_findings),
        "critical_count": sum(f.severity == "CRITICAL" for f in all_findings),
        "approved": not blocking,
        "findings": [f.__dict__ for f in all_findings],
    }


class MultiPassReviewPipeline:
    """Pass 1: each file alone. Pass 2: cross-file contracts. Then aggregate."""

    def __init__(self) -> None:
        self.file_reviewer = IndependentReviewerInstance("reviewer_file_specialist")
        self.integration_reviewer = IndependentReviewerInstance("reviewer_arch_specialist")

    def run_review(self, codebase: Dict[str, str]) -> Dict[str, Any]:
        findings: List[ReviewFinding] = []
        for filename, content in codebase.items():
            findings.extend(self.file_reviewer.review_local_file(filename, content))
        findings.extend(self.integration_reviewer.review_system_contracts(codebase))
        return build_report(findings)


# ==============================================================================
# 2. Self-review vs independent reviewer (what context does the reviewer see?)
# ==============================================================================


@dataclass
class GeneratorSession:
    task: str
    reasoning: str  # the author's own explanation of why the code is right
    code: str


def build_self_review_messages(session: GeneratorSession) -> List[Dict[str, Any]]:
    """Anti-pattern: same conversation, the author reviews itself with its reasoning in view."""
    return [
        {"role": "user", "content": session.task},
        {"role": "assistant", "content": f"{session.reasoning}\n\n{session.code}"},
        {"role": "user", "content": "Review your code above. Any bugs?"},
    ]


def build_independent_review_messages(code: str, checklist: List[str]) -> List[Dict[str, Any]]:
    """Correct: a fresh conversation containing only the artifact and a checklist."""
    body = f"Checklist: {checklist}\n\nCode under review:\n```python\n{code}\n```"
    return [{"role": "user", "content": body}]


def shares_generator_context(messages: List[Dict[str, Any]], session: GeneratorSession) -> bool:
    """True when the reviewer can see the author's reasoning."""
    return any(session.reasoning in str(m["content"]) for m in messages)


# ==============================================================================
# 3. Client-driven reviewer (mock-friendly) with explicit stop_reason handling
# ==============================================================================


@dataclass
class ReviewResult:
    findings: List[ReviewFinding] = field(default_factory=list)
    truncated: bool = False
    refused: bool = False


def build_review_request(
    model: str, system: str, messages: List[Dict[str, Any]], use_thinking: bool
) -> Dict[str, Any]:
    """thinking => tool_choice auto (required); otherwise force the findings tool with 'any'."""
    request: Dict[str, Any] = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": system,
        "tools": [REVIEW_TOOL],
        "tool_choice": {"type": "auto"} if use_thinking else {"type": "any"},
        "messages": list(messages),
    }
    if use_thinking:
        request["thinking"] = {"type": "enabled", "budget_tokens": THINKING_BUDGET}
    return request


def run_review_conversation(
    client: Any,
    model: str,
    system: str,
    messages: List[Dict[str, Any]],
    pass_type: str,
    use_thinking: bool = False,
) -> ReviewResult:
    """Loop on stop_reason: tool_use -> record findings and continue, end_turn -> done."""
    result = ReviewResult()
    convo = list(messages)  # never mutate the caller's list
    for _ in range(MAX_TURNS):
        request = build_review_request(model, system, convo, use_thinking)
        response = client.messages.create(**request)
        stop = response.stop_reason
        if stop == "end_turn":
            return result
        if stop == "max_tokens":
            result.truncated = True
            return result
        if stop == "refusal":
            result.refused = True
            return result
        if stop in ("tool_use", "pause_turn"):
            tool_results: List[Dict[str, Any]] = []
            for block in response.content:
                if getattr(block, "type", "") == "tool_use" and block.name == FINDING_TOOL_NAME:
                    data = block.input
                    where = f"{data['file']}:{data['line']}" if data.get("line") else data["file"]
                    result.findings.append(
                        ReviewFinding(
                            pass_type,
                            data["severity"],
                            where,
                            data["description"],
                            data["remediation"],
                            data.get("confidence"),
                        )
                    )
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": "recorded"}
                    )
            convo.append({"role": "assistant", "content": response.content})  # echoed unchanged
            if tool_results:
                convo.append({"role": "user", "content": tool_results})
            continue
        break  # unknown stop_reason: stop rather than loop
    return result


def extract_interfaces(codebase: Dict[str, str]) -> Dict[str, List[str]]:
    """def/class lines per file: the signatures Pass 2 needs, without full implementations."""
    return {
        name: [ln.strip() for ln in code.splitlines() if re.match(r"\s*(def|class)\s+\w+", ln)]
        for name, code in codebase.items()
    }


def extract_call_sites(codebase: Dict[str, str]) -> List[str]:
    """Lines that call a function defined in a DIFFERENT file."""
    defined: Dict[str, str] = {}
    for name, code in codebase.items():
        for fn in re.findall(r"def\s+(\w+)\s*\(", code):
            defined[fn] = name
    sites: List[str] = []
    for name, code in codebase.items():
        for line in code.splitlines():
            for fn, home in defined.items():
                if home != name and re.search(rf"\b{fn}\s*\(", line) and "def " not in line:
                    sites.append(f"{name}: {line.strip()}")
    return sites


def route_by_confidence(
    findings: List[ReviewFinding], threshold: float = CONFIDENCE_THRESHOLD
) -> Dict[str, List[ReviewFinding]]:
    """Verification routing: low or missing confidence goes to a human. Nothing is dropped."""
    auto: List[ReviewFinding] = []
    human: List[ReviewFinding] = []
    for f in findings:
        (auto if f.confidence is not None and f.confidence >= threshold else human).append(f)
    return {"auto_report": auto, "human_review": human}


class LLMMultiPassPipeline:
    """Per-file passes (fresh context each) + one integration pass + verification routing."""

    def __init__(self, client: Any, use_thinking_on_integration: bool = False) -> None:
        self.client = client
        self.use_thinking = use_thinking_on_integration

    def run_review(self, codebase: Dict[str, str]) -> Dict[str, Any]:
        findings: List[ReviewFinding] = []
        for filename, code in codebase.items():
            messages = build_independent_review_messages(code, ["bugs", "security"])
            res = run_review_conversation(
                self.client, WORKER_MODEL, LOCAL_SYSTEM, messages, "FILE_LOCAL"
            )
            findings.extend(res.findings)

        summary = json.dumps(
            {"interfaces": extract_interfaces(codebase), "call_sites": extract_call_sites(codebase)}
        )
        res = run_review_conversation(
            self.client,
            REVIEW_MODEL,
            INTEGRATION_SYSTEM,
            [{"role": "user", "content": summary}],
            "SYSTEM_INTEGRATION",
            use_thinking=self.use_thinking,
        )
        findings.extend(res.findings)

        report = build_report(findings)
        routed = route_by_confidence(findings)
        report["auto_report_count"] = len(routed["auto_report"])
        report["human_review_count"] = len(routed["human_review"])
        return report


def main() -> None:
    codebase = {
        "auth_api.py": "def verify_session(bearer_token: str):\n    try:\n        pass\n"
        "    except Exception: pass\n",
        "auth_client.py": "def login():\n    return verify_session(auth_token='jwt')\n",
    }
    report = MultiPassReviewPipeline().run_review(codebase)
    print("Pass 1:", report["pass_1_local_count"], "Pass 2:", report["pass_2_integration_count"])
    print("Merge:", "APPROVED" if report["approved"] else "BLOCKED")
    print(json.dumps(report["findings"], indent=2))


if __name__ == "__main__":
    main()
