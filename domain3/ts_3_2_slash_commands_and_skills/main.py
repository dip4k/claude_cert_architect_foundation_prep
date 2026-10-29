"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.2: Configure Custom Slash Commands and Skills
Exam Scenario 2: Code Generation with Claude Code

Offline simulation (no API calls). It validates the REAL formats used by this repo:
1. Project-scoped commands live in `.claude/commands/` (shared via version control);
   user-scoped commands live in `~/.claude/commands/` (personal).
2. Skills live in `.claude/skills/<name>/SKILL.md` with frontmatter keys such as
   `context: fork`, `allowed-tools` and `argument-hint`.
3. `context: fork` runs a skill in an isolated context; only a summary returns to the
   main conversation. (The fork itself is simulated here.)
4. Skills are on-demand workflows; CLAUDE.md is always-loaded universal standards.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from domain3.ts_3_3_path_specific_rules.main import as_list, parse_frontmatter  # noqa: E402


@dataclass
class SkillDefinition:
    """Parsed SKILL.md: frontmatter fields plus the instruction body."""

    name: str
    description: str
    context: str = "inline"  # 'inline' or 'fork'
    allowed_tools: list[str] = field(default_factory=list)
    argument_hint: str = ""
    instructions: str = ""


def classify_command_path(command_file: Path, project_root: Path) -> str:
    """
    Returns "project-scoped" for <project_root>/.claude/commands/*.md (shared via VCS),
    "user-scoped" for any other .claude/commands/ folder (e.g. ~/.claude/commands/),
    or "not-a-command" otherwise.
    """
    resolved = command_file.resolve()
    if resolved.is_relative_to(project_root.resolve() / ".claude" / "commands"):
        return "project-scoped"
    parts = resolved.parts
    for i in range(len(parts) - 1):
        if parts[i] == ".claude" and parts[i + 1] == "commands":
            return "user-scoped"
    return "not-a-command"


class SkillCommandParser:
    """Parses .claude/skills/ and .claude/commands/ structures."""

    @staticmethod
    def parse_slash_command(command_text: str, user_args: str) -> str:
        """Interpolates $ARGUMENTS and positional tokens ($1, $2) into a command template."""
        interpolated = command_text.replace("$ARGUMENTS", user_args)
        for i, val in enumerate(user_args.split(), start=1):
            interpolated = interpolated.replace(f"${i}", val)
        return interpolated

    @staticmethod
    def parse_skill_markdown(skill_md_content: str) -> SkillDefinition:
        """Extracts frontmatter (name, description, context, allowed-tools, argument-hint)."""
        data, body = parse_frontmatter(skill_md_content)
        if not data:
            return SkillDefinition(name="unknown", description="", instructions=body.strip())
        hint = data.get("argument-hint", "")
        if isinstance(hint, list):
            hint = "[" + ", ".join(hint) + "]"
        description = data.get("description", "")
        return SkillDefinition(
            name=str(data.get("name", "unnamed")),
            description=description if isinstance(description, str) else "",
            context=str(data.get("context", "inline")),
            allowed_tools=as_list(data.get("allowed-tools")),
            argument_hint=hint,
            instructions=body.strip(),
        )

    @staticmethod
    def load_skills_from_dir(skills_dir: Path) -> list[SkillDefinition]:
        """Loads every `<skills_dir>/<name>/SKILL.md`."""
        return [
            SkillCommandParser.parse_skill_markdown(f.read_text(encoding="utf-8"))
            for f in sorted(skills_dir.glob("*/SKILL.md"))
        ]


class ClaudeCodeRunner:
    """Demonstrates context-forked skill execution vs inline execution (simulated)."""

    def __init__(self) -> None:
        self.main_context_history: list[str] = []

    def execute_slash_command(self, cmd_template: str, raw_user_args: str) -> str:
        prompt = SkillCommandParser.parse_slash_command(cmd_template, raw_user_args)
        self.main_context_history.append(f"[COMMAND EXPANSION]: {prompt}")
        return f"Executed command with prompt: {prompt}"

    def execute_skill(self, skill: SkillDefinition, task_args: str) -> dict[str, Any]:
        """If `context == 'fork'`, only a short summary reaches the main context."""
        if skill.context == "fork":
            scratchpad = [
                f"[FORKED SESSION {skill.name}] Target: {task_args}",
                f"[ALLOWED TOOLS]: {skill.allowed_tools}",
                "[INTERMEDIATE NOISE]: Read 45 files, Grepped 120 lines (stays in the fork)",
            ]
            summary = f"Audit complete: 0 vulnerabilities found in {task_args}"
            self.main_context_history.append(f"[SKILL SUMMARY ({skill.name})]: {summary}")
            return {
                "execution_mode": "forked",
                "subagent_events_count": len(scratchpad),
                "summary": summary,
                "main_context_bloat_prevented": True,
            }
        self.main_context_history.append(f"[INLINE SKILL]: {skill.instructions}")
        return {
            "execution_mode": "inline",
            "summary": f"Executed inline: {skill.name}",
            "main_context_bloat_prevented": False,
        }


def main() -> None:
    print("=" * 70)
    print("TS 3.2: Slash Commands & Skills Demo (real .claude files)")
    print("=" * 70)

    print("\n1. Commands in this repo:")
    for cmd in sorted((REPO_ROOT / ".claude" / "commands").glob("*.md")):
        print(f"  /{cmd.stem}: {classify_command_path(cmd, REPO_ROOT)}")

    print("\n2. Skills in this repo (parsed frontmatter):")
    skills = SkillCommandParser.load_skills_from_dir(REPO_ROOT / ".claude" / "skills")
    for skill in skills:
        print(
            f"  {skill.name}: context={skill.context}, "
            f"allowed-tools={skill.allowed_tools}, argument-hint={skill.argument_hint!r}"
        )

    print("\n3. Simulated fork vs inline:")
    runner = ClaudeCodeRunner()
    for skill in skills[:1]:
        print(json.dumps(runner.execute_skill(skill, "src/auth"), indent=2))
    print(f"Entries in main context: {len(runner.main_context_history)}")


if __name__ == "__main__":
    main()
