"""
Offline unit tests verifying the integrity and token efficiency of .agents configuration,
rules, and interview preparation skills.
"""

from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / ".agents"
SKILLS_DIR = AGENTS_DIR / "skills"


def test_rule_integrity_and_efficiency():
    """Verify safety rule exists, has always_on trigger, and is compact."""
    rule_file = AGENTS_DIR / "rules" / "no_claude_api_execution.md"
    assert rule_file.exists(), "Safety rule file must exist"
    content = rule_file.read_text(encoding="utf-8")
    assert "trigger: always_on" in content
    assert "Strict Rule" in content or "Rule" in content
    # Ensure rule is compact (< 2500 bytes) to save system prompt tokens
    assert len(content.encode("utf-8")) < 2500


def test_gemini_and_agents_md_efficiency():
    """Verify GEMINI.md and AGENTS.md exist and are concise (< 3500 bytes)."""
    gemini_md = REPO_ROOT / "GEMINI.md"
    agents_md = REPO_ROOT / "AGENTS.md"

    assert gemini_md.exists()
    assert agents_md.exists()

    gemini_content = gemini_md.read_text(encoding="utf-8")
    agents_content = agents_md.read_text(encoding="utf-8")

    # Both must be compact to avoid context window explosion
    assert len(gemini_content.encode("utf-8")) < 3500
    assert len(agents_content.encode("utf-8")) < 3500

    # Ensure AGENTS.md doesn't have broken markdown code fences
    fence_count = agents_content.count("```")
    assert fence_count % 2 == 0, "AGENTS.md has unclosed code fences"


def test_skills_have_valid_frontmatter_and_concise_descriptions():
    """Verify all skills have name and description frontmatter under 200 characters."""
    skill_folders = [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
    assert len(skill_folders) >= 6, f"Expected at least 6 skills, found {len(skill_folders)}"

    frontmatter_pattern = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

    for skill_dir in skill_folders:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md missing in {skill_dir.name}"

        content = skill_file.read_text(encoding="utf-8")
        match = frontmatter_pattern.match(content)
        assert match, f"Frontmatter missing or invalid in {skill_file}"

        frontmatter_text = match.group(1)
        assert "name:" in frontmatter_text, f"Missing 'name' in {skill_file}"
        assert "description:" in frontmatter_text, f"Missing 'description' in {skill_file}"

        # Extract description value
        desc_match = re.search(r"description:\s*(.+)", frontmatter_text)
        assert desc_match, f"Could not parse description in {skill_file}"
        description = desc_match.group(1).strip()
        assert len(description) > 10, f"Description too short in {skill_file}"
        # Keep description under 200 chars for system prompt context efficiency
        assert len(description) <= 200, f"Description too long ({len(description)} chars) in {skill_file}"


def test_interview_coach_references_exist():
    """Verify that references linked in claude-interview-coach and claude-scenario-architect exist."""
    coach_dir = SKILLS_DIR / "claude-interview-coach"
    rubric = coach_dir / "references" / "rubric.md"
    question_bank = coach_dir / "references" / "question_bank.md"

    assert rubric.exists()
    assert question_bank.exists()

    rubric_content = rubric.read_text(encoding="utf-8")
    assert "Determinism vs. Probabilism" in rubric_content
    assert "Context Window Efficiency" in rubric_content

    qb_content = question_bank.read_text(encoding="utf-8")
    assert "Customer Support Refund Gate" in qb_content
    assert "MCP Tool Error Classification" in qb_content

    # Check scenario architect references
    scenario_dir = SKILLS_DIR / "claude-scenario-architect"
    traps = scenario_dir / "references" / "exam_traps.md"
    assert traps.exists()
    traps_content = traps.read_text(encoding="utf-8")
    assert "The Batch API CI Trap" in traps_content
    assert "The 0-Result Search Trap" in traps_content


def test_subagent_personas_exist():
    """Verify subagent persona files exist and are populated."""
    exam_mentor = AGENTS_DIR / "claude-exam-mentor.md"
    reviewer = AGENTS_DIR / "offline-code-reviewer.md"
    scaffolder = AGENTS_DIR / "claude-cert-scaffolder.md"

    assert exam_mentor.exists()
    assert reviewer.exists()
    assert scaffolder.exists()

    mentor_text = exam_mentor.read_text(encoding="utf-8")
    assert "Mode 1" in mentor_text or "Mock Exam" in mentor_text
