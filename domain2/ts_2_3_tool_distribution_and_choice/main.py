"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.3: Distribute tools across agents and configure tool_choice
Exam Scenarios 4 (Developer Productivity) and 3 (Research)

Key Exam Concepts Demonstrated:
1. Least privilege: 4-5 scoped tools per role beats one agent with 18 tools
   (`ROLE_TOOLSETS`, `check_tool_budget`).
2. Constrained replacement: `load_document` (allow-listed hosts) instead of open `fetch_url`.
3. Scoped cross-role tool: `verify_fact` gives the synthesis agent a cheap fact check;
   complex cases still go through the coordinator.
4. tool_choice: auto (may return text), any (must call some tool), forced
   {"type": "tool", "name": ...}. With extended thinking only auto or none are legal; any or
   forced is HTTP 400 (`validate_request_params`). Force a first step on a request WITHOUT
   thinking (`tool_choice_for_turn`), then use auto on later turns.
5. Models: claude-sonnet-4-5 coordinator, claude-haiku-4-5 workers (module constants).

This module makes no API calls.
"""

import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

COORDINATOR_MODEL = "claude-sonnet-4-5"  # orchestration and reasoning
WORKER_MODEL = "claude-haiku-4-5"  # scoped subagents
MAX_TOOLS_PER_AGENT = 5
MIN_THINKING_BUDGET = 1024

# ==============================================================================
# 1. Tool distribution: scoped toolsets per role
# ==============================================================================

# Anti-pattern: every tool handed to one agent.
MONOLITH_TOOLS: List[str] = [
    "get_customer", "lookup_order", "process_refund", "escalate_to_human", "web_search",
    "fetch_url", "analyze_document", "summarize_content", "extract_metadata", "verify_fact",
    "query_inventory", "send_email", "create_ticket", "update_ticket", "run_sql",
    "read_file", "write_file", "delete_record",
]  # fmt: skip

ROLE_TOOLSETS: Dict[str, List[str]] = {
    "support": ["get_customer", "lookup_order", "process_refund", "escalate_to_human"],
    "search": ["web_search", "load_document", "extract_metadata"],
    "synthesis": ["summarize_content", "verify_fact"],
    "coordinator": ["delegate_task", "ask_user", "escalate_to_human"],
}


def tools_for_role(role: str) -> List[str]:
    """Return the scoped tool names for a role; unknown roles get no tools."""
    return list(ROLE_TOOLSETS.get(role, []))


def check_tool_budget(
    tool_names: List[str], max_tools: int = MAX_TOOLS_PER_AGENT
) -> List[str]:
    """Return problems when an agent holds too many tools or duplicate names."""
    problems: List[str] = []
    if len(tool_names) > max_tools:
        problems.append(f"{len(tool_names)} tools exceeds the budget of {max_tools}")
    if len(set(tool_names)) != len(tool_names):
        problems.append("duplicate tool names")
    return problems


def model_for_role(role: str) -> str:
    """Coordinator reasons on Sonnet 4.5; every scoped worker runs on Haiku 4.5."""
    return COORDINATOR_MODEL if role == "coordinator" else WORKER_MODEL


# ==============================================================================
# 2. Constrained and scoped tools
# ==============================================================================

ALLOWED_DOC_HOSTS = ("docs.example.com", "kb.example.com")


def load_document(url: str, allowed_hosts: Tuple[str, ...] = ALLOWED_DOC_HOSTS) -> Dict[str, Any]:
    """Constrained replacement for fetch_url: https only, allow-listed hosts only."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return {
            "isError": True,
            "errorCategory": "validation",
            "isRetryable": False,
            "message": f"Only https URLs on {', '.join(allowed_hosts)} can be loaded.",
        }
    return {"isError": False, "url": url, "content": f"(document body of {url})"}


def verify_fact(
    claim: str, source_id: str, sources: Dict[str, str]
) -> Dict[str, Any]:
    """Scoped cross-role tool: check one claim against one known source text."""
    text = sources.get(source_id)
    if text is None:
        return {"isError": False, "verdict": "not_found", "source_id": source_id}
    verdict = "supported" if claim.lower() in text.lower() else "not_found"
    return {"isError": False, "verdict": verdict, "source_id": source_id}


# ==============================================================================
# 3. tool_choice and request validation
# ==============================================================================


def resolve_tool_choice_mode(mode: str, target_tool: Optional[str] = None) -> Any:
    """Return a short label: 'auto', 'any', or the forced-tool object (see build_tool_choice)."""
    if mode == "auto":
        return "auto"
    if mode == "any":
        return "any"
    if mode == "forced" and target_tool:
        return {"type": "tool", "name": target_tool}
    raise ValueError(f"Invalid mode: {mode}")


