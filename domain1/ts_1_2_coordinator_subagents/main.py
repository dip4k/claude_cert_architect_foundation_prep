"""
Domain 1: Agentic Architecture & Orchestration
Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns
Exam Scenario 3: Multi-Agent Research System

Key Exam Concepts Demonstrated:
1. Hub-and-spoke architecture: A coordinator manages all inter-subagent communication,
   error handling, and routing.
2. Context isolation: Subagents operate with isolated context—they do NOT automatically
   inherit coordinator history.
3. Query-complexity routing: Coordinator dynamically chooses which subagents to invoke
   rather than forcing every query through a monolithic rigid pipeline.
4. Iterative refinement loops: Coordinator inspects synthesis outputs for coverage gaps,
   re-delegates targeted follow-up queries, and re-synthesizes until coverage is complete.
5. ResponseTrail logging for JSONL audit trail of all coordinator and subagent interactions.

Manual Execution (WSL Ubuntu):
    uv run domain1/ts_1_2_coordinator_subagents/main.py
"""

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
# 1. Specialized Subagents (Isolated Contexts)
# ==============================================================================

class WebSearchSubagent:
    """Subagent specialized in retrieving external research snippets."""

    MOCK_KB: Dict[str, str] = {
        "claude agent sdk": (
            "Claude Agent SDK provides primitives for building autonomous agentic loops, "
            "subagent delegation via Task tool, hooks, and session resumption."
        ),
        "mcp tool error patterns": (
            "Model Context Protocol (MCP) tool errors should return isError: true with "
            "structured categories (transient, validation, business, permission) and isRetryable booleans."
        ),
        "context window preservation": (
            "Managing large context requires trimming tool outputs, extracting immutable case facts "
            "outside conversation summaries, and using scratchpads."
        ),
    }

    def execute(self, query: str) -> Dict[str, Any]:
        """Runs with isolated context. Only receives query in its input."""
        norm_query = query.lower()
        matched = []
        for key, text in self.MOCK_KB.items():
            if any(word in norm_query for word in key.split()):
                matched.append({"topic": key, "content": text})

        if not matched:
            return {
                "source": "web_search",
                "query": query,
                "found": False,
                "findings": "No matching external articles found for query.",
            }

        return {
            "source": "web_search",
            "query": query,
            "found": True,
            "findings": matched,
        }


class DocumentAnalysisSubagent:
    """Subagent specialized in deep document extraction and data breakdown."""

    def execute(self, document_id: str, focus_topic: str) -> Dict[str, Any]:
        """Runs with isolated context."""
        return {
            "source": "doc_analysis",
            "doc_id": document_id,
            "focus": focus_topic,
            "key_metrics": [
                {"metric": "Passing score", "value": "720/1000"},
                {"metric": "Question count", "value": "60 questions"},
                {"metric": "Time limit", "value": "120 minutes"},
            ],
            "attribution": {"author": "Anthropic Certification Program", "version": "0.2"},
        }


class SynthesisSubagent:
    """Subagent specialized in combining findings and evaluating coverage gaps."""

    def execute(self, research_findings: List[Dict[str, Any]], required_topics: List[str]) -> Dict[str, Any]:
        """Synthesizes findings and flags missing required topics."""
        aggregated_text = []
        covered_topics = set()

        for item in research_findings:
            if item.get("source") == "web_search" and item.get("found"):
                for entry in item.get("findings", []):
                    covered_topics.add(entry["topic"])
                    aggregated_text.append(f"Web Finding [{entry['topic']}]: {entry['content']}")
            elif item.get("source") == "doc_analysis":
                aggregated_text.append(f"Doc Finding [{item['doc_id']}]: {json.dumps(item.get('key_metrics', []))}")

        # Check coverage gaps
        missing_topics = [t for t in required_topics if not any(t.lower() in c.lower() for c in covered_topics)]

        return {
            "source": "synthesis",
            "coverage_sufficient": len(missing_topics) == 0,
            "missing_topics": missing_topics,
            "synthesized_report": "\n\n".join(aggregated_text),
        }


# ==============================================================================
# 2. Coordinator Tools
# ==============================================================================

