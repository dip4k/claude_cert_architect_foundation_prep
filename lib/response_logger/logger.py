"""
ResponseTrail and replay utilities for logging agentic loop events.

The ResponseTrail class appends structured events to a JSONL file.
Events are timestamped, session-tagged, and include full context.

Supported events:
  - session_start / session_end: lifecycle
  - api_request / api_response: Claude API calls
  - tool_call / tool_result: tool invocations and results
"""

import os
import json
import time
import inspect
import ast
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


def get_agent_trail_path(agent_file: Optional[str] = None) -> str:
    """
    Get the trail file path for an agent script.

    Creates a 'trails/' subdirectory in the same location as the agent script.
    This isolates each agent's trails from other agents.

    Args:
        agent_file: Path to the agent script (__file__). If None, tries to
                   auto-detect from the calling script.

    Returns:
        Path to trail file: {agent_directory}/trails/agent_trail.jsonl

    Example:
        # In your agent script (e.g., stop_reason/main.py):
        from lib.response_logger import ResponseTrail, get_agent_trail_path

        trail_path = get_agent_trail_path(__file__)
        trail = ResponseTrail(trail_path)
    """
    if agent_file is None:
        # Auto-detect caller's __file__
        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            agent_file = frame.f_back.f_globals.get("__file__")
        if not agent_file:
            # Fallback to current working directory
            return "trails/agent_trail.jsonl"

    # Get absolute path to agent directory
    agent_dir = os.path.dirname(os.path.abspath(agent_file))
    trail_dir = os.path.join(agent_dir, "trails")

    # Create directory if it doesn't exist
    os.makedirs(trail_dir, exist_ok=True)

    return os.path.join(trail_dir, "agent_trail.jsonl")


def _serialize_content(content: Any) -> Any:
    """
    Convert SDK block objects, dataclasses, Pydantic models, or nested containers
    into JSON-serializable structures (dicts, lists, primitives) for faithful trail logging.
    """
    if content is None or isinstance(content, (str, int, float, bool)):
        return content
    if isinstance(content, (list, tuple)):
        return [_serialize_content(item) for item in content]
    if isinstance(content, dict):
        return {k: _serialize_content(v) for k, v in content.items()}
    if hasattr(content, "model_dump") and callable(content.model_dump):
        return _serialize_content(content.model_dump())
    if hasattr(content, "to_dict") and callable(content.to_dict):
        return _serialize_content(content.to_dict())
    if hasattr(content, "__dict__"):
        return _serialize_content(content.__dict__)
    return str(content)


def _serialize_message(message: Any) -> Dict[str, Any]:
    """Serialize a single conversation message into a clean, JSON-serializable dict."""
    if isinstance(message, dict):
        clean = {
            "role": message.get("role", "unknown"),
            "content": _serialize_content(message.get("content")),
        }
        for k, v in message.items():
            if k not in ("role", "content"):
                clean[k] = _serialize_content(v)
        return clean
    if hasattr(message, "model_dump") and callable(message.model_dump):
        return _serialize_content(message.model_dump())
    return {
        "role": getattr(message, "role", "unknown"),
        "content": _serialize_content(getattr(message, "content", str(message))),
    }


def _json_default(obj: Any) -> Any:
    """Fail-safe serializer for json.dumps in case any object lacks explicit serialization."""
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return obj.model_dump()
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