def build_tool_choice(mode: str, target_tool: Optional[str] = None) -> Dict[str, Any]:
    """Return the API-shaped tool_choice object for auto, any, none or forced."""
    if mode in ("auto", "any", "none"):
        return {"type": mode}
    if mode == "forced" and target_tool:
        return {"type": "tool", "name": target_tool}
    raise ValueError(f"Invalid mode: {mode}")


def tool_choice_for_turn(turn: int, first_tool: str = "extract_metadata") -> Dict[str, Any]:
    """Force the mandatory first tool on turn 1, then let Claude decide (auto)."""
    if turn == 1:
        return build_tool_choice("forced", first_tool)
    return build_tool_choice("auto")


def validate_request_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Reject request shapes the API refuses when extended thinking is on; return params."""
    thinking = params.get("thinking")
    if not thinking:
        return params
    choice = params.get("tool_choice", {"type": "auto"})
    if choice.get("type") not in ("auto", "none"):
        raise ValueError("With thinking, tool_choice must be auto or none (any/forced = HTTP 400)")
    budget = thinking.get("budget_tokens", 0)
    if budget < MIN_THINKING_BUDGET or budget >= params.get("max_tokens", 0):
        raise ValueError("budget_tokens must be >= 1024 and < max_tokens")
    if "temperature" in params:
        raise ValueError("Omit temperature when thinking is enabled (HTTP 400)")
    if "top_k" in params:
        raise ValueError("Leave top_k unset when thinking is enabled")
    if "top_p" in params and not 0.95 <= params["top_p"] <= 1.0:
        raise ValueError("top_p must be between 0.95 and 1.0 when thinking is enabled")
    return params


def build_request_params(
    role: str,
    messages: List[Dict[str, Any]],
    tool_choice: Dict[str, Any],
    thinking_budget: Optional[int] = None,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Build and validate messages.create kwargs for a role (no temperature is ever set)."""
    params: Dict[str, Any] = {
        "model": model_for_role(role),
        "max_tokens": max_tokens,
        "messages": messages,
        "tool_choice": tool_choice,
    }
    if thinking_budget is not None:
        params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
    return validate_request_params(params)


# ==============================================================================
# 4. Built-in tools simulation (kept for TS 2.5 cross-reference)
# ==============================================================================


class BuiltinToolsEngine:
    """Simulates Claude Code built-in tools (Glob, Grep, Edit) for developer productivity."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def glob_files(self, pattern: str) -> List[str]:
        """Glob pattern file finder (matches paths, never contents)."""
        matches = []
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
        for dirpath, dirnames, filenames in os.walk(str(self.root)):
            dirnames[:] = [
                d for d in dirnames if d not in ignore_dirs and not d.startswith(".venv")
            ]
            rel_dir = os.path.relpath(dirpath, str(self.root)).replace("\\", "/")
            for fname in filenames:
                rel = f"{rel_dir}/{fname}" if rel_dir != "." else fname
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(fname, pattern):
                    matches.append(rel)
        return sorted(matches)

    def grep_content(self, regex_pattern: str, file_pattern: str = "*") -> List[Dict[str, Any]]:
        """Grep content pattern searcher across files."""
        results = []
        compiled = re.compile(regex_pattern)
        for rel_path in self.glob_files(file_pattern):
            full_path = self.root / rel_path
            try:
                lines = full_path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for line_no, line in enumerate(lines, start=1):
                if compiled.search(line):
                    results.append({"file": rel_path, "line": line_no, "content": line.strip()})
        return results

    def edit_with_fallback(self, rel_path: str, old_str: str, new_str: str) -> Tuple[bool, str]:
        """Edit when old_str is unique; otherwise report that Read + Write is required."""
        target_file = self.root / rel_path
        if not target_file.exists():
            return False, f"File {rel_path} does not exist."

        content = target_file.read_text(encoding="utf-8")
        occurrences = content.count(old_str)

        if occurrences == 1:
            target_file.write_text(content.replace(old_str, new_str), encoding="utf-8")
            return True, "Edit executed cleanly with unique text match."
        if occurrences > 1:
            return False, (
                f"Edit failed: Anchor text '{old_str}' occurs {occurrences} times. "
                "Triggering fallback: Use Read to load surrounding context, then Write full chunk."
            )
        return False, f"Edit failed: Anchor text '{old_str}' not found in {rel_path}."


def main() -> None:
    """Offline demo: scoped toolsets, tool_choice shapes and the thinking constraint."""
    print("Monolith:", check_tool_budget(MONOLITH_TOOLS))
    for role, names in ROLE_TOOLSETS.items():
        print(f"{role}: {len(names)} tools, problems={check_tool_budget(names)}")
    print("Turn 1:", tool_choice_for_turn(1), "| Turn 2:", tool_choice_for_turn(2))
    try:
        build_request_params("coordinator", [], build_tool_choice("any"), thinking_budget=2000)
    except ValueError as exc:
        print("Rejected:", exc)


if __name__ == "__main__":
    main()
