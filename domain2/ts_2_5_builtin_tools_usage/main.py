"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.5: Select and apply built-in tools (Grep, Glob, Read, Write, Edit) effectively
Exam Scenario 4: Developer Productivity with Claude

Key Concepts:
- Grep searches file CONTENT; Glob matches file PATHS; Read/Write handle whole files.
- Edit replaces text that is UNIQUE in the file. If the text is not unique, the fallback is
  Read + Write (or expand the anchor with surrounding lines).
- Build understanding incrementally: Grep for entry points, Read the imports, then trace usage
  through wrapper modules by listing the exported names and grepping each one
  (`list_exported_names`, `trace_usage`).

This module makes no API calls.
"""

import ast
import fnmatch
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}


class BuiltinToolbox:
    """Simulates Claude Code's built-in file and search tools with safe fallbacks."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def glob_files(self, pattern: str) -> List[str]:
        """Glob: locate files whose PATH matches a pattern (never reads contents)."""
        matches = []
        for dirpath, dirnames, filenames in os.walk(str(self.root)):
            dirnames[:] = [
                d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".venv")
            ]
            rel_dir = os.path.relpath(dirpath, str(self.root)).replace("\\", "/")
            for fname in filenames:
                rel = f"{rel_dir}/{fname}" if rel_dir != "." else fname
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(fname, pattern):
                    matches.append(rel)
        return sorted(matches)

    def grep_search(self, regex_pattern: str, file_pattern: str = "*") -> List[Dict[str, Any]]:
        """Grep: search file CONTENT with a regex across files matching file_pattern."""
        results = []
        compiled = re.compile(regex_pattern)
        for rel_path in self.glob_files(file_pattern):
            try:
                lines = (self.root / rel_path).read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for line_no, line in enumerate(lines, start=1):
                if compiled.search(line):
                    results.append({"file": rel_path, "line": line_no, "content": line.strip()})
        return results

    def read_file(
        self, rel_path: str, offset: int = 1, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read: whole file, or a window of `limit` lines starting at line `offset`."""
        full_path = self.root / rel_path
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}

        lines = full_path.read_text(encoding="utf-8").splitlines()
        total_lines = len(lines)
        start_idx = max(0, offset - 1)
        end_idx = total_lines if limit is None else min(total_lines, start_idx + limit)
        return {
            "success": True,
            "file": rel_path,
            "total_lines": total_lines,
            "start_line": offset,
            "end_line": end_idx,
            "content": "\n".join(lines[start_idx:end_idx]),
        }

    def edit_file(self, rel_path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """Edit: replace old_str once. Fails when it is missing or matches several places."""
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
                "recovery_suggestion": "Read the file to verify exact whitespace and context",
            }
        if occurrences > 1:
            return {
                "success": False,
                "error": f"Ambiguous edit: target string matches {occurrences} locations",
                "occurrences": occurrences,
                "recovery_suggestion": "Expand old_str with unique lines, or Read + Write",
            }

        full_path.write_text(content.replace(old_str, new_str, 1), encoding="utf-8")
        return {"success": True, "file": rel_path, "occurrences": 1}

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Write: create a file or overwrite it completely."""
        full_path = self.root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {"success": True, "file": rel_path, "bytes_written": len(content)}

    def execute_edit_with_fallback(
        self,
        rel_path: str,
        old_str: str,
        new_str: str,
        unique_context: Optional[str] = None,
        occurrence: int = 0,
    ) -> Dict[str, Any]:
        """Edit, then expanded-anchor Edit, then Read + Write of the chosen occurrence.

        `occurrence` (0-based) picks which match the Read + Write fallback replaces.
        """
        initial = self.edit_file(rel_path, old_str, new_str)
        if initial["success"]:
            return {"status": "EDIT_SUCCESS", "result": initial}

        if unique_context:
            expanded = unique_context.replace(old_str, new_str)
            retry = self.edit_file(rel_path, unique_context, expanded)
            if retry["success"]:
                return {"status": "EDIT_RETRY_SUCCESS", "result": retry}

        full_path = self.root / rel_path
        if not full_path.exists():
            return {"status": "FAILED", "error": f"File not found: {rel_path}"}
        content = full_path.read_text(encoding="utf-8")
        positions = [m.start() for m in re.finditer(re.escape(old_str), content)]
        if occurrence >= len(positions):
            return {"status": "FAILED", "error": "Target string missing after read inspection"}
        start = positions[occurrence]
        rewritten = content[:start] + new_str + content[start + len(old_str):]
        write_result = self.write_file(rel_path, rewritten)
        return {"status": "FALLBACK_WRITE_SUCCESS", "result": write_result}

    # ---- incremental exploration -------------------------------------------------

    def list_exported_names(self, rel_path: str) -> List[str]:
        """Names a wrapper module exports: __all__ if present, else top-level public defs."""
        tree = ast.parse((self.root / rel_path).read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
            ):
                return [
                    str(c.value)
                    for c in getattr(node.value, "elts", [])
                    if isinstance(c, ast.Constant)
                ]
        defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        return [n.name for n in tree.body if isinstance(n, defs) and not n.name.startswith("_")]

    def trace_usage(self, wrapper_path: str, file_pattern: str = "*.py") -> Dict[str, List[str]]:
        """Trace usage across a wrapper: list its exported names, then Grep each one."""
        usage: Dict[str, List[str]] = {}
        for name in self.list_exported_names(wrapper_path):
            hits = self.grep_search(rf"\b{re.escape(name)}\b", file_pattern)
            usage[name] = sorted({h["file"] for h in hits if h["file"] != wrapper_path})
        return usage


def main() -> None:
    """Offline demo: ambiguous Edit, expanded-anchor recovery, Read + Write and usage tracing."""
    with tempfile.TemporaryDirectory() as tmp:
        toolbox = BuiltinToolbox(Path(tmp))
        sample = "def compute():\n    return 42\n\ndef helper():\n    return 42\n"
        toolbox.write_file("service.py", sample)

        first = toolbox.edit_file("service.py", "return 42", "return 100")
        print(f"1. Ambiguous edit: {first['error']} (occurrences={first.get('occurrences')})")

        second = toolbox.execute_edit_with_fallback(
            "service.py", "return 42", "return 100", unique_context="def compute():\n    return 42"
        )
        print(f"2. Fallback status: {second['status']}")
        print("3. Final file:\n" + toolbox.read_file("service.py")["content"])


if __name__ == "__main__":
    main()
