"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.3: Implement Path-Specific Rules and Scoping
Exam Scenario 2: Code Generation with Claude Code

Key Architectural Concepts:
1. Rule scoping via YAML frontmatter `paths: [...]`.
2. Evaluator selectively injects rules only when active target files match glob patterns.
3. Hierarchy resolution: Global User -> Project -> Subdirectory -> Path-scoped rules.
4. Prevents instruction pollution across multi-language / multi-tier repositories.
"""

import fnmatch
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class ScopedRule:
    rule_id: str
    paths: List[str]  # Empty means universally applies
    instructions: str

    def matches_files(self, touched_files: List[str]) -> bool:
        """Checks if any touched file matches any of the rule's path patterns."""
        if not self.paths:
            return True  # Universal rule
        
        for file_path in touched_files:
            clean_path = file_path.replace("\\", "/")
            for pattern in self.paths:
                clean_pattern = pattern.replace("\\", "/")
                # Support glob matching (e.g., backend/** or *.py)
                if fnmatch.fnmatch(clean_path, clean_pattern) or fnmatch.fnmatch(clean_path, f"*/{clean_pattern}"):
                    return True
                # Match directory prefixes if pattern ends with /**
                if clean_pattern.endswith("/**"):
                    prefix = clean_pattern[:-3]
                    if clean_path.startswith(prefix) or f"/{prefix}" in clean_path:
                        return True
        return False


class RuleEngine:
    """Simulates Claude Code's path-scoped rule evaluator."""

    def __init__(self) -> None:
        self.rules: List[ScopedRule] = []

    def register_rule(self, rule_id: str, raw_markdown: str) -> None:
        """Parses markdown with optional YAML frontmatter paths."""
        paths: List[str] = []
        instructions = raw_markdown

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_markdown, re.DOTALL)
        if match:
            frontmatter, instructions = match.groups()
            for line in frontmatter.splitlines():
                line = line.strip()
                if line.startswith("paths:"):
                    continue
                if line.startswith("- "):
                    path_val = line[2:].strip().strip("'\"")
                    if path_val:
                        paths.append(path_val)

        self.rules.append(ScopedRule(rule_id=rule_id, paths=paths, instructions=instructions.strip()))

    def get_applicable_instructions(self, touched_files: List[str]) -> List[Dict[str, Any]]:
        """Filters rules down strictly to those matching the active file context."""
        applicable = []
        for rule in self.rules:
            if rule.matches_files(touched_files):
                applicable.append({
                    "rule_id": rule.rule_id,
                    "scoped_patterns": rule.paths,
                    "instructions": rule.instructions
                })
        return applicable


def main() -> None:
    print("=" * 70)
    print("TS 3.3: Path-Specific Rules Engine Demo")
    print("=" * 70)

    engine = RuleEngine()

    # Rule 1: Universal
    engine.register_rule("global_style", "Always use 4 spaces for indentation and UTF-8 encoding.")

    # Rule 2: Python Backend Only
    backend_rule = """---
paths:
  - "backend/**"
  - "*.py"
---
All backend handlers must use async def and return validated Pydantic schemas.
"""
    engine.register_rule("backend_async", backend_rule)

    # Rule 3: Frontend TypeScript Only
    frontend_rule = """---
paths:
  - "frontend/**"
  - "*.tsx"
---
Always use React functional components with explicit TypeScript interfaces.
"""
    engine.register_rule("frontend_react", frontend_rule)

    # Scenario A: Developer edits backend file
    touched_backend = ["backend/api/auth.py"]
    active_backend = engine.get_applicable_instructions(touched_backend)
    print(f"\nFiles touched: {touched_backend}")
    print(f"Rules injected: {[r['rule_id'] for r in active_backend]}")

    # Scenario B: Developer edits frontend file
    touched_frontend = ["frontend/src/Button.tsx"]
    active_frontend = engine.get_applicable_instructions(touched_frontend)
    print(f"\nFiles touched: {touched_frontend}")
    print(f"Rules injected: {[r['rule_id'] for r in active_frontend]}")

    # Verification: Frontend rule is NEVER injected into backend session!
    backend_rule_ids = [r["rule_id"] for r in active_backend]
    assert "frontend_react" not in backend_rule_ids
    print("\nVerified: Zero cross-domain prompt pollution!")


if __name__ == "__main__":
    main()
