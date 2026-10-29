"""
Unit tests verifying that all 6 production scenarios (Scenario 1 to Scenario 6)
have interactive workbench notebooks (scenario_workbench.ipynb) that execute cleanly offline.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = REPO_ROOT / "scenarios"


def test_all_scenarios_have_workbenches():
    """Verify that each of the 6 production scenarios has a valid scenario_workbench.ipynb."""
    scenario_dirs = [p for p in sorted(SCENARIOS_DIR.iterdir()) if p.is_dir() and p.name.startswith("scenario_")]
    assert len(scenario_dirs) == 6, f"Expected 6 scenario directories, found {len(scenario_dirs)}"

    for s_dir in scenario_dirs:
        nb_path = s_dir / "scenario_workbench.ipynb"
        assert nb_path.exists(), f"Missing scenario workbench in {s_dir.name}"

        data = json.loads(nb_path.read_text(encoding="utf-8"))
        assert data.get("nbformat") == 4, f"Invalid nbformat in {nb_path}"
        cell_types = {c["cell_type"] for c in data.get("cells", [])}
        assert "markdown" in cell_types, f"No markdown cells in {nb_path}"
        assert "code" in cell_types, f"No code cells in {nb_path}"


def test_scenario_workbenches_offline_safety():
    """Verify that scenario workbenches do not contain live API keys."""
    for nb_path in SCENARIOS_DIR.rglob("*.ipynb"):
        content = nb_path.read_text(encoding="utf-8")
        assert "sk-ant-api03" not in content
        assert "anthropic.com/v1/messages" not in content


def test_all_scenario_workbenches_execute_cleanly():
    """Execute all 6 scenario workbenches in isolated namespaces to guarantee zero runtime errors."""
    scenario_dirs = [p for p in sorted(SCENARIOS_DIR.iterdir()) if p.is_dir() and p.name.startswith("scenario_")]
    for s_dir in scenario_dirs:
        nb_path = s_dir / "scenario_workbench.ipynb"
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        code_cells = [c for c in data["cells"] if c["cell_type"] == "code"]
        assert len(code_cells) > 0, f"Notebook {nb_path} has no code cells"

        ns: dict = {}
        for idx, cell in enumerate(code_cells, start=1):
            code_str = "".join(cell.get("source", []))
            try:
                exec(code_str, ns)
            except Exception as exc:
                pytest.fail(f"Execution error in {s_dir.name}/scenario_workbench.ipynb cell {idx}: {exc}")