COORDINATOR_TOOLS = [
    {
        "name": "delegate_web_search",
        "description": "Delegates a specific web search query to the Web Search Subagent (isolated context).",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Specific search query."}},
            "required": ["query"],
        },
    },
    {
        "name": "delegate_doc_analysis",
        "description": "Delegates document extraction to the Document Analysis Subagent (isolated context).",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID of document to analyze."},
                "focus_topic": {"type": "string", "description": "Specific focus topic."},
            },
            "required": ["document_id", "focus_topic"],
        },
    },
    {
        "name": "evaluate_synthesis",
        "description": "Delegates accumulated findings to the Synthesis Subagent to compile report and evaluate coverage gaps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "required_topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of essential topics that must be covered in report.",
                }
            },
            "required": ["required_topics"],
        },
    },
]


# ==============================================================================
# 3. Hub-and-Spoke Coordinator Engine
# ==============================================================================

class MultiAgentCoordinator:
    """Hub-and-spoke coordinator managing all subagent routing and iteration."""

    def __init__(self, client: Any, trail: ResponseTrail) -> None:
        self.client = client
        self.trail = trail
        self.web_agent = WebSearchSubagent()
        self.doc_agent = DocumentAnalysisSubagent()
        self.synthesis_agent = SynthesisSubagent()
        self.accumulated_findings: List[Dict[str, Any]] = []

    def dispatch_tool(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Routes communication exclusively through the coordinator."""
        if name == "delegate_web_search":
            result = self.web_agent.execute(inputs["query"])
            self.accumulated_findings.append(result)
            return result
        elif name == "delegate_doc_analysis":
            result = self.doc_agent.execute(inputs["document_id"], inputs["focus_topic"])
            self.accumulated_findings.append(result)
            return result
        elif name == "evaluate_synthesis":
            return self.synthesis_agent.execute(self.accumulated_findings, inputs["required_topics"])
        return {"error": f"Unknown coordinator tool: {name}"}

    def run_research_pipeline(
        self,
        user_query: str,
        max_turns: int = 5,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Coordinator loop with iterative synthesis refinement.

        max_turns is a safety cap (fallback only). The loop ends on stop_reason == "end_turn";
        any other terminal stop_reason raises LoopStopped.
        """
        session_id = str(uuid.uuid4())
        self.trail.session_start(session_id, user_query, COORDINATOR_MODEL)
        parser = create_parser()

        messages: List[Dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"Coordinator Task: Research the following request comprehensively:\n'{user_query}'\n\n"
                    "Instructions:\n"
                    "1. Break the topic into subtasks that cover ALL its major areas, and give each "
                    "subagent a distinct slice so work is not duplicated.\n"
                    "2. Select subagents by query complexity; answer simple questions directly.\n"
                    "3. Pass all findings to evaluate_synthesis.\n"
                    "4. If synthesis reports missing_topics, re-delegate follow-up searches until complete."
                ),
            }
        ]

        for turn in range(1, max_turns + 1):
            self.trail.api_request(session_id, turn, messages)
            response = self.client.messages.create(
                model=COORDINATOR_MODEL,
                max_tokens=1500,
                tools=COORDINATOR_TOOLS,
                messages=messages,
            )

            stop_reason = read_stop_reason(parser, response)

            if stop_reason == "tool_use":
                # Echo assistant content unchanged (including any thinking blocks and signatures).
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if getattr(block, "type", "") == "tool_use":
                        tool_name = block.name
                        tool_id = block.id
                        tool_input = block.input

                        self.trail.tool_call(session_id, turn, tool_name, tool_id, tool_input)
                        result = self.dispatch_tool(tool_name, tool_input)
                        self.trail.tool_result(session_id, turn, tool_name, tool_id, result)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result),
                        })

                messages.append({"role": "user", "content": tool_results})

            elif stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})

            elif stop_reason == "end_turn":
                final_text = response_text(response)
                self.trail.session_end(session_id, final_text, "end_turn")
                return final_text, self.accumulated_findings

            else:
                text = response_text(response)
                self.trail.session_end(session_id, text, stop_status(stop_reason))
                raise LoopStopped(stop_reason, text)

        self.trail.session_end(session_id, "", "safety_cap_reached")
        return "", self.accumulated_findings


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY missing in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    coordinator = MultiAgentCoordinator(client, trail)
    prompt = "Research Claude Agent SDK and MCP Tool Error Patterns for the foundations exam."
    report, findings = coordinator.run_research_pipeline(prompt)
    print("\n--- Final Coordinator Synthesized Output ---")
    print(report)
    print(f"\nTotal subagent findings gathered: {len(findings)}")


if __name__ == "__main__":
    main()
