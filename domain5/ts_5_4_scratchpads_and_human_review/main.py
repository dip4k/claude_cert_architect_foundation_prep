"""
Domain 5: Context Management & Reliability
Task Statement 5.4: Manage context effectively in large codebase exploration
Exam Scenario 4: Developer Productivity (code exploration)

Key Exam Concepts Demonstrated (all offline, no API calls):
1. Context degradation in long sessions: the model gives "typical patterns" instead of the
   specific classes it found earlier.
2. Scratchpad file: key findings are written to a file and re-read in later phases.
3. Explore subagent: verbose exploration stays isolated; only a compact summary returns.
4. Summarise a phase before spawning the next phase's subagents.
5. Crash recovery: each agent exports its state; a coordinator manifest is loaded on resume.
6. In Claude Code, `/compact` reduces context usage during a long exploration session.

Cross-reference: the human-review classes at the bottom belong to TS 5.5
(see domain5/ts_5_5_human_review_calibration). They stay here only for backward compatibility.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

# ==============================================================================
# 1. Scratchpad (persistent key findings)
# ==============================================================================


class CodebaseScratchpadManager:
    """Keeps key findings in a file-backed scratchpad to counteract context degradation."""

    def __init__(self) -> None:
        self.findings: List[str] = []

    def record_finding(self, finding: str) -> None:
        self.findings.append(finding)

    def render_scratchpad(self) -> str:
        lines = ["# CODEBASE EXPLORATION SCRATCHPAD (KEY FINDINGS)"]
        for idx, item in enumerate(self.findings, start=1):
            lines.append(f"{idx}. {item}")
        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Write the scratchpad to disk so it survives context resets and crashes."""
        path.write_text(self.render_scratchpad() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "CodebaseScratchpadManager":
        """Rebuild a scratchpad from a saved file (numbered lines after the title)."""
        pad = cls()
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            _, _, text = line.partition(". ")
            if text:
                pad.record_finding(text)
        return pad


# ==============================================================================
# 2. Explore subagent (isolate verbose output, return a compact summary)
# ==============================================================================


@dataclass
class ExploreSummary:
    """What the main session receives: findings plus size stats, not the raw file contents."""

    query: str
    findings: List[Dict[str, Any]]
    files_scanned: int
    raw_lines_seen: int


def explore_subagent(
    files: Mapping[str, str], needle: str, max_findings: int = 5
) -> ExploreSummary:
    """
    Scan many files and return only matching lines with file and line number.

    The raw text stays inside the subagent; the coordinator keeps a handful of specific facts.
    """
    findings: List[Dict[str, Any]] = []
    raw_lines = 0
    for name in sorted(files):
        for number, line in enumerate(files[name].splitlines(), start=1):
            raw_lines += 1
            if needle in line and len(findings) < max_findings:
                findings.append({"file": name, "line": number, "text": line.strip()})
    return ExploreSummary(needle, findings, len(files), raw_lines)


def summarise_phase(phase: str, summaries: List[ExploreSummary]) -> str:
    """Condense a finished phase into a short block to inject before spawning the next phase."""
    lines = [f"## Phase summary: {phase}"]
    for summary in summaries:
        for f in summary.findings:
            lines.append(f"- {f['file']}:{f['line']} {f['text']}")
    return "\n".join(lines)


# ==============================================================================
# 3. Crash recovery: per-agent state exports + coordinator manifest
# ==============================================================================


class CrashRecoveryManifest:
    """Each agent exports its state to a known file; the coordinator keeps a manifest."""

    MANIFEST_NAME = "manifest.json"

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def export_agent_state(self, agent_id: str, phase: str, findings: List[str]) -> Path:
        """Write one agent's state and register it in the manifest."""
        state_path = self.directory / f"{agent_id}.json"
        state_path.write_text(
            json.dumps({"agent_id": agent_id, "phase": phase, "findings": findings}, indent=2),
            encoding="utf-8",
        )
        manifest = self.load_manifest()
        manifest["agents"][agent_id] = {"phase": phase, "state_file": state_path.name}
        (self.directory / self.MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return state_path

    def load_manifest(self) -> Dict[str, Any]:
        """Return the manifest, or an empty one if no run has been recorded yet."""
        path = self.directory / self.MANIFEST_NAME
        if not path.exists():
            return {"agents": {}}
        loaded: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return loaded

    def resume_prompt(self, expected_agents: List[str]) -> str:
        """Build the text injected into the coordinator prompt on resume."""
        manifest = self.load_manifest()
        done = sorted(manifest["agents"])
        lines = ["## RESUME STATE (loaded from manifest)"]
        for agent_id in done:
            state = json.loads(
                (self.directory / manifest["agents"][agent_id]["state_file"]).read_text("utf-8")
            )
            lines.append(f"- {agent_id} (phase {state['phase']}) findings: {state['findings']}")
        pending = [a for a in expected_agents if a not in done]
        lines.append(f"- Still to run: {pending if pending else 'nothing'}")
        return "\n".join(lines)


# ==============================================================================
# 4. Backward-compatible human review helpers (canonical home: TS 5.5)
# ==============================================================================


@dataclass
class ExtractionRecord:
    doc_id: str
    doc_type: str  # "standard_invoice" | "customs_declaration" | "handwritten_receipt"
    confidence_score: float
    extracted_total: float
    requires_human_review: bool = False


class HumanReviewRoutingEngine:
    """Simple threshold routing and per-segment sampling (full model lives in TS 5.5)."""

    def __init__(self, confidence_threshold: float = 0.85) -> None:
        self.threshold = confidence_threshold

    def route_record(self, record: ExtractionRecord) -> ExtractionRecord:
        """Route low confidence records to human reviewers."""
        if record.confidence_score < self.threshold:
            record.requires_human_review = True
        return record

    @staticmethod
    def stratified_random_sample(
        records: List[ExtractionRecord],
        sample_size_per_segment: int = 2,
        seed: Optional[int] = None,
    ) -> List[ExtractionRecord]:
        """Sample up to N records from each document-type segment."""
        rng = random.Random(seed)
        segments: Dict[str, List[ExtractionRecord]] = {}
        for r in records:
            segments.setdefault(r.doc_type, []).append(r)
        sampled: List[ExtractionRecord] = []
        for name in sorted(segments):
            k = min(sample_size_per_segment, len(segments[name]))
            sampled.extend(rng.sample(segments[name], k))
        return sampled


def main() -> None:
    """Offline demo: explore, scratchpad, summarise, export state, resume."""
    import tempfile

    files = {
        "auth/service.py": "class TokenVerifier:\n    def verify(self): ...",
        "auth/legacy.py": "class TokenVerifier:  # v1\n    pass",
        "billing/api.py": "class InvoiceService:\n    pass",
    }
    summary = explore_subagent(files, "class TokenVerifier")
    print(f"Scanned {summary.files_scanned} files, {summary.raw_lines_seen} lines ->")
    print(f"{len(summary.findings)} findings returned to the main session")

    pad = CodebaseScratchpadManager()
    for f in summary.findings:
        pad.record_finding(f"TokenVerifier defined in {f['file']}:{f['line']}")
    print(pad.render_scratchpad())
    print(summarise_phase("auth discovery", [summary]))

    with tempfile.TemporaryDirectory() as tmp:
        manifest = CrashRecoveryManifest(Path(tmp))
        manifest.export_agent_state("auth-explorer", "discovery", pad.findings)
        print(manifest.resume_prompt(["auth-explorer", "billing-explorer"]))


if __name__ == "__main__":
    main()
