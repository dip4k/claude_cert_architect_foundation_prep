"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.3: Configure subagent invocation, context passing, and spawning
Exam Scenario 3: Multi-Agent Research System

Key Exam Concepts Demonstrated:
1. The Task tool as the mechanism for spawning subagents, requiring allowedTools to include "Task".
2. Parallel subagent spawning: Emitting multiple Task tool calls in a SINGLE coordinator turn
   instead of sequential round-trips.
3. Explicit context passing: Passing complete research findings and instructions in the prompt;
   subagents do not share memory or inherit parent context automatically.
4. Preserving attribution: Separating content from metadata (source URLs, doc titles, page numbers,
   publication dates) in structured payloads.
5. Goal-oriented coordinator prompts: Specifying research goals and quality criteria rather than
   rigid procedural steps.

Manual Execution (WSL Ubuntu):
    uv run domain1/ts_1_3_subagent_invocation_spawning/main.py
"""

import json
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
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

# The coordinator can only spawn subagents if "Task" is in its allowedTools.
COORDINATOR_ALLOWED_TOOLS: List[str] = ["Task"]


# ==============================================================================
# 1. AgentDefinition Specification & Task Tool
# ==============================================================================

@dataclass
class AgentDefinition:
    """Agent definition configuration as tested in Task Statement 1.3."""
    name: str
    description: str
    system_prompt: str
    allowed_tools: List[str]


SUBAGENT_REGISTRY = {
    "web_researcher": AgentDefinition(
        name="web_researcher",
        description="Researches technical topics across web articles and documentation.",
        system_prompt="You are a precise technical researcher. Return findings with structured metadata.",
        allowed_tools=["fetch_url", "search"],
    ),
    "code_analyzer": AgentDefinition(
        name="code_analyzer",
        description="Inspects source code repositories, classes, and architectural structures.",
        system_prompt="You are an expert static code analyst. Trace caller graphs and dependencies.",
        allowed_tools=["grep", "read_file"],
    ),
}

# Coordinator tool declaration: Task tool enables spawning subagents
TASK_TOOL = {
    "name": "Task",
    "description": (
        "Spawns an isolated subagent to perform an asynchronous subtask. "
        "Coordinator can invoke multiple Task calls in a single response for parallel execution."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "subagent_type": {
                "type": "string",
                "enum": ["web_researcher", "code_analyzer"],
                "description": "The registered subagent type to instantiate.",
            },
            "prompt": {
                "type": "string",
                "description": (
                    "Complete, explicit prompt for the subagent. Must include all necessary "
                    "background context since subagents do not inherit coordinator history."
                ),
            },
            "task_metadata": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "expected_output_format": {"type": "string"},
                },
                "required": ["task_id"],
                "description": "Metadata for tracking and correlating subagent tasks.",
            },
        },
        "required": ["subagent_type", "prompt", "task_metadata"],
    },
}


# ==============================================================================
# 2. Simulated Subagent Workers
# ==============================================================================

def execute_subagent_task(subagent_type: str, prompt: str, task_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes subagent task with structured metadata separation for attribution.
    """
    if subagent_type not in SUBAGENT_REGISTRY:
        return {"error": f"Unknown subagent type: {subagent_type}"}

    # Simulate subagent response with structured findings separating content and metadata
    if subagent_type == "web_researcher":
        return {
            "subagent": subagent_type,
            "task_id": task_metadata.get("task_id"),
            "status": "completed",
            "findings": [
                {
                    "content": "Claude Code supports project-level and user-level slash commands and skills.",
                    "metadata": {
                        "source_url": "https://docs.anthropic.com/en/docs/claude-code",
                        "doc_title": "Claude Code User Guide",
                        "collection_date": "2026-10-06",
                    },
                }
            ],
        }
    elif subagent_type == "code_analyzer":
        return {
            "subagent": subagent_type,
            "task_id": task_metadata.get("task_id"),
            "status": "completed",
            "findings": [
                {
                    "content": "Repository has modular rules in .claude/rules/ with glob path scoping.",
                    "metadata": {
                        "filepath": ".claude/rules/domain_exercises.md",
                        "module_type": "path_scoped_rule",
                        "scanned_lines": 45,
                    },
                }
            ],
        }

    return {"error": "Unhandled subagent"}


