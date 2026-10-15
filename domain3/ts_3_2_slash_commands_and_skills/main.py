"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.2: Configure Custom Slash Commands and Skills
Exam Scenario 2: Code Generation with Claude Code

Key Architectural Concepts:
1. Custom Slash Command expansion (.claude/commands/command.md) with $ARGUMENTS interpolation.
2. Skill frontmatter parsing:
   - context: fork (spawns isolated sub-agent context to avoid polluting main session)
   - allowed-tools: limits tool permissions strictly (principle of least privilege)
   - argument-hint: UI autocomplete hint
3. Forked skill execution returns only synthesized outcome to the main context.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class SkillDefinition:
    name: str
    description: str
    context: str = "inline"  # 'inline' or 'fork'
    allowed_tools: List[str] = field(default_factory=list)
    argument_hint: str = ""
    instructions: str = ""


class SkillCommandParser:
    """Parses .claude/skills/ and .claude/commands/ structures."""

    @staticmethod
    def parse_slash_command(command_text: str, user_args: str) -> str:
        """Interpolates $ARGUMENTS or positional tokens ($1, $2) into command template."""
        interpolated = command_text.replace("$ARGUMENTS", user_args)
        # Handle positional tokens
        args_list = user_args.split()
        for i, val in enumerate(args_list, start=1):
            interpolated = interpolated.replace(f"${i}", val)
        return interpolated

    @staticmethod
    def parse_skill_markdown(skill_md_content: str) -> SkillDefinition:
        """Extracts YAML frontmatter and body from a SKILL.md file."""
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", skill_md_content, re.DOTALL)
        if not frontmatter_match:
            return SkillDefinition(name="unknown", description="", instructions=skill_md_content)

        yaml_block, body = frontmatter_match.groups()
        data: Dict[str, Any] = {}
        for line in yaml_block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    data[k] = items
                else:
                    data[k] = v

        return SkillDefinition(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            context=data.get("context", "inline"),
            allowed_tools=data.get("allowed-tools", []),
            argument_hint=data.get("argument-hint", ""),
            instructions=body.strip(),
        )


class ClaudeCodeRunner:
    """Demonstrates context-forked skill execution vs inline command execution."""

    def __init__(self) -> None:
        self.main_context_history: List[str] = []

    def execute_slash_command(self, cmd_template: str, raw_user_args: str) -> str:
        prompt = SkillCommandParser.parse_slash_command(cmd_template, raw_user_args)
        self.main_context_history.append(f"[COMMAND EXPANSION]: {prompt}")
        return f"Executed command with prompt: {prompt}"

    def execute_skill(self, skill: SkillDefinition, task_args: str) -> Dict[str, Any]:
        """
        If skill.context == 'fork', executes in an isolated environment.
        Only the concise summary is returned to the main context.
        """
        if skill.context == "fork":
            # Isolated session (no main context token pollution)
            subagent_scratchpad = [
                f"[FORKED SESSION {skill.name}] Target: {task_args}",
                f"[ALLOWED TOOLS]: {skill.allowed_tools}",
                "[INTERMEDIATE NOISE]: Read 45 files, Grepped 120 lines (pruned from main context)",
            ]
            synthesized_summary = f"Audit complete: 0 vulnerabilities found in {task_args}"
            # Only summary touches main context
            self.main_context_history.append(f"[SKILL SUMMARY ({skill.name})]: {synthesized_summary}")
            return {
                "execution_mode": "forked",
                "subagent_events_count": len(subagent_scratchpad),
                "summary": synthesized_summary,
                "main_context_bloat_prevented": True
            }
        else:
            # Inline execution (adds everything to main context)
            self.main_context_history.append(f"[INLINE SKILL]: {skill.instructions}")
            return {
                "execution_mode": "inline",
                "summary": f"Executed inline: {skill.name}",
                "main_context_bloat_prevented": False
            }


def main() -> None:
    print("=" * 70)
    print("TS 3.2: Slash Commands & Skills Architecture Demo")
    print("=" * 70)

    runner = ClaudeCodeRunner()

    # 1. Slash Command
    cmd_template = "Review the pull request for branch $ARGUMENTS. Run lint and typecheck first."
    res_cmd = runner.execute_slash_command(cmd_template, "feature/auth-v2")
    print("\n1. Slash Command Execution:")
    print(res_cmd)

    # 2. Forked Skill
    skill_content = """---
name: code-auditor
description: Scans security boundaries without polluting main context.
context: fork
allowed-tools: [Read, Grep]
argument-hint: [path]
---
Audit the given directory thoroughly.
"""
    skill = SkillCommandParser.parse_skill_markdown(skill_content)
    res_skill = runner.execute_skill(skill, "src/auth")
    print("\n2. Forked Skill Execution:")
    print(json.dumps(res_skill, indent=2))

    print("\n3. Main Context History Size:")
    print(f"Total entries in main context: {len(runner.main_context_history)}")


if __name__ == "__main__":
    main()
