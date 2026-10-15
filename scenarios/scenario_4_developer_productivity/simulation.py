"""
Scenario 4: Developer Productivity with Claude
End-to-End System Simulation

Weaves Together:
- TS 2.3: Tool Distribution & Principle of Least Privilege
- TS 2.4: MCP Server Integration & MCP Resources (resources/read)
- TS 2.5: Built-in Tools Execution (Grep, Glob, Read, Edit & Fallback Protocol)
- TS 1.7: Session State & Forked Exploration
"""

import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class MCPResourceRecord:
    uri: str
    name: str
    mime_type: str
    content: str


class DeveloperProductivityToolbox:
    """Simulates Claude Code's developer productivity toolbox with safe fallbacks and MCP resources."""

    def __init__(self, workspace_files: Dict[str, str]) -> None:
        self.files = dict(workspace_files)
        self.mcp_resources = {
            "resource://specs/openapi.json": MCPResourceRecord(
                uri="resource://specs/openapi.json",
                name="Billing API Spec",
                mime_type="application/json",
                content='{"openapi": "3.0.0", "paths": {"/tax": {"get": {"summary": "Tax calculation"}}}}'
            )
        }

    # 1. MCP Resource Reader (On-Demand reference data)
    def read_mcp_resource(self, uri: str) -> Dict[str, Any]:
        """Reads static documentation or catalogs as an MCP Resource rather than active tool."""
        if uri not in self.mcp_resources:
            return {"success": False, "error": f"Resource not found: {uri}"}
        res = self.mcp_resources[uri]
        return {"success": True, "uri": res.uri, "name": res.name, "content": res.content}

    # 2. Incremental Discovery: Grep & Glob
    def glob_paths(self, pattern: str) -> List[str]:
        return [p for p in self.files.keys() if fnmatch.fnmatch(p, pattern)]

    def grep_symbols(self, symbol_regex: str) -> List[Dict[str, Any]]:
        matches = []
        compiled = re.compile(symbol_regex)
        for path, content in self.files.items():
            lines = content.splitlines()
            for line_no, line in enumerate(lines, start=1):
                if compiled.search(line):
                    matches.append({"file": path, "line": line_no, "text": line.strip()})
        return matches

    def read_file_range(self, path: str, offset: int = 1, limit: int = 20) -> Dict[str, Any]:
        if path not in self.files:
            return {"success": False, "error": "File not found"}
        lines = self.files[path].splitlines()
        start = max(0, offset - 1)
        end = min(len(lines), start + limit)
        return {
            "success": True,
            "file": path,
            "lines": lines[start:end],
            "total_lines": len(lines)
        }

    def read_file(self, path: str) -> Dict[str, Any]:
        """Built-in Read tool: reads entire file contents."""
        if path not in self.files:
            return {"success": False, "status": "FILE_NOT_FOUND", "error": f"File '{path}' does not exist."}
        return {"success": True, "path": path, "content": self.files[path]}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Built-in Write tool: writes entire file contents."""
        self.files[path] = content
        return {"success": True, "status": "WRITTEN", "path": path}

    # 3. Surgical Edit & Fallback Protocol
    def apply_edit(self, path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        if path not in self.files:
            return {"success": False, "status": "FILE_NOT_FOUND", "error": "File not found"}
        
        content = self.files[path]
        count = content.count(old_str)

        if count == 0:
            return {"success": False, "status": "NOT_FOUND", "error": "Target string not found in file."}
        if count > 1:
            # Anchor Collision!
            return {
                "success": False,
                "status": "AMBIGUOUS_COLLISION",
                "occurrences": count,
                "error": f"Ambiguous anchor: '{old_str}' matches {count} locations. Expand context or fallback to Read+Write."
            }

        # Unique match: apply safely
        self.files[path] = content.replace(old_str, new_str, 1)
        return {"success": True, "status": "EDITED", "file": path}

    def execute_edit_with_fallback(
        self,
        path: str,
        old_str: str,
        new_str: str,
        expanded_anchor: Optional[str] = None,
        target_occurrence: int = 1,
        full_replacement_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Implements the standard Claude Code recovery protocol when Edit encounters collision."""
        if path not in self.files:
            return {"final_status": "FAILED", "error": f"File not found: {path}"}

        # Step 1: Try initial surgical edit
        res1 = self.apply_edit(path, old_str, new_str)
        if res1["success"]:
            return {"final_status": "SURGICAL_EDIT_SUCCESS", "details": res1}

        # Step 2: Try expanded anchor if provided
        if expanded_anchor and expanded_anchor in self.files.get(path, ""):
            expanded_replacement = expanded_anchor.replace(old_str, new_str)
            res2 = self.apply_edit(path, expanded_anchor, expanded_replacement)
            if res2["success"]:
                return {"final_status": "EXPANDED_ANCHOR_SUCCESS", "details": res2}

        # Step 3: Fall back to Read + Write
        read_res = self.read_file(path)
        if not read_res["success"]:
            return {"final_status": "FAILED", "error": read_res.get("error")}

        full_content = read_res["content"]
        if full_replacement_content is not None:
            self.write_file(path, full_replacement_content)
            return {
                "final_status": "FALLBACK_READ_WRITE_SUCCESS",
                "message": "Fell back to Read + Write cleanly with verified full replacement."
            }

        if old_str in full_content:
            # Replace target occurrence without corrupting earlier occurrences
            parts = full_content.split(old_str)
            if 0 < target_occurrence < len(parts):
                rewritten = (
                    old_str.join(parts[:target_occurrence])
                    + new_str
                    + old_str.join(parts[target_occurrence:])
                )
            else:
                rewritten = full_content.replace(old_str, new_str, 1)

            self.write_file(path, rewritten)
            return {
                "final_status": "FALLBACK_READ_WRITE_SUCCESS",
                "message": f"Fell back to Read + Write cleanly after anchor ambiguity (targeted occurrence {target_occurrence})."
            }

        return {"final_status": "FAILED", "error": "Unable to locate anchor for replacement"}


