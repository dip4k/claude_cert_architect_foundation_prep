"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.1: Design and implement agentic loops for autonomous task execution

Exercise: Build a Multi-Tool Agent Loop
Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/build-a-tool-using-agent

Demonstrates:
- The agentic loop lifecycle: send request -> inspect stop_reason -> execute tool -> repeat
- stop_reason as the sole, deterministic loop-control signal ("tool_use" vs "end_turn")
- Appending tool results to conversation history so Claude can reason about them
- A safety iteration cap (MAX_ITERATIONS) used ONLY as a fallback bound, not the primary
  stopping mechanism
- sdk_parser_py for structured response parsing
- response_logger for full JSONL audit trail + offline replay
"""

import ast
import json
import operator
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import anthropic
from dotenv import load_dotenv

from domain1.loop_common import (
    COORDINATOR_MODEL,
    LoopStopped,
    read_stop_reason,
    response_text,
    stop_status,
)
from lib.sdk_parser_py import create_parser, format_stop_reason
from lib.response_logger import ResponseTrail, get_agent_trail_path, replay_trail

load_dotenv()

# Safety cap only: a fallback bound, never the primary stopping mechanism.
# Normal queries must terminate via stop_reason well before this is reached.
MAX_ITERATIONS = 20

AGENT_MODEL = COORDINATOR_MODEL


# ==============================================================================
# 1. Tool implementations
# ==============================================================================

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    """Evaluate an arithmetic AST node without using eval()."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression element: {ast.dump(node)}")


def calculator_tool(expression: str) -> Dict[str, Any]:
    """Evaluates a basic arithmetic expression and returns the numeric result."""
    try:
        tree = ast.parse(expression, mode="eval")
        return {"expression": expression, "result": _safe_eval(tree.body)}
    except Exception as e:
        return {"expression": expression, "error": f"Could not evaluate expression: {e}"}


# Mock web search index: maps known query keywords to a canned factual snippet.
MOCK_SEARCH_INDEX = {
    "tokyo population": (
        "As of 2024, the Greater Tokyo Area has an estimated population of "
        "37,400,000 people, making it the most populous metropolitan area in the world."
    ),
    "speed of light": "The speed of light in a vacuum is 299,792,458 meters per second.",
    "everest height": "Mount Everest stands at 8,849 meters (29,032 feet) above sea level.",
    "average human heart rate": "The average resting human heart rate is 72 beats per minute.",
}


def web_search_tool(query: str) -> Dict[str, Any]:
    """Mock web search stub: returns a canned snippet for known queries."""
    normalized = query.strip().lower()
    for key, snippet in MOCK_SEARCH_INDEX.items():
        if all(word in normalized for word in key.split()):
            return {"query": query, "results": [{"title": key.title(), "snippet": snippet}]}
    return {
        "query": query,
        "results": [{"title": "No match", "snippet": f"No mock data available for '{query}'."}],
    }


def execute_tool(name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches a tool_use request to the corresponding local function."""
    if name == "calculator":
        return calculator_tool(tool_input.get("expression", ""))
    if name == "web_search":
        return web_search_tool(tool_input.get("query", ""))
    return {"error": f"Unknown tool: '{name}'"}


# ==============================================================================
# 2. Tool declarations (Anthropic API tool schema)
# ==============================================================================

TOOLS = [
    {
        "name": "calculator",
        "description": (
            "Evaluates a basic arithmetic expression (+, -, *, /, parentheses, exponent) and "
            "returns the numeric result. Use this whenever the user needs a computation "
            "performed, including calculations that use a value obtained from web_search. "
            "Does not handle unit conversion, symbolic math, or non-arithmetic expressions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid arithmetic expression, e.g. '37400000 * 0.15'.",
                },
            },
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Searches the web for up-to-date facts, statistics, or general knowledge and "
            "returns short snippets with titles. Use this when the user asks about "
            "information that could be current or that you are not certain of (e.g. "
            "populations, prices, measurements). Returns mock results in this practice "
            "environment; does not perform calculations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'current population of Tokyo'.",
                },
            },
            "required": ["query"],
        },
    },
]

parser = create_parser()


# ==============================================================================
# 3. The agentic loop
# ==============================================================================

def run_agent(prompt: str, client: Any, trail: ResponseTrail,
              model: str = AGENT_MODEL) -> str:
    """
    Agentic loop lifecycle:
      1. Send the conversation to Claude.
      2. Inspect response.stop_reason - the ONLY signal used for control flow.
         - "tool_use": execute the requested tool(s), append results, loop again.
         - "pause_turn": append the assistant turn unchanged and loop again.
         - "end_turn": Claude is done; extract and return the final text.
         - max_tokens / stop_sequence / refusal / unknown: raise LoopStopped.
      3. MAX_ITERATIONS is a safety cap (fallback only), never the normal exit.
    """
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, model)

    print("\n" + "=" * 70)
    print(f"User Prompt: {prompt}")
    print(f"Session ID: {session_id[:8]}...")
    print("=" * 70)

    messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]
    iterations = 0

    while True:
        iterations += 1

        if iterations > MAX_ITERATIONS:
            print(f"WARNING: safety cap of {MAX_ITERATIONS} iterations reached without end_turn.")
            trail.session_end(session_id, "", "safety_cap_reached")
            return ""

        print(f"\n--- Iteration {iterations} ---")
        trail.api_request(session_id, iterations, messages)

        t0 = time.perf_counter()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        latency_s = time.perf_counter() - t0
        trail.api_response(session_id, iterations, response, latency_s)

        stop_reason = read_stop_reason(parser, response)
        print(f"stop_reason: {stop_reason} ({format_stop_reason(str(stop_reason))})  [{latency_s:.2f}s]")

        text = response_text(response)
        if text:
            print(f"Claude: {text}")

        if stop_reason == "tool_use":
            # Echo the assistant content unchanged (tool_use plus any thinking blocks and signatures).
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if getattr(block, "type", "") != "tool_use":
                    continue
                print(f"Tool call: {block.name}({json.dumps(block.input)})")
                trail.tool_call(session_id, iterations, block.name, block.id, block.input)

                result = execute_tool(block.name, block.input)
                print(f"Tool result [{block.name}]: {json.dumps(result)}")
                trail.tool_result(session_id, iterations, block.name, block.id, result)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            # Feed results back so the model can incorporate them into its next decision.
            messages.append({"role": "user", "content": tool_results})
            continue

        if stop_reason == "pause_turn":
            # Send the paused assistant turn back unchanged so Claude can continue.
            messages.append({"role": "assistant", "content": response.content})
            continue

        if stop_reason == "end_turn":
            trail.session_end(session_id, text, "end_turn")
            return text

        # max_tokens, stop_sequence, refusal or an unknown value: never treat as success.
        trail.session_end(session_id, text, stop_status(stop_reason))
        raise LoopStopped(stop_reason, text)


# ==============================================================================
# 4. Entry point
# ==============================================================================

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY in your environment or .env file.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(trail_path)

    # Single tool call
    run_agent("What is 234 * 18?", client, trail)

    # Sequential multi-tool call: search first, then calculate using the search result.
    run_agent(
        "Search for the current population of Tokyo, then calculate 15% of that population.",
        client,
        trail,
    )

    print("\nREPLAYING TRAIL (offline, no API calls)...\n")
    replay_trail(trail_path)


if __name__ == "__main__":
    main()