# ==============================================================================
# 3. Parallel Spawning Coordinator
# ==============================================================================

def run_parallel_spawning_coordinator(
    user_goal: str,
    client: Any,
    trail: ResponseTrail,
    max_turns: int = 4,
    allowed_tools: Optional[List[str]] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Coordinator agent demonstrating parallel subagent spawning via multiple Task calls.

    max_turns is a safety cap (fallback only). The loop ends on stop_reason == "end_turn";
    any other terminal stop_reason raises LoopStopped. Task is only offered to the model
    when "Task" is in allowed_tools.
    """
    allowed = COORDINATOR_ALLOWED_TOOLS if allowed_tools is None else allowed_tools
    tools = [TASK_TOOL] if "Task" in allowed else []

    session_id = str(uuid.uuid4())
    trail.session_start(session_id, user_goal, COORDINATOR_MODEL)
    parser = create_parser()

    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"Goal: {user_goal}\n\n"
                "You have access to the Task tool to spawn subagents ('web_researcher' and 'code_analyzer').\n"
                "Each subagent starts with an empty context, so put every fact it needs in its prompt. "
                "State the goal and the quality criteria, not step-by-step instructions. "
                "If several independent angles are needed, emit multiple Task tool calls in a SINGLE "
                "response so they run in parallel."
            ),
        }
    ]

    all_spawned_results: List[Dict[str, Any]] = []

    for turn in range(1, max_turns + 1):
        trail.api_request(session_id, turn, messages)
        request: Dict[str, Any] = {
            "model": COORDINATOR_MODEL,
            "max_tokens": 1500,
            "messages": messages,
        }
        if tools:
            request["tools"] = tools
        response = client.messages.create(**request)

        stop_reason = read_stop_reason(parser, response)

        if stop_reason == "tool_use":
            # Echo assistant content unchanged (including any thinking blocks and signatures).
            messages.append({"role": "assistant", "content": response.content})

            tool_blocks = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
            task_blocks = [b for b in tool_blocks if b.name == "Task"]

            for block in task_blocks:
                trail.tool_call(session_id, turn, "Task", block.id, block.input)

            # map() keeps results in task_blocks order while subagents run concurrently.
            with ThreadPoolExecutor(max_workers=max(1, len(task_blocks))) as pool:
                task_results = list(pool.map(
                    lambda b: execute_subagent_task(
                        subagent_type=b.input["subagent_type"],
                        prompt=b.input["prompt"],
                        task_metadata=b.input["task_metadata"],
                    ),
                    task_blocks,
                ))
            result_by_id = {b.id: r for b, r in zip(task_blocks, task_results)}

            # Every tool_use block needs exactly one tool_result, in the same order.
            tool_results = []
            for block in tool_blocks:
                if block.id in result_by_id:
                    subagent_result = result_by_id[block.id]
                    trail.tool_result(session_id, turn, "Task", block.id, subagent_result)
                    all_spawned_results.append(subagent_result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(subagent_result),
                    })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({"error": f"Tool not allowed: {block.name}"}),
                        "is_error": True,
                    })

            messages.append({"role": "user", "content": tool_results})

        elif stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})

        elif stop_reason == "end_turn":
            final_text = response_text(response)
            trail.session_end(session_id, final_text, "end_turn")
            return final_text, all_spawned_results

        else:
            text = response_text(response)
            trail.session_end(session_id, text, stop_status(stop_reason))
            raise LoopStopped(stop_reason, text)

    trail.session_end(session_id, "", "safety_cap_reached")
    return "", all_spawned_results


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    prompt = (
        "Investigate Claude Code slash commands: research official documentation using web_researcher, "
        "and analyze local rule configs using code_analyzer. Spawn both tasks in parallel."
    )
    res, tasks = run_parallel_spawning_coordinator(prompt, client, trail)
    print("\n--- Coordinator Result ---")
    print(res)
    print(f"\nSpawned Subagent Tasks: {len(tasks)}")


if __name__ == "__main__":
    main()
