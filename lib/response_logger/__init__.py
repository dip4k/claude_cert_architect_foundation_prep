"""
Response Logger - Audit trail logging for Claude SDK agentic loops.

Provides structured logging of:
  - API requests and responses
  - Tool calls and results
  - Session lifecycle events
  - Latency and performance metrics

All events are appended to a JSONL file (one JSON object per line) for
offline replay and analysis without re-running the API.

Quick Start - Auto-detect trail path (recommended):
    from lib.response_logger import ResponseTrail, get_agent_trail_path

    # Auto-detect trail directory based on agent script location
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(trail_path)

    trail.session_start(session_id, prompt, model)
    trail.api_request(session_id, turn, messages)
    trail.api_response(session_id, turn, response, latency_s)
    trail.tool_call(session_id, turn, name, tool_id, input)
    trail.tool_result(session_id, turn, name, tool_id, output)
    trail.session_end(session_id, final_text, reason)

    # Replay without API calls
    from lib.response_logger import replay_trail
    replay_trail(trail_path)

Quick Start - Manual path:
    from lib.response_logger import ResponseTrail

    trail = ResponseTrail("custom/path/to/trail.jsonl")
    # ... rest as above
"""

from .logger import (
    ResponseTrail,
    replay_trail,
    query_trail,
    parse_trail,
    reconstruct_session_messages,
    repair_trail_file,
    parse_block_repr,
    get_agent_trail_path,
)

__all__ = [
    "ResponseTrail",
    "replay_trail",
    "query_trail",
    "parse_trail",
    "reconstruct_session_messages",
    "repair_trail_file",
    "parse_block_repr",
    "get_agent_trail_path",
]