def main() -> None:
    print("=" * 70)
    print("Scenario 4: Developer Productivity with Claude Simulation")
    print("=" * 70)

    repo_files = {
        "src/billing/calc.py": """
def get_rate():
    return 0.05

def calculate_tax(amount):
    return 0.05
""",
        "src/billing/invoice.py": "def create_invoice(): pass",
        "tests/test_calc.py": "def test_tax(): pass"
    }

    toolbox = DeveloperProductivityToolbox(repo_files)

    # 1. MCP Resource on-demand reading
    res = toolbox.read_mcp_resource("resource://specs/openapi.json")
    print("\n1. MCP Resource Read (No tool token bloat):")
    print(f"Loaded: {res['name']} ({res['uri']})")

    # 2. Incremental Discovery: Grep
    print("\n2. Incremental Discovery via Grep (Finding definition):")
    matches = toolbox.grep_symbols("def calculate_tax")
    print(f"Grep Results: {matches}")

    # 3. Surgical Edit Anchor Collision
    print("\n3. Testing Edit Collision on duplicate anchor 'return 0.05':")
    collision_res = toolbox.apply_edit("src/billing/calc.py", "return 0.05", "return 0.08")
    print(f"Status: {collision_res['status']} ({collision_res.get('error')})")

    # 4. Fallback Protocol Resolution
    print("\n4. Resolving via Fallback Protocol:")
    fallback_res = toolbox.execute_edit_with_fallback(
        "src/billing/calc.py",
        old_str="return 0.05",
        new_str="return 0.08",
        expanded_anchor="def calculate_tax(amount):\n    return 0.05"
    )
    print(f"Outcome: {fallback_res['final_status']}")
    print(f"Updated File Content:\n{toolbox.files['src/billing/calc.py']}")


if __name__ == "__main__":
    main()
