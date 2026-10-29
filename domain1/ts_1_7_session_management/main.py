"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.7: Manage session state, resumption, and forking
Exam Scenario 2 & 4: Code Generation & Developer Productivity

Key Exam Concepts Demonstrated:
1. Named session resumption (--resume <session-name>): Continuing a specific prior exploration session.
2. Fork-based session management (fork_session): Creating independent diverging exploration branches
   from a shared analysis baseline (e.g., comparing two refactoring approaches).
3. Stale context vs Injected summaries:
   - When prior tool results are stale (files changed, db updated), resuming raw conversation
     causes hallucinated assumptions.
   - Starting a fresh session with an injected structured summary is cleaner and more reliable.
4. Informing resumed sessions about specific file delta changes.

Manual Execution (WSL Ubuntu):
    uv run domain1/ts_1_7_session_management/main.py
"""

import copy
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path
from domain1.loop_common import (
    COORDINATOR_MODEL,
    LoopStopped,
    read_stop_reason,
    response_text,
    stop_status,
)

load_dotenv()


# ==============================================================================
# 1. Session State Engine (Resumption & Forking)
# ==============================================================================

@dataclass
class SessionState:
    session_id: str
    session_name: str
    messages: List[Dict[str, Any]]
    context_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def fork(self, fork_name: str) -> "SessionState":
        """
        Creates an independent branch from current analysis baseline.
        Mutations in fork do not affect parent session.
        """
        forked_id = f"fork_{uuid.uuid4().hex[:8]}"
        return SessionState(
            session_id=forked_id,
            session_name=fork_name,
            messages=copy.deepcopy(self.messages),
            context_summary=self.context_summary,
            metadata={"parent_session_id": self.session_id, "fork_timestamp": "2026-10-06T12:00:00Z"},
        )


class SessionManager:
    """Manages persistent named sessions and forking."""

    def __init__(self) -> None:
        self.sessions: Dict[str, SessionState] = {}

    def create_session(self, name: str, initial_messages: List[Dict[str, Any]]) -> SessionState:
        sess = SessionState(session_id=str(uuid.uuid4()), session_name=name, messages=initial_messages)
        self.sessions[name] = sess
        return sess

    def get_session(self, name: str) -> Optional[SessionState]:
        return self.sessions.get(name)

    def resume(self, name: str, changed_files: Optional[List[str]] = None) -> SessionState:
        """
        Named resumption (--resume <session-name>): continue the same history. If files changed
        since the last turn, tell the resumed session which ones so it re-reads them instead of
        trusting stale tool results.
        """
        sess = self.sessions[name]
        if changed_files:
            listed = "\n".join(f"- {path}" for path in changed_files)
            sess.messages.append({
                "role": "user",
                "content": (
                    "These files changed since your last tool results. Re-read them before "
                    f"relying on earlier output:\n{listed}"
                ),
            })
        return sess

    def resume_with_injected_summary(
        self,
        name: str,
        structured_summary: str,
        new_instruction: str,
    ) -> SessionState:
        """
        Exam Pattern: Starting fresh with an injected summary instead of resuming
        with bloated stale tool results.
        """
        fresh_messages = [
            {
                "role": "user",
                "content": (
                    f"### Baseline Context Summary (from prior session '{name}'):\n"
                    f"{structured_summary}\n\n"
                    f"### Current Task:\n{new_instruction}"
                ),
            }
        ]
        resumed_sess = SessionState(
            session_id=str(uuid.uuid4()),
            session_name=f"{name}_resumed_summary",
            messages=fresh_messages,
            context_summary=structured_summary,
        )
        self.sessions[resumed_sess.session_name] = resumed_sess
        return resumed_sess


# ==============================================================================
# 2. Resumption & Forking Demonstration
# ==============================================================================

def execute_turn(
    session: SessionState,
    client: Any,
    trail: ResponseTrail,
) -> str:
    trail.api_request(session.session_id, len(session.messages), session.messages)
    response = client.messages.create(
        model=COORDINATOR_MODEL,
        max_tokens=600,
        messages=session.messages,
    )
    parser = create_parser()
    stop_reason = read_stop_reason(parser, response)
    reply_text = response_text(response)
    if stop_reason != "end_turn":
        trail.session_end(session.session_id, reply_text, stop_status(stop_reason))
        raise LoopStopped(stop_reason, reply_text)
    session.messages.append({"role": "assistant", "content": reply_text})
    trail.session_end(session.session_id, reply_text, "turn_complete")
    return reply_text


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    mgr = SessionManager()

    # Step 1: Base analysis session
    print("Step 1: Baseline Architecture Analysis Session...")
    base_sess = mgr.create_session(
        name="legacy_db_analysis",
        initial_messages=[
            {
                "role": "user",
                "content": "Analyze legacy database: 50 models using SQLAlchemy 1.4 sync queries.",
            }
        ],
    )
    ans1 = execute_turn(base_sess, client, trail)
    print(f"Base Analysis:\n{ans1[:150]}...\n")

    # Step 2: Fork session into two divergent paths
    print("Step 2: Forking session into 2 divergent architectural approaches...")
    fork_async = base_sess.fork("approach_async_sqlalchemy")
    fork_async.messages.append({
        "role": "user",
        "content": "Approach A: Evaluate migrating to Async SQLAlchemy 2.0 with asyncpg.",
    })
    ans_async = execute_turn(fork_async, client, trail)
    print(f"Fork A (Async):\n{ans_async[:150]}...\n")

    fork_prisma = base_sess.fork("approach_prisma")
    fork_prisma.messages.append({
        "role": "user",
        "content": "Approach B: Evaluate migrating to Prisma Python ORM.",
    })
    ans_prisma = execute_turn(fork_prisma, client, trail)
    print(f"Fork B (Prisma):\n{ans_prisma[:150]}...\n")

    # Step 3: Resuming with injected summary rather than stale context
    print("Step 3: Starting clean session with injected structured summary...")
    summary = "Database currently has 50 sync models. Evaluated Async SQLAlchemy 2.0 vs Prisma."
    clean_sess = mgr.resume_with_injected_summary(
        name="legacy_db_analysis",
        structured_summary=summary,
        new_instruction="Produce a final migration recommendation matrix.",
    )
    ans_final = execute_turn(clean_sess, client, trail)
    print(f"Final Decision:\n{ans_final[:150]}...\n")


if __name__ == "__main__":
    main()
