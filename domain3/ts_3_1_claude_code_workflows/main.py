"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.1: Configure CLAUDE.md files with appropriate hierarchy and scoping
Exam Scenario 2 & 5: Code Generation & CI/CD Pipelines

Offline simulation (no API calls). Key exam concepts:
1. Three CLAUDE.md scopes: user (~/.claude/CLAUDE.md, personal, NOT in version control),
   project (./CLAUDE.md or .claude/CLAUDE.md, shared) and directory (<subdir>/CLAUDE.md).
2. `resolve_claude_md_chain` lists which files apply to a target file, general -> specific.
3. Only project and directory files reach teammates; user-level files do not.
4. `.claude/rules/*.md` path-scoped rules load only for files matching their `paths:` globs.
5. `@import` syntax (`@path/to/file`) keeps a CLAUDE.md modular.
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from domain3.ts_3_3_path_specific_rules.main import (  # noqa: E402
    as_list,
    glob_match,
    parse_frontmatter,
)

# ==============================================================================
# 1. CLAUDE.md hierarchy resolution (TS 3.1)
# ==============================================================================


@dataclass(frozen=True)
class MemoryEntry:
    """One CLAUDE.md file in the chain. scope is 'user', 'project' or 'directory'."""

    scope: str
    path: Path

    @property
    def shared_via_vcs(self) -> bool:
        """User-level files live in the home folder, so teammates never receive them."""
        return self.scope != "user"


def resolve_claude_md_chain(
    project_root: Path,
    target_file: Path,
    user_dir: Path | None = None,
) -> list[MemoryEntry]:
    """
    Lists the existing CLAUDE.md files that apply to `target_file`, general -> specific:
    user (user_dir/CLAUDE.md), project (root or .claude/), then each directory on the way down.
    """
    root = project_root.resolve()
    target = target_file if target_file.is_absolute() else root / target_file
    entries: list[MemoryEntry] = []
    if user_dir is not None and (user_dir / "CLAUDE.md").is_file():
        entries.append(MemoryEntry("user", user_dir / "CLAUDE.md"))
    for candidate in (root / "CLAUDE.md", root / ".claude" / "CLAUDE.md"):
        if candidate.is_file():
            entries.append(MemoryEntry("project", candidate))
    current = root
    for part in target.resolve().parent.relative_to(root).parts:
        current = current / part
        if (current / "CLAUDE.md").is_file():
            entries.append(MemoryEntry("directory", current / "CLAUDE.md"))
    return entries


def teammate_visible(entries: list[MemoryEntry]) -> list[MemoryEntry]:
    """Entries a new teammate gets after cloning the repo (user-level ones are excluded)."""
    return [e for e in entries if e.shared_via_vcs]


_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_CODE_SPAN = re.compile(r"`[^`\n]*`")
_IMPORT_TOKEN = re.compile(r"(?:(?<=\s)|^)@(\S+)", re.MULTILINE)


def find_imports(claude_md_text: str) -> list[str]:
    """Returns the paths imported with `@path/to/file`, skipping code spans and fenced blocks."""
    visible = _CODE_SPAN.sub("", _CODE_FENCE.sub("", claude_md_text))
    return [token.rstrip(".,;:)") for token in _IMPORT_TOKEN.findall(visible)]


# ==============================================================================
# 2. Path-scoped rules (TS 3.3 recap)
# ==============================================================================


@dataclass
class PathScopedRule:
    rule_name: str
    globs: list[str]
    rule_content: str

    def matches(self, filepath: str) -> bool:
        """True if any `paths:` glob matches (a rule without globs is universal)."""
        return not self.globs or any(glob_match(filepath, g) for g in self.globs)


def load_path_rules(rules_dir: Path) -> list[PathScopedRule]:
    """Reads real `.claude/rules/*.md` files (frontmatter `paths:` + body)."""
    rules: list[PathScopedRule] = []
    for rule_file in sorted(rules_dir.glob("*.md")):
        data, body = parse_frontmatter(rule_file.read_text(encoding="utf-8"))
        rules.append(PathScopedRule(rule_file.stem, as_list(data.get("paths")), body.strip()))
    return rules


RULE_STORE: list[PathScopedRule] = [
    PathScopedRule(
        rule_name="api_conventions",
        globs=["src/api/**/*", "**/api/**/*.py"],
        rule_content="All API handlers must use explicit Pydantic response models and async.",
    ),
    PathScopedRule(
        rule_name="test_conventions",
        globs=["**/*.test.*", "tests/**/*.py"],
        rule_content="All tests must use pytest patterns and include docstrings with AAA structure.",
    ),
]


def resolve_active_rules_for_file(filepath: str) -> list[str]:
    """Returns only the rules that apply to the given file, preventing context bloat."""
    return [r.rule_content for r in RULE_STORE if r.matches(filepath)]


# ==============================================================================
# 3. CI review stub (full command builder lives in TS 3.6)
# ==============================================================================


def simulate_ci_review_execution(
    git_diff: str,
    rules_applied: list[str],
    is_non_interactive: bool = True,
) -> dict[str, Any]:
    """
    Simulates: claude -p ... --output-format json --json-schema <schema>
    `is_non_interactive=True` mirrors the -p / --print flag; without it a CI job would hang.
    """
    if not is_non_interactive:
        raise RuntimeError("CI runner hung waiting for terminal input! Missing -p flag.")

    findings = []
    if "eval(" in git_diff or "os.system(" in git_diff:
        findings.append(
            {
                "severity": "CRITICAL",
                "file": "main.py",
                "line": 42,
                "message": "Use of unsafe eval/system call detected in diff.",
            }
        )
    return {
        "status": "completed",
        "non_interactive_mode": True,
        "rules_enforced_count": len(rules_applied),
        "total_findings": len(findings),
        "findings": findings,
    }


def main() -> None:
    target = Path("domain3/ts_3_1_claude_code_workflows/main.py")
    print("1. CLAUDE.md chain for", target)
    for entry in resolve_claude_md_chain(REPO_ROOT, target):
        shared = "shared" if entry.shared_via_vcs else "personal"
        print(f"   [{entry.scope}/{shared}] {entry.path.relative_to(REPO_ROOT)}")

    print("\n2. Path-scoped rules from .claude/rules/ that load for that file:")
    for rule in load_path_rules(REPO_ROOT / ".claude" / "rules"):
        if rule.matches(target.as_posix()):
            print(f"   {rule.rule_name}: paths={rule.globs}")

    print("\n3. CI stub with -p:")
    result = simulate_ci_review_execution("diff\n+ eval(user_input)", ["rule"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
