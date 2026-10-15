"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.3: Distribute tools appropriately across agents and configure tool choice
Task Statement 2.5: Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively
Exam Scenario 4: Developer Productivity with Claude

Key Exam Concepts Demonstrated:
1. Principle of least privilege: Limiting agent tool suites to 4-5 specialized tools.
2. Tool choice configuration:
   - "auto": Model decides freely whether to call tools or respond directly.
   - "any": Model is strictly forced to invoke a tool, but selects which one.
   - {"type": "tool", "name": "..."}: Forces a specific named tool to execute.
3. Built-in tool selection:
   - Grep: Searching file contents for definitions/callers.
   - Glob: Pattern-matching filenames.
   - Edit fallback: Falling back to Read + Write when Edit fails unique anchor matching.
"""

import fnmatch
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ==============================================================================
# 1. Built-in Tools Simulation (Grep, Glob, Read, Edit Fallback)
# ==============================================================================

class BuiltinToolsEngine:
    """Simulates Claude Code built-in tools for developer productivity."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def glob_files(self, pattern: str) -> List[str]:
        """Glob pattern file finder."""
        matches = []
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        for dirpath, dirnames, filenames in os.walk(str(self.root)):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".venv")]
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
                for line_no, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        results.append({"file": rel_path, "line": line_no, "content": line.strip()})
            except Exception:
                continue
        return results

    def edit_with_fallback(self, rel_path: str, old_str: str, new_str: str) -> Tuple[bool, str]:
        """
        Executes Edit tool. If old_str appears multiple times (non-unique anchor),
        triggers documented fallback: Read followed by Write.
        """
        target_file = self.root / rel_path
        if not target_file.exists():
            return False, f"File {rel_path} does not exist."

        content = target_file.read_text(encoding="utf-8")
        occurrences = content.count(old_str)

        if occurrences == 1:
            target_file.write_text(content.replace(old_str, new_str), encoding="utf-8")
            return True, "Edit executed cleanly with unique text match."
        elif occurrences > 1:
            return False, (
                f"Edit failed: Anchor text '{old_str}' occurs {occurrences} times. "
                "Triggering fallback: Use Read to load surrounding context, then Write full chunk."
            )
        else:
            return False, f"Edit failed: Anchor text '{old_str}' not found in {rel_path}."


# ==============================================================================
# 2. Tool Choice Resolver (Auto vs Any vs Forced)
# ==============================================================================

def resolve_tool_choice_mode(mode: str, target_tool: Optional[str] = None) -> Any:
    """
    Demonstrates Claude API tool_choice options:
    - 'auto': Claude decides freely.
    - 'any': Claude MUST call a tool (guarantees no conversational text cop-out).
    - forced: Claude MUST call the specific tool named in target_tool.
    """
    if mode == "auto":
        return "auto"
    elif mode == "any":
        return "any"
    elif mode == "forced" and target_tool:
        return {"type": "tool", "name": target_tool}
    raise ValueError(f"Invalid mode: {mode}")


def main() -> None:
    engine = BuiltinToolsEngine(REPO_ROOT)
    print("Testing Glob:")
    test_files = engine.glob_files("**/test_*.py")
    print(f"Discovered {len(test_files)} test files.\n")

    print("Testing tool_choice resolution:")
    print("Auto:", resolve_tool_choice_mode("auto"))
    print("Any:", resolve_tool_choice_mode("any"))
    print("Forced:", resolve_tool_choice_mode("forced", "get_customer"))


if __name__ == "__main__":
    main()
