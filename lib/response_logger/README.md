# Response Logger - Audit Trail for Claude SDK

Structured logging of agentic loop events to JSONL files for offline review, replay, and audit without re-running the API.

## Overview

**ResponseTrail** captures every step in an agentic loop:
- Session lifecycle (start, end with reason)
- API requests and responses (with latency)
- Tool calls and results
- Full timestamps and session IDs

All events are appended to a **JSONL file** (one JSON object per line) for:
- 📋 Audit trail and compliance
- 🔍 Offline debugging without re-running API calls
- 📊 Performance analysis (latency, token usage)
- 🎯 Replay and understanding model behavior

## Installation

Already included in the project. Import from `lib.response_logger`:

```python
from lib.response_logger import ResponseTrail, replay_trail
```

## Quick Start

### 1. Create a Trail Logger (Recommended: Auto-detect path)

```python
from lib.response_logger import ResponseTrail, get_agent_trail_path
import uuid

# Auto-detect trail directory based on agent script location
# This creates: {agent_directory}/trails/agent_trail.jsonl
trail_path = get_agent_trail_path(__file__)
trail = ResponseTrail(path=trail_path)
session_id = str(uuid.uuid4())
```

**Benefits of auto-detection:**
- Each agent's trails are isolated in their own `trails/` directory
- Multiple agents can run without interfering with each other
- Trail path is relative to the agent script, not the working directory

### 1B. Manual Path (Alternative)

```python
from lib.response_logger import ResponseTrail
import uuid

trail = ResponseTrail(path="custom/path/to/trail.jsonl")
session_id = str(uuid.uuid4())
```

### 2. Log Session Events

```python
# Log session start
trail.session_start(session_id, "What is Claude?", "claude-haiku-4-5")

# Log API request
trail.api_request(session_id, turn=1, messages=messages)

# Log API response with latency
import time
t0 = time.perf_counter()
response = await client.messages.create(...)
latency_s = time.perf_counter() - t0
trail.api_response(session_id, turn=1, response=response, latency_s=latency_s)

# Log tool calls
trail.tool_call(session_id, turn=1, name="get_pokemon", tool_id=block.id, tool_input=block.input)

# Log tool results
trail.tool_result(session_id, turn=1, name="get_pokemon", tool_id=block.id, output=result)

# Log session end
trail.session_end(session_id, final_text="...", reason="end_turn")
```

### 3. Replay Offline (No API Calls!)

```python
from lib.response_logger import replay_trail

# Replay all events
replay_trail("trails/agent_trail.jsonl")

# Replay specific session
replay_trail("trails/agent_trail.jsonl", session_id="uuid-xxx")
```

## API Reference

### Utility Functions

#### `get_agent_trail_path(agent_file: Optional[str] = None) -> str`
Get the trail file path for an agent script.

Creates a `trails/` subdirectory in the same location as the agent script,
isolating each agent's trails from other agents.

**Args:**
- `agent_file` (str, optional): Path to the agent script (`__file__`).
  If None, tries to auto-detect from the calling script.

**Returns:**
- Path to trail file: `{agent_directory}/trails/agent_trail.jsonl`

**Example:**
```python
from lib.response_logger import ResponseTrail, get_agent_trail_path

# In stop_reason/main.py
trail_path = get_agent_trail_path(__file__)
# Returns: /path/to/stop_reason/trails/agent_trail.jsonl

trail = ResponseTrail(trail_path)
```

**Use Cases:**
- Isolate trails per agent script
- Multiple agents can run without interfering
- Easy to locate trails relative to agent file

### ResponseTrail

#### `__init__(path: str = "agent_trail.jsonl")`
Initialize the trail logger. Creates subdirectories as needed.

**Args:**
- `path` (str): File path for JSONL trail file.
  Use `get_agent_trail_path(__file__)` to auto-generate path.

**Example:**
```python
from lib.response_logger import ResponseTrail, get_agent_trail_path

# Recommended: auto-detect based on script location
trail_path = get_agent_trail_path(__file__)
trail = ResponseTrail(trail_path)

# Or manual path
trail = ResponseTrail("logs/agent_runs/trail.jsonl")
```

#### `session_start(session_id, prompt, model)`
Log the start of an agentic session.

**Args:**
- `session_id` (str): Unique session identifier
- `prompt` (str): User prompt/input
- `model` (str): Claude model used (e.g., "claude-haiku-4-5")

#### `session_end(session_id, final_text, reason)`
Log the end of an agentic session.

