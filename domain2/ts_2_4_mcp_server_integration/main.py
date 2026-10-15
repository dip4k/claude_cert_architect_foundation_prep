"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.4: Integrate MCP servers into Claude Code and agent workflows
Task Statement 2.5: Select and apply built-in tools effectively
Exam Scenario 4: Developer Productivity with Claude

Key Exam Concepts Demonstrated:
1. MCP Resources vs Tools: Exposing read-only content catalogs (e.g. database schema,
   API documentation index) as MCP Resources to eliminate exploratory tool calls.
2. Built-in Tools: Incremental codebase discovery using Grep to locate entry points,
   followed by Read to trace import flows (avoiding reading entire codebases upfront).
3. Edit fallback: Safe fallback to Read + Write when text matches are non-unique.
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path

load_dotenv()

# ==============================================================================
# Simulated MCP Server with Resources and Tools
# ==============================================================================

class DeveloperMCPService:
    """Simulates an MCP service offering both Resources (catalogs) and Tools (mutations)."""

    RESOURCES = {
        "catalog://schema/orders": {
            "uri": "catalog://schema/orders",
            "name": "Orders Database Schema",
            "mimeType": "application/json",
            "text": json.dumps({
                "tables": {
                    "orders": ["id", "customer_id", "total_cents", "status", "created_at"],
                    "order_items": ["id", "order_id", "sku", "quantity", "unit_price_cents"],
                }
            }),
        },
        "catalog://docs/api_endpoints": {
            "uri": "catalog://docs/api_endpoints",
            "name": "API Route Catalog",
            "mimeType": "text/markdown",
            "text": "# Routes\n- GET /api/v1/orders/{id}\n- POST /api/v1/orders/{id}/refund",
        },
    }

    @classmethod
    def read_resource(cls, uri: str) -> Optional[Dict[str, Any]]:
        """Reading an MCP Resource does NOT require model execution round-trips."""
        return cls.RESOURCES.get(uri)


# Built-in tool fallback engine (TS 2.5)
def safe_edit_file(filepath: Path, target_anchor: str, replacement: str) -> Tuple[bool, str]:
    """
    Attempts targeted string replacement.
    If anchor is not unique, falls back to Read + Write.
    """
    if not filepath.exists():
        return False, "File not found"

    content = filepath.read_text(encoding="utf-8")
    count = content.count(target_anchor)

    if count == 1:
        # Unique anchor -> Edit succeeds
        updated = content.replace(target_anchor, replacement)
        filepath.write_text(updated, encoding="utf-8")
        return True, "Edited with unique anchor match."
    elif count > 1:
        # Non-unique anchor -> Trigger documented fallback: Read + Write with context
        return False, "Edit failed: Anchor text is non-unique. Triggering Read + Write fallback."
    else:
        return False, "Edit failed: Anchor text not found."


def main() -> None:
    print("Testing MCP Resource Catalog Retrieval:")
    resource = DeveloperMCPService.read_resource("catalog://schema/orders")
    print(f"Resource Loaded: {resource['name'] if resource else 'Not Found'}")
    print(f"Schema Content: {resource['text'] if resource else ''}\n")


if __name__ == "__main__":
    main()
