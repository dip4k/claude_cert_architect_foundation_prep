"""
Domain 2: Tool Design & MCP Integration
Task Statement 2.4: Integrate MCP servers into Claude Code and agent workflows
Exam Scenarios 3 (Research) and 4 (Developer Productivity)

Key Exam Concepts Demonstrated:
1. Scoping: project `.mcp.json` (shared, version controlled) vs user `~/.claude.json`
   (personal or experimental).
2. Secrets never live in `.mcp.json`; `${GITHUB_TOKEN}` style expansion keeps them in the
   environment (`expand_env`, `load_mcp_config`, `find_hardcoded_secrets`).
3. Tools from ALL configured servers are discovered at connection time and are available
   at the same time (`discover_tools`).
4. MCP Resources expose content catalogs (schemas, doc hierarchies, issue summaries) so the
   agent needs fewer exploratory tool calls (`DeveloperMCPService`).
5. Rich MCP tool descriptions stop the agent from preferring built-in Grep (`audit_mcp_tool`).

This module makes no API calls.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class MissingEnvVarError(ValueError):
    """Raised when .mcp.json references an environment variable that is not set."""


# ==============================================================================
# 1. .mcp.json parsing with ${ENV_VAR} expansion
# ==============================================================================

EXAMPLE_PROJECT_MCP_JSON = json.dumps(
    {
        "mcpServers": {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
            },
            "jira": {
                "command": "npx",
                "args": ["-y", "<community-jira-mcp-package>"],
                "env": {"JIRA_API_TOKEN": "${JIRA_API_TOKEN}"},
            },
        }
    }
)


def expand_env(value: Any, env: Mapping[str, str]) -> Any:
    """Recursively replace ${VAR} in strings; raise MissingEnvVarError for unset variables."""
    if isinstance(value, str):

        def _sub(match: "re.Match[str]") -> str:
            name = match.group(1)
            if name not in env:
                raise MissingEnvVarError(f"Environment variable '{name}' is not set")
            return env[name]

        return ENV_REF.sub(_sub, value)
    if isinstance(value, list):
        return [expand_env(item, env) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item, env) for key, item in value.items()}
    return value


def load_mcp_config(text: str, env: Mapping[str, str]) -> Dict[str, Any]:
    """Parse .mcp.json text and return the config with ${VAR} expanded from `env`."""
    config = json.loads(text)
    if "mcpServers" not in config:
        raise ValueError("Config must contain a 'mcpServers' object")
    expanded: Dict[str, Any] = expand_env(config, env)
    return expanded


def find_hardcoded_secrets(text: str) -> List[str]:
    """Return 'server.KEY' for every env value that is a literal instead of ${VAR}."""
    config = json.loads(text)
    leaks: List[str] = []
    for server_name, server in config.get("mcpServers", {}).items():
        for key, value in server.get("env", {}).items():
            if not ENV_REF.fullmatch(str(value)):
                leaks.append(f"{server_name}.{key}")
    return leaks


def discover_tools(servers: Mapping[str, List[str]]) -> Dict[str, str]:
    """Merge tools from every connected server; maps tool name -> server (all available at once)."""
    catalog: Dict[str, str] = {}
    for server_name, tool_names in servers.items():
        for tool_name in tool_names:
            catalog[tool_name] = server_name
    return catalog


def audit_mcp_tool(tool: Dict[str, Any]) -> List[str]:
    """Flag MCP tool descriptions too thin to beat a built-in like Grep."""
    description = str(tool.get("description", ""))
    problems: List[str] = []
    if len(description) < 80:
        problems.append("description too short; the agent may prefer built-in Grep")
    if "example" not in description.lower():
        problems.append("add an example query and when to prefer this tool over Grep")
    return problems


# ==============================================================================
# 2. Simulated MCP server: Resources (catalogs) vs Tools (actions)
# ==============================================================================


class DeveloperMCPService:
    """Simulates an MCP service offering read-only Resources and operational Tools."""

    RESOURCES: Dict[str, Dict[str, str]] = {
        "catalog://schema/orders": {
            "uri": "catalog://schema/orders",
            "name": "Orders Database Schema",
            "mimeType": "application/json",
            "text": json.dumps(
                {
                    "tables": {
                        "orders": ["id", "customer_id", "total_cents", "status", "created_at"],
                        "order_items": ["id", "order_id", "sku", "quantity", "unit_price_cents"],
                    }
                }
            ),
        },
        "catalog://docs/api_endpoints": {
            "uri": "catalog://docs/api_endpoints",
            "name": "API Route Catalog",
            "mimeType": "text/markdown",
            "text": "# Routes\n- GET /api/v1/orders/{id}\n- POST /api/v1/orders/{id}/refund",
        },
    }

    @classmethod
    def list_resources(cls) -> List[Dict[str, str]]:
        """Return the catalog index (uri + name): one call replaces many exploratory calls."""
        return [{"uri": r["uri"], "name": r["name"]} for r in cls.RESOURCES.values()]

    @classmethod
    def read_resource(cls, uri: str) -> Optional[Dict[str, str]]:
        """Read one resource by URI; returns None for an unknown URI."""
        return cls.RESOURCES.get(uri)


# ==============================================================================
# 3. Edit fallback (cross-reference to TS 2.5)
# ==============================================================================


def safe_edit_file(filepath: Path, target_anchor: str, replacement: str) -> Tuple[bool, str]:
    """Replace a unique anchor; for a non-unique anchor ask for the Read + Write fallback."""
    if not filepath.exists():
        return False, "File not found"

    content = filepath.read_text(encoding="utf-8")
    count = content.count(target_anchor)

    if count == 1:
        filepath.write_text(content.replace(target_anchor, replacement), encoding="utf-8")
        return True, "Edited with unique anchor match."
    if count > 1:
        return False, "Edit failed: Anchor text is non-unique. Triggering Read + Write fallback."
    return False, "Edit failed: Anchor text not found."


def main() -> None:
    """Offline demo of env expansion, secret detection and resource catalog reads."""
    env = {"GITHUB_TOKEN": "ghp_example", "JIRA_API_TOKEN": "jira_example"}
    config = load_mcp_config(EXAMPLE_PROJECT_MCP_JSON, env)
    print("Servers:", list(config["mcpServers"]))
    print("Hardcoded secrets:", find_hardcoded_secrets(EXAMPLE_PROJECT_MCP_JSON))
    print("Resources:", DeveloperMCPService.list_resources())


if __name__ == "__main__":
    main()