**Args:**
- `session_id` (str): Unique session identifier
- `final_text` (str): Final response text from Claude
- `reason` (str): Termination reason ("end_turn", "max_tokens", "max_turns_exhausted", etc.)

#### `api_request(session_id, turn, messages)`
Log an outgoing request to Claude API.

**Args:**
- `session_id` (str): Unique session identifier
- `turn` (int): Turn number in the agentic loop
- `messages` (List[Dict]): Message list sent to the API

#### `api_response(session_id, turn, response, latency_s)`
Log a response from Claude API.

**Args:**
- `session_id` (str): Unique session identifier
- `turn` (int): Turn number in the agentic loop
- `response` (Any): Full SDK response object
- `latency_s` (float): Request latency in seconds

#### `tool_call(session_id, turn, name, tool_id, tool_input)`
Log a tool call invocation.

**Args:**
- `session_id` (str): Unique session identifier
- `turn` (int): Turn number in the agentic loop
- `name` (str): Tool name
- `tool_id` (str): Unique tool call ID
- `tool_input` (Dict): Input parameters

#### `tool_result(session_id, turn, name, tool_id, output)`
Log a tool execution result.

**Args:**
- `session_id` (str): Unique session identifier
- `turn` (int): Turn number in the agentic loop
- `name` (str): Tool name
- `tool_id` (str): Unique tool call ID
- `output` (Dict): Tool execution output

### Utility Functions

#### `replay_trail(path, session_id=None)`
Replay a saved trail file with formatted output.

**Args:**
- `path` (str): Path to JSONL trail file
- `session_id` (str, optional): Filter to specific session

**Example:**
```python
# Replay all events
replay_trail("trails/agent_trail.jsonl")

# Replay specific session
replay_trail("trails/agent_trail.jsonl", session_id="abc-123")
```

#### `query_trail(path, event_type=None, session_id=None)`
Query trail file and return matching records as a list.

**Args:**
- `path` (str): Path to JSONL trail file
- `event_type` (str, optional): Filter by event type ("api_response", "tool_call", etc.)
- `session_id` (str, optional): Filter by session ID

**Returns:**
- List of matching records (each as a dict)

**Example:**
```python
from lib.response_logger import query_trail

# Get all API responses
responses = query_trail("trail.jsonl", event_type="api_response")

# Get tool calls for a specific session
tool_calls = query_trail("trail.jsonl", 
                        event_type="tool_call", 
                        session_id="abc-123")
```

#### `parse_trail(path, session_id=None, repair_blocks=True)`
Parse a JSONL trail file into a list of structured records, with automatic repair of any legacy stringified SDK block representations.

**Args:**
- `path` (str): Path to JSONL trail file
- `session_id` (str, optional): Filter by session ID
- `repair_blocks` (bool): Whether to auto-convert stringified blocks into dicts (default: True)

**Returns:**
- List of parsed event records (each as a dict)

**Example:**
```python
from lib.response_logger import parse_trail

records = parse_trail("trails/agent_trail.jsonl")
print(f"Loaded {len(records)} events")
```

#### `reconstruct_session_messages(path_or_records, session_id=None)`
Reconstruct the full, replayable conversation message history from trail records for crash recovery and state persistence (Exam Domain 5, TS 5.4).

**Args:**
- `path_or_records` (str or list): Path to trail file or list of trail records
- `session_id` (str, optional): Session ID to reconstruct (defaults to latest session)

**Returns:**
- List of message dicts ready for `client.messages.create(messages=...)`

**Example:**
```python
from lib.response_logger import reconstruct_session_messages

# Reconstruct message state after crash
messages = reconstruct_session_messages("trails/agent_trail.jsonl", session_id="abc-123")

# Resume the agentic loop seamlessly!
response = await client.messages.create(
    model="claude-haiku-4-5",
    messages=messages,
    tools=TOOLS,
)
```

#### `repair_trail_file(source_path, target_path=None)`
Scan an existing trail file, convert any legacy stringified blocks (e.g. `ToolUseBlock(...)`) into valid JSON dictionaries, and save the repaired file.

**Args:**
- `source_path` (str): Path to existing trail file
- `target_path` (str, optional): Destination file path (if None, repairs in-place)

**Returns:**
- Number of records repaired

**Example:**
```python
from lib.response_logger import repair_trail_file

repaired = repair_trail_file("trails/agent_trail.jsonl")
print(f"Repaired {repaired} records")
```

