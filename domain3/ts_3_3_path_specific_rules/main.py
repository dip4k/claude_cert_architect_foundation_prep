"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.3: Apply Path-Specific Rules for Conditional Convention Loading
Exam Scenario 2: Code Generation with Claude Code

Offline simulation (no API calls). It validates the REAL file formats used by this repo:
1. `.claude/rules/*.md` files carry YAML-style frontmatter with a `paths:` list of globs.
2. A path-scoped rule loads only when the file being edited matches one of its globs.
3. A rule with no `paths:` is always loaded (universal).
4. `parse_frontmatter` and `glob_match` are shared by TS 3.1 and TS 3.2.

Inputs: markdown text or a rules directory. Outputs: matching rule instructions.
"""

import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FrontValue = str | list[str]

_FRONTMATTER = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z",
    re.DOTALL,
)


def _unquote(value: str) -> str:
    """Strips one pair of matching quotes and surrounding spaces."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, FrontValue], str]:
    """
    Tiny YAML-subset parser for the frontmatter used by rules and skills.

    Supports `key: value`, `key: [a, b]` and `key:` followed by `- item` lines.
    Returns (data, body). No frontmatter returns ({}, text).
    """
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    block, body = match.groups()
    data: dict[str, FrontValue] = {}
    key: str | None = None
    for raw in block.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and key is not None:
            current = data.get(key)
            items = current if isinstance(current, list) else []
            items.append(_unquote(stripped[2:]))
            data[key] = items
        elif ":" in raw and not raw[0].isspace():
            name, _, value = raw.partition(":")
            key = name.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                data[key] = [_unquote(x) for x in value[1:-1].split(",") if x.strip()]
            else:
                data[key] = _unquote(value)
    return data, body


def as_list(value: FrontValue | None) -> list[str]:
    """Normalizes a frontmatter value (missing, scalar or list) to a list of strings."""
    if value is None or value == "":
        return []
    return [value] if isinstance(value, str) else list(value)


@lru_cache(maxsize=256)
def _glob_regex(pattern: str) -> re.Pattern[str]:
    """Compiles a glob: `**/` = any dirs (or none), `**` = anything, `*` = within one dir."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def glob_match(path: str, pattern: str) -> bool:
    """True if a repo-relative path matches the glob (`*` never crosses a `/`)."""
    clean_path = path.replace("\\", "/").removeprefix("./")
    clean_pattern = pattern.replace("\\", "/").removeprefix("./")
    return _glob_regex(clean_pattern).match(clean_path) is not None


@dataclass
class ScopedRule:
    """One rule file: instructions plus the globs that activate it."""

    rule_id: str
    paths: list[str]  # Empty means the rule is universal (always loaded)
    instructions: str

    def matches(self, file_path: str) -> bool:
        """True if the rule applies to this single file."""
        return not self.paths or any(glob_match(file_path, p) for p in self.paths)

    def matches_files(self, touched_files: list[str]) -> bool:
        """True if the rule applies to at least one touched file."""
        return not self.paths or any(self.matches(f) for f in touched_files)


class RuleEngine:
    """Simulates Claude Code's path-scoped rule loader."""

    def __init__(self) -> None:
        self.rules: list[ScopedRule] = []

    def register_rule(self, rule_id: str, raw_markdown: str) -> None:
        """Parses a rule file's text; the `paths:` frontmatter list becomes the globs."""
        data, body = parse_frontmatter(raw_markdown)
        paths = as_list(data.get("paths"))
        self.rules.append(ScopedRule(rule_id=rule_id, paths=paths, instructions=body.strip()))

    def register_rules_from_dir(self, rules_dir: Path) -> int:
        """Loads every `*.md` file in a rules directory. Returns how many were loaded."""
        files = sorted(rules_dir.glob("*.md"))
        for rule_file in files:
            self.register_rule(rule_file.stem, rule_file.read_text(encoding="utf-8"))
        return len(files)

    def get_applicable_instructions(self, touched_files: list[str]) -> list[dict[str, Any]]:
        """Returns only the rules matching the files in play (saves tokens)."""
        return [
            {
                "rule_id": rule.rule_id,
                "scoped_patterns": rule.paths,
                "instructions": rule.instructions,
            }
            for rule in self.rules
            if rule.matches_files(touched_files)
        ]


def main() -> None:
    print("=" * 70)
    print("TS 3.3: Path-Specific Rules Demo (real .claude/rules files)")
    print("=" * 70)

    engine = RuleEngine()
    count = engine.register_rules_from_dir(REPO_ROOT / ".claude" / "rules")
    print(f"\nLoaded {count} rule files from .claude/rules/")
    for rule in engine.rules:
        print(f"  {rule.rule_id}: paths={rule.paths}")

    for edited in ("domain3/ts_3_3_path_specific_rules/main.py", "README.md", "src/tools/x.py"):
        ids = [r["rule_id"] for r in engine.get_applicable_instructions([edited])]
        print(f"\nEditing {edited}\n  rules loaded: {ids}")


if __name__ == "__main__":
    main()
