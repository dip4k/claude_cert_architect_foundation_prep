"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.5: Select and Apply Built-in Tools (Read, Write, Edit, Bash, Grep, Glob) Effectively
Exam Scenario 4: Developer Productivity with Claude

Key Concepts:
- Grep: Searching file contents for symbol definitions/references.
- Glob: Matching file paths by pattern.
- Edit: Surgical string replacement requiring unique anchor matches.
- Edit Fallback: Expanding anchor lines or falling back to Read + Write when Edit fails.
"""

import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class BuiltinToolbox:
    """Simulates Claude Code's built-in file and search tools with safe fallbacks."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def glob_files(self, pattern: str) -> List[str]:
        """Locates files matching a glob pattern."""
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

    def grep_search(self, regex_pattern: str, file_pattern: str = "*") -> List[Dict[str, Any]]:
        """Searches file contents using regex across matching files."""
        results = []
        compiled = re.compile(regex_pattern)
        for rel_path in self.glob_files(file_pattern):
            full_path = self.root / rel_path
            try:
                lines = full_path.read_text(encoding="utf-8").splitlines()
                for line_no, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        results.append({
                            "file": rel_path,
                            "line": line_no,
                            "content": line.strip()
                        })
            except Exception:
                continue
        return results

    def read_file(self, rel_path: str, offset: int = 1, limit: Optional[int] = None) -> Dict[str, Any]:
        """Reads file content with optional line slicing."""
        full_path = self.root / rel_path
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}
        
        lines = full_path.read_text(encoding="utf-8").splitlines()
        total_lines = len(lines)
        start_idx = max(0, offset - 1)
        end_idx = total_lines if limit is None else min(total_lines, start_idx + limit)
        selected_lines = lines[start_idx:end_idx]

        return {
            "success": True,
            "file": rel_path,
            "total_lines": total_lines,
            "start_line": offset,
            "end_line": end_idx,
            "content": "\n".join(selected_lines)
        }

    def edit_file(self, rel_path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """
        Surgically replaces old_str with new_str.
        Fails if old_str is not found or matches multiple times (ambiguous anchor).
        """
        full_path = self.root / rel_path
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}

        content = full_path.read_text(encoding="utf-8")
        occurrences = content.count(old_str)

        if occurrences == 0:
            return {
                "success": False,
                "error": "Target string not found",
                "occurrences": 0,
                "recovery_suggestion": "Read file to verify exact whitespace and surrounding context"
            }
        elif occurrences > 1:
            return {
                "success": False,
                "error": f"Ambiguous edit: target string matches {occurrences} locations",
                "occurrences": occurrences,
                "recovery_suggestion": "Expand old_str with unique surrounding lines, or fallback to Read+Write"
            }

        new_content = content.replace(old_str, new_str, 1)
        full_path.write_text(new_content, encoding="utf-8")
        return {
            "success": True,
            "file": rel_path,
            "occurrences": 1,
            "message": "Replacement applied successfully"
        }

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Creates or completely overwrites a file."""
        full_path = self.root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {"success": True, "file": rel_path, "bytes_written": len(content)}

    def execute_edit_with_fallback(self, rel_path: str, old_str: str, new_str: str, unique_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Applies the standard Claude Code fallback protocol:
        1. Attempt surgical edit.
        2. If ambiguous, try with expanded unique context.
        3. If still ambiguous, read full content and apply write replacement.
        """
        initial_result = self.edit_file(rel_path, old_str, new_str)
        if initial_result["success"]:
            return {"status": "EDIT_SUCCESS", "result": initial_result}

        # Step 2: Try with unique context if provided
        if unique_context:
            context_result = self.edit_file(rel_path, unique_context, unique_context.replace(old_str, new_str))
            if context_result["success"]:
                return {"status": "EDIT_RETRY_SUCCESS", "result": context_result}

        # Step 3: Fall back to Read + Write
        read_result = self.read_file(rel_path)
        if not read_result["success"]:
            return {"status": "FAILED", "error": read_result["error"]}

        full_content = read_result["content"]
        # In full rewrite mode, replace the first occurrence or targeted section
        if old_str in full_content:
            rewritten = full_content.replace(old_str, new_str, 1)
            write_result = self.write_file(rel_path, rewritten)
            return {
                "status": "FALLBACK_WRITE_SUCCESS",
                "message": "Fell back to Read + Write due to anchor ambiguity",
                "result": write_result
            }

        return {"status": "FAILED", "error": "Target string missing even after read inspection"}


def main() -> None:
    print("=" * 70)
    print("TS 2.5: Built-in Tools Selection & Fallback Protocol Demo")
    print("=" * 70)
    
    workspace = Path("/tmp/claude_ts25_demo") if os.name != "nt" else Path("./scratch/ts25_demo")
    workspace.mkdir(parents=True, exist_ok=True)
    
    toolbox = BuiltinToolbox(workspace)
    sample_file = "service.py"
    toolbox.write_file(sample_file, "def compute():\n    return 42\n\ndef helper():\n    return 42\n")
    
    print("\n1. Testing ambiguous edit on 'return 42':")
    res1 = toolbox.edit_file(sample_file, "return 42", "return 100")
    print(f"Result: {res1['error']} (Occurrences: {res1.get('occurrences')})")
    
    print("\n2. Applying fallback protocol with unique context:")
    res2 = toolbox.execute_edit_with_fallback(
        sample_file, 
        old_str="return 42", 
        new_str="return 100", 
        unique_context="def compute():\n    return 42"
    )
    print(f"Fallback status: {res2['status']}")
    
    # Read verified
    verified = toolbox.read_file(sample_file)
    print("\n3. Verified final file content:\n" + verified["content"])


if __name__ == "__main__":
    main()