class ResponseTrail:
    """
    Appends every agentic-loop event to a JSONL file (one JSON object per line).
    JSONL is append-friendly and streaming-readable — ideal for audit trails.

    Events logged:
      - session_start: begins a new session with prompt and model
      - session_end: concludes session with final text and reason
      - api_request: messages sent to Claude (turn number)
      - api_response: raw response with stop_reason and latency
      - tool_call: tool invocation (name, id, input)
      - tool_result: tool output (name, id, output)

    Usage:
        from lib.response_logger import ResponseTrail, get_agent_trail_path

        # Auto-detect trail path based on agent script location
        trail_path = get_agent_trail_path(__file__)
        trail = ResponseTrail(trail_path)

        trail.session_start(session_id, prompt, model)
        trail.api_request(session_id, turn, messages)
        trail.api_response(session_id, turn, response, latency_s)
        # ...
        trail.session_end(session_id, final_text, "end_turn")
    """

    def __init__(self, path: str = "agent_trail.jsonl") -> None:
        """
        Initialize ResponseTrail.

        Args:
            path: File path for JSONL trail. Subdirectories created if needed.
                 Use get_agent_trail_path(__file__) to auto-generate path
                 relative to agent script location.
        """
        self.path = path
        # Ensure directory exists if a nested path is given
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _write(self, event_type: str, session_id: str, payload: Dict[str, Any]) -> None:
        """Write a single event record to the JSONL file."""
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "event": event_type,
            "payload": payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=_json_default, ensure_ascii=False) + "\n")

    def session_start(self, session_id: str, prompt: str, model: str) -> None:
        """Log the start of an agentic session."""
        self._write("session_start", session_id, {"prompt": prompt, "model": model})

    def session_end(self, session_id: str, final_text: str, reason: str) -> None:
        """
        Log the end of an agentic session.

        Args:
            session_id: Unique session identifier
            final_text: Final response text from Claude
            reason: Termination reason (e.g., 'end_turn', 'max_tokens', 'max_turns_exhausted')
        """
        self._write("session_end", session_id, {
            "final_text": final_text,
            "reason": reason
        })

    def api_request(self, session_id: str, turn: int, messages: List[Dict[str, Any]]) -> None:
        """
        Log an outgoing request to Claude API.

        Deep-cleans each message so that live SDK block objects (e.g. ToolUseBlock)
        are serialized as proper JSON dicts rather than stringified reprs.

        Args:
            session_id: Unique session identifier
            turn: Turn number in the agentic loop
            messages: Message list sent to the API
        """
        clean_messages = [_serialize_message(m) for m in messages]
        self._write("api_request", session_id, {
            "turn": turn,
            "messages": clean_messages
        })

    def api_response(
        self,
        session_id: str,
        turn: int,
        response: Any,
        latency_s: float
    ) -> None:
        """
        Log a response from Claude API.

        Args:
            session_id: Unique session identifier
            turn: Turn number in the agentic loop
            response: Full SDK response object or response dict
            latency_s: Request latency in seconds
        """
        # Extract raw response data
        try:
            # Anthropic SDK responses have model_dump()
            raw = response.model_dump()
        except AttributeError:
            # Fallback for dict or other response types
            if isinstance(response, dict):
                raw = _serialize_content(response)
            else:
                raw = str(response)

        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason is None and isinstance(response, dict):
            stop_reason = response.get("stop_reason")

        self._write("api_response", session_id, {
            "turn": turn,
            "stop_reason": stop_reason,
            "latency_s": round(latency_s, 3),
            "raw": raw,
        })

    def tool_call(
        self,
        session_id: str,
        turn: int,
        name: str,
        tool_id: str,
        tool_input: Dict[str, Any]
    ) -> None:
        """
        Log a tool call invocation.

        Args:
            session_id: Unique session identifier
            turn: Turn number in the agentic loop
            name: Tool name
            tool_id: Unique tool call ID
            tool_input: Input parameters sent to the tool
        """
        self._write("tool_call", session_id, {
            "turn": turn,
            "name": name,
            "tool_id": tool_id,
            "input": _serialize_content(tool_input)
        })

    def tool_result(
        self,
        session_id: str,
        turn: int,
        name: str,
        tool_id: str,
        output: Dict[str, Any]
    ) -> None:
        """
        Log a tool execution result.

        Args:
            session_id: Unique session identifier
            turn: Turn number in the agentic loop
            name: Tool name
            tool_id: Unique tool call ID
            output: Tool execution output
        """
        self._write("tool_result", session_id, {
            "turn": turn,
            "name": name,
            "tool_id": tool_id,
            "output": _serialize_content(output)
        })