#### `parse_block_repr(text)`
Parse a stringified Python repr (e.g. `ToolUseBlock(...)` or `TextBlock(...)`) into a valid dictionary block.

**Example:**
```python
from lib.response_logger import parse_block_repr

block = parse_block_repr("ToolUseBlock(id='toolu_1', name='get_pokemon', input={'name': 'charizard'})")
# Returns: {'type': 'tool_use', 'id': 'toolu_1', 'name': 'get_pokemon', 'input': {'name': 'charizard'}}
```

## JSONL File Format

Each line is a JSON object with this structure:

```json
{
  "ts": "2024-09-14T12:34:56.789123+00:00",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "api_response",
  "payload": {
    "turn": 1,
    "stop_reason": "tool_use",
    "latency_s": 1.234,
    "raw": { "id": "msg_123", "content": [...], ... }
  }
}
```

**Fields:**
- `ts` (str): ISO 8601 timestamp (UTC)
- `session_id` (str): Unique session identifier
- `event` (str): Event type ("session_start", "api_request", "api_response", "tool_call", "tool_result", "session_end")
- `payload` (dict): Event-specific data

## Example: Full Agentic Loop

```python
import asyncio
import os
import uuid
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import anthropic
from lib.response_logger import ResponseTrail, replay_trail, get_agent_trail_path

load_dotenv()

async def run_agent_with_logging():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    # Initialize trail (auto-detect path relative to this script)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(trail_path)
    session_id = str(uuid.uuid4())
    
    prompt = "What is the capital of France?"
    model = "claude-haiku-4-5"
    
    # Log session start
    trail.session_start(session_id, prompt, model)
    
    messages = [{"role": "user", "content": prompt}]
    
    # Turn 1: API call
    trail.api_request(session_id, turn=1, messages=messages)
    
    t0 = time.perf_counter()
    response = await client.messages.create(
        model=model,
        max_tokens=512,
        messages=messages,
    )
    latency_s = time.perf_counter() - t0
    
    # Log response
    trail.api_response(session_id, turn=1, response=response, latency_s=latency_s)
    
    # Extract text and log session end
    final_text = "".join(b.text for b in response.content if b.type == "text")
    trail.session_end(session_id, final_text, "end_turn")
    
    print(final_text)

# Run and then replay
asyncio.run(run_agent_with_logging())
# Replay uses the same path (trails are in {script_dir}/trails/)
replay_trail(get_agent_trail_path(__file__))
```

## Use Cases

### 🔍 Debugging & Development
- Understand what Claude saw and how it responded
- Review tool calls and results without re-running
- Track latency and performance

### 📋 Compliance & Audit
- Complete audit trail of all API interactions
- Timestamps on every event
- Export for compliance reporting

### 📊 Performance Analysis
- Measure latency per API call
- Identify slow tool calls
- Analyze token usage patterns

### 🎯 ML Model Analysis
- Understand model behavior
- Review stop_reason patterns
- Compare different runs

## Tips & Best Practices

1. **Use unique session IDs** — Makes replaying specific runs easy
   ```python
   import uuid
   session_id = str(uuid.uuid4())
   ```

2. **Log latency for performance** — Helps identify bottlenecks
   ```python
   import time
   t0 = time.perf_counter()
   response = await client.messages.create(...)
   latency_s = time.perf_counter() - t0
   trail.api_response(session_id, turn, response, latency_s)
   ```

3. **Organize trails by date/run** — Makes querying easier
   ```python
   from datetime import datetime
   date_str = datetime.now().strftime("%Y-%m-%d")
   trail = ResponseTrail(f"logs/{date_str}/trail.jsonl")
   ```

4. **Use query_trail for analysis** — Don't just replay, query
   ```python
   from lib.response_logger import query_trail
   all_api_responses = query_trail("trail.jsonl", event_type="api_response")
   avg_latency = sum(r["payload"]["latency_s"] for r in all_api_responses) / len(all_api_responses)
   ```

5. **Handle structured errors** — Return dicts, never raise in tools
   ```python
   async def my_tool(input_data):
       try:
           result = do_work(input_data)
           return {"success": True, "data": result}
       except Exception as e:
           return {"success": False, "error": str(e), "isRetryable": True}
   ```

## See Also

- [stop_reason/main.py](../../stop_reason/main.py) — Full agent example with logging
- [CLAUDE.md](../../CLAUDE.md) — Project overview
- [Anthropic Documentation](https://docs.anthropic.com) — Claude API docs
