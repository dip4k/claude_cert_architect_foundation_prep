"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.6: Design task decomposition strategies for complex workflows
Exam Scenario 2 & 5: Code Generation & Continuous Integration

Key Exam Concepts Demonstrated:
1. Prompt chaining (Fixed sequential passes):
   - Analyzing each file individually for local issues (Pass 1).
   - Running a separate cross-file integration pass to examine data flow and contracts (Pass 2).
   - Why single-pass multi-file reviews cause attention dilution and missed bugs.
2. Dynamic adaptive decomposition:
   - For open-ended tasks, generating subtasks adaptively based on intermediate discoveries
     (e.g., mapping dependencies before deciding refactoring order).
3. ResponseTrail logging for multi-pass audit tracking.

Manual Execution (WSL Ubuntu):
    uv run domain1/ts_1_6_task_decomposition/main.py
"""

import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path

load_dotenv()


# ==============================================================================
# 1. Multi-Pass Review Decomposition Architecture
# ==============================================================================

@dataclass
class CodeFile:
    filename: str
    content: str


SAMPLE_PULL_REQUEST: List[CodeFile] = [
    CodeFile(
        filename="auth_service.py",
        content="""def create_user_token(user_id: str) -> str:
    # Generates JWT without expiration timestamp
    return jwt.encode({"sub": user_id}, SECRET_KEY)
""",
    ),
    CodeFile(
        filename="api_router.py",
        content="""@app.route("/profile")
def profile():
    token = request.headers.get("Authorization")
    user_id = verify_token(token)["sub"]
    # Unsanitized SQL query
    user = db.query(f"SELECT * FROM users WHERE id = '{user_id}'")
    return jsonify(user)
""",
    ),
]


def run_prompt_chaining_review(
    files: List[CodeFile],
    client: Any,
    trail: ResponseTrail,
) -> Dict[str, Any]:
    """
    Fixed Sequential Pipeline (Prompt Chaining):
    - Pass 1: Local per-file analysis pass (avoids attention dilution).
    - Pass 2: Cross-file integration pass examining shared contracts.
    """
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, "Multi-pass review decomposition", "claude-haiku-4-5")

    local_file_findings: Dict[str, str] = {}

    # --------------------------------------------------------------------------
    # PASS 1: Per-File Local Analysis Pass
    # --------------------------------------------------------------------------
    for idx, f in enumerate(files, start=1):
        prompt = (
            f"Review Pass 1 (Local File Isolation): Analyze ONLY the following file for syntax, "
            f"security, and error handling issues local to this file.\n\n"
            f"File: {f.filename}\n"
            f"```python\n{f.content}\n```"
        )
        trail.api_request(session_id, idx, [{"role": "user", "content": prompt}])

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        finding_text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
        local_file_findings[f.filename] = finding_text
        trail.session_end(session_id, finding_text, f"pass1_file_{idx}")

    # --------------------------------------------------------------------------
    # PASS 2: Cross-File Integration Pass
    # --------------------------------------------------------------------------
    integration_prompt = (
        "Review Pass 2 (Cross-File Integration): Given the local findings and the interaction "
        "between files, identify contract mismatches, end-to-end data flow vulnerabilities, "
        "and architectural concerns across modules.\n\n"
    )
    for fn, findings in local_file_findings.items():
        integration_prompt += f"--- Findings for {fn} ---\n{findings}\n\n"

    turn_integration = len(files) + 1
    trail.api_request(session_id, turn_integration, [{"role": "user", "content": integration_prompt}])

    response_integration = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": integration_prompt}],
    )
    integration_text = "".join(b.text for b in response_integration.content if getattr(b, "type", "") == "text")
    trail.session_end(session_id, integration_text, "pass2_integration")

    return {
        "local_findings": local_file_findings,
        "integration_findings": integration_text,
    }


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    print("Executing Multi-Pass Prompt Chaining Review Pipeline...")
    results = run_prompt_chaining_review(SAMPLE_PULL_REQUEST, client, trail)
    print("\n=== Local File Analysis (Pass 1) ===")
    for fn, res in results["local_findings"].items():
        print(f"\n[{fn}]:\n{res}")

    print("\n=== Cross-File Integration Analysis (Pass 2) ===")
    print(results["integration_findings"])


if __name__ == "__main__":
    main()