def parse_block_repr(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a stringified SDK block repr (e.g. from legacy or corrupted logs) into a dict.

    Handles:
      - ToolUseBlock(id='...', caller=..., input={...}, name='...', type='tool_use', ...)
      - TextBlock(text='...', type='text', ...)
    """
    if not isinstance(text, str):
        return None

    stripped = text.strip()

    # ToolUseBlock
    if stripped.startswith("ToolUseBlock(") and stripped.endswith(")"):
        block: Dict[str, Any] = {"type": "tool_use"}

        id_match = re.search(r"\bid=(['\"])(.*?)\1", stripped)
        if id_match:
            block["id"] = id_match.group(2)

        name_match = re.search(r"\bname=(['\"])(.*?)\1", stripped)
        if name_match:
            block["name"] = name_match.group(2)

        type_match = re.search(r",\s*type=(['\"])(.*?)\1", stripped)
        if type_match:
            block["type"] = type_match.group(2)
        else:
            block["type"] = "tool_use"

        # Extract input dict by balancing braces
        input_pos = stripped.find("input={")
        if input_pos != -1:
            brace_start = input_pos + len("input=")
            depth = 0
            brace_end = -1
            in_quote = None
            escaped = False

            for i in range(brace_start, len(stripped)):
                ch = stripped[i]
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if in_quote:
                    if ch == in_quote:
                        in_quote = None
                    continue
                if ch in ("'", '"'):
                    in_quote = ch
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        brace_end = i + 1
                        break

            if brace_end != -1:
                input_str = stripped[brace_start:brace_end]
                try:
                    block["input"] = ast.literal_eval(input_str)
                except Exception:
                    try:
                        block["input"] = json.loads(input_str)
                    except Exception:
                        block["input"] = input_str
            else:
                block["input"] = {}
        else:
            block["input"] = {}

        return block

    # TextBlock
    if stripped.startswith("TextBlock(") and stripped.endswith(")"):
        text_match = re.search(r"\btext=(['\"])(.*?)\1(?:,\s*[a-zA-Z_]+=|,\s*\)|$|\))", stripped, re.DOTALL)
        return {
            "type": "text",
            "text": text_match.group(2) if text_match else "",
        }

    return None


def _repair_content(content: Any) -> Any:
    """Repair any stringified SDK blocks in content structure."""
    if isinstance(content, str):
        parsed = parse_block_repr(content)
        return parsed if parsed is not None else content
    if isinstance(content, list):
        repaired = []
        for item in content:
            if isinstance(item, str):
                parsed = parse_block_repr(item)
                repaired.append(parsed if parsed is not None else item)
            elif isinstance(item, dict):
                repaired.append({k: _repair_content(v) for k, v in item.items()})
            else:
                repaired.append(item)
        return repaired
    if isinstance(content, dict):
        return {k: _repair_content(v) for k, v in content.items()}
    return content


def parse_trail(
    path: str = "agent_trail.jsonl",
    session_id: Optional[str] = None,
    repair_blocks: bool = True,
) -> List[Dict[str, Any]]:
    """
    Parse a JSONL trail file into a list of structured event records.

    Args:
        path: Path to the JSONL trail file.
        session_id: Optional session ID filter.
        repair_blocks: If True, automatically detects and converts stringified
                       SDK block reprs (e.g. ToolUseBlock) into proper dicts.

    Returns:
        List of parsed record dicts.
    """
    if not os.path.exists(path):
        return []

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            rec = json.loads(line)
            if session_id and rec.get("session_id") != session_id:
                continue

            if repair_blocks:
                ev = rec.get("event")
                payload = rec.get("payload", {})
                if ev == "api_request" and "messages" in payload:
                    clean_msgs = []
                    for msg in payload["messages"]:
                        if isinstance(msg, dict):
                            clean_m = dict(msg)
                            clean_m["content"] = _repair_content(msg.get("content"))
                            clean_msgs.append(clean_m)
                        else:
                            clean_msgs.append(msg)
                    payload["messages"] = clean_msgs

            records.append(rec)

    return records


def reconstruct_session_messages(
    path_or_records: Union[str, List[Dict[str, Any]]],
    session_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Reconstruct the full conversation message list for crash recovery and state persistence.
    Examines trail events to restore the exact message sequence up to the latest known state.

    Args:
        path_or_records: Path to JSONL trail file or pre-parsed list of records.
        session_id: Optional session ID. If omitted, uses the latest session found.

    Returns:
        List of valid message dicts ready for Claude API (`client.messages.create(messages=...)`).
    """
    if isinstance(path_or_records, str):
        records = parse_trail(path_or_records, session_id=session_id, repair_blocks=True)
    else:
        records = path_or_records

    if not records:
        return []

    if not session_id:
        session_id = records[-1].get("session_id")
        records = [r for r in records if r.get("session_id") == session_id]

    # Find all api_requests in order
    api_requests = [r for r in records if r.get("event") == "api_request"]
    if not api_requests:
        return []

    latest_req = api_requests[-1]
    messages = list(latest_req.get("payload", {}).get("messages", []))

    # Deep clean/repair any remaining stringified blocks
    repaired_messages = []
    for m in messages:
        if isinstance(m, dict):
            cm = dict(m)
            cm["content"] = _repair_content(m.get("content"))
            repaired_messages.append(cm)
        else:
            repaired_messages.append(m)

    return repaired_messages


def repair_trail_file(source_path: str, target_path: Optional[str] = None) -> int:
    """
    Repairs a JSONL trail file by converting any stringified SDK block representations
    into valid JSON objects and saving the result.

    Args:
        source_path: Path to the existing trail file.
        target_path: Optional target path. If None, overwrites source_path in-place.

    Returns:
        The number of event records repaired.
    """
    if not os.path.exists(source_path):
        return 0

    repaired_count = 0
    records = []

    with open(source_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ev = rec.get("event")
            payload = rec.get("payload", {})
            was_repaired = False

            if ev == "api_request" and "messages" in payload:
                new_msgs = []
                for msg in payload["messages"]:
                    if isinstance(msg, dict):
                        original_content = msg.get("content")
                        repaired_content = _repair_content(original_content)
                        if repaired_content != original_content:
                            was_repaired = True
                        new_msg = dict(msg)
                        new_msg["content"] = repaired_content
                        new_msgs.append(new_msg)
                    else:
                        new_msgs.append(msg)
                payload["messages"] = new_msgs

            if was_repaired:
                repaired_count += 1
            records.append(rec)

    dest = target_path if target_path is not None else source_path
    with open(dest, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=_json_default, ensure_ascii=False) + "\n")

    return repaired_count


def replay_trail(path: str = "agent_trail.jsonl", session_id: Optional[str] = None) -> None:
    """
    Re-read and pretty-print a saved trail WITHOUT calling the API.
    Useful for offline review, debugging, and audit.

    Args:
        path: Path to the JSONL trail file
        session_id: Optional; filter to a single session ID
    """
    if not os.path.exists(path):
        print(f"❌ No trail file found at: {path}")
        return

    print("\n" + "#" * 80)
    print(f"REPLAYING TRAIL: {path}" + (f"  (session={session_id})" if session_id else ""))
    print("#" * 80)

    records = parse_trail(path, session_id=session_id, repair_blocks=True)
    event_count = len(records)

    for rec in records:
        ev = rec["event"]
        p = rec["payload"]
        ts = rec["ts"]
        sid = rec["session_id"][:8]

        if ev == "session_start":
            print(f"\n[{ts}] ({sid}) ▶▶  SESSION START")
            print(f"       Model: {p['model']}")
            print(f"       Prompt: {p['prompt'][:100]}{'...' if len(p['prompt']) > 100 else ''}")

        elif ev == "api_request":
            msgs = p.get("messages", [])
            print(f"[{ts}] ({sid}) ⇒   API_REQUEST turn={p['turn']}")
            print(f"       Messages: {len(msgs)} message(s)")
            for idx, m in enumerate(msgs, 1):
                role = m.get("role", "unknown")
                content = m.get("content")
                if isinstance(content, str):
                    preview = content[:80] + ("..." if len(content) > 80 else "")
                    print(f"         {idx}. [{role}] \"{preview}\"")
                elif isinstance(content, list):
                    block_descs = []
                    for b in content:
                        if isinstance(b, dict):
                            b_type = b.get("type")
                            if b_type == "tool_use":
                                block_descs.append(f"tool_use:{b.get('name')}")
                            elif b_type == "tool_result":
                                block_descs.append(f"tool_result(id={b.get('tool_use_id', '')[:8]}...)")
                            elif b_type == "text":
                                block_descs.append(f"text:\"{b.get('text', '')[:30]}\"")
                            else:
                                block_descs.append(str(b_type))
                        else:
                            block_descs.append(str(b)[:40])
                    print(f"         {idx}. [{role}] [{', '.join(block_descs)}]")
                else:
                    print(f"         {idx}. [{role}] {str(content)[:80]}")

        elif ev == "api_response":
            print(f"[{ts}] ({sid}) ⇐   API_RESPONSE turn={p['turn']}")
            print(f"       Stop Reason: {p['stop_reason']}")
            print(f"       Latency: {p['latency_s']}s")

        elif ev == "tool_call":
            input_preview = json.dumps(p["input"])[:80]
            print(f"[{ts}] ({sid}) 🔧  TOOL_CALL turn={p['turn']} | {p['name']}({input_preview}...)")
            print(f"       Tool ID: {p['tool_id']}")

        elif ev == "tool_result":
            output_preview = json.dumps(p["output"])[:80]
            print(f"[{ts}] ({sid}) 📤  TOOL_RESULT turn={p['turn']} | {p['name']} → {output_preview}...")

        elif ev == "session_end":
            print(f"[{ts}] ({sid}) ◀◀  SESSION END")
            print(f"       Reason: {p['reason']}")
            final_preview = p["final_text"][:100] if p["final_text"] else "(empty)"
            print(f"       Final Text: {final_preview}{'...' if len(p['final_text']) > 100 else ''}")

    print("\n" + "#" * 80)
    print(f"Total events replayed: {event_count}")
    print("#" * 80 + "\n")


def query_trail(
    path: str = "agent_trail.jsonl",
    event_type: Optional[str] = None,
    session_id: Optional[str] = None,
    repair_blocks: bool = True,
) -> List[Dict[str, Any]]:
    """
    Query trail file and return matching records.

    Args:
        path: Path to the JSONL trail file
        event_type: Optional; filter by event type (e.g., 'api_response', 'tool_call')
        session_id: Optional; filter by session ID
        repair_blocks: If True, automatically repairs stringified blocks in results.

    Returns:
        List of matching records (each as a dict)
    """
    records = parse_trail(path, session_id=session_id, repair_blocks=repair_blocks)
    if event_type:
        records = [r for r in records if r.get("event") == event_type]
    return records
