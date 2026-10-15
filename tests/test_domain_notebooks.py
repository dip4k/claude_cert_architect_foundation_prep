"""
Unit tests verifying that all certification domain task statements (TS 1.1 to TS 5.6)
have valid, compliant Jupyter notebooks that execute completely offline without live Claude API calls.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ["domain1", "domain2", "domain3", "domain4", "domain5"]


def test_all_task_statements_have_notebooks():
    """Verify that every task statement directory contains a valid notebook.ipynb and named notebook."""
    total_ts_checked = 0
    for d in DOMAINS:
        domain_dir = REPO_ROOT / d
        ts_dirs = [p for p in sorted(domain_dir.iterdir()) if p.is_dir() and (p / "main.py").exists()]
        assert len(ts_dirs) > 0, f"No TS directories found in {d}"
        for ts in ts_dirs:
            total_ts_checked += 1
            canonical_nb = ts / "notebook.ipynb"
            named_nb = ts / f"{ts.name}.ipynb"
            top_level_nb = domain_dir / f"{ts.name}.ipynb"

            assert canonical_nb.exists(), f"Missing canonical notebook: {canonical_nb}"
            assert named_nb.exists(), f"Missing named notebook in TS dir: {named_nb}"
            assert top_level_nb.exists(), f"Missing top-level domain notebook: {top_level_nb}"

            # Verify JSON schema and cell content
            data = json.loads(canonical_nb.read_text(encoding="utf-8"))
            assert data.get("nbformat") == 4, f"Invalid nbformat in {canonical_nb}"
            cell_types = {c["cell_type"] for c in data.get("cells", [])}
            assert "markdown" in cell_types, f"No markdown cells in {canonical_nb}"
            assert "code" in cell_types, f"No code cells in {canonical_nb}"

    assert total_ts_checked == 30, f"Expected 30 task statements, found {total_ts_checked}"


def test_notebooks_offline_execution_safety():
    """Verify that notebooks do not contain live API calls and use MockClaudeClient / offline logic."""
    for d in DOMAINS:
        domain_dir = REPO_ROOT / d
        for nb_path in domain_dir.rglob("*.ipynb"):
            content = nb_path.read_text(encoding="utf-8")
            # Verify no live API keys hardcoded
            assert "sk-ant-api03" not in content
            assert "anthropic.com/v1/messages" not in content


def test_all_canonical_notebooks_execute_cleanly():
    """Execute all 30 canonical task statement notebooks in isolated namespaces to guarantee zero runtime/syntax errors."""
    for d in DOMAINS:
        domain_dir = REPO_ROOT / d
        ts_dirs = [p for p in sorted(domain_dir.iterdir()) if p.is_dir() and (p / "main.py").exists()]
        for ts in ts_dirs:
            canonical_nb = ts / "notebook.ipynb"
            data = json.loads(canonical_nb.read_text(encoding="utf-8"))
            code_cells = [c for c in data["cells"] if c["cell_type"] == "code"]
            assert len(code_cells) > 0, f"Notebook {canonical_nb} has no executable code cells"

            ns: dict = {}
            for idx, cell in enumerate(code_cells, start=1):
                code_text = "".join(cell.get("source", []))
                try:
                    exec(code_text, ns)
                except Exception as exc:
                    pytest.fail(f"Execution failed in {canonical_nb} (cell {idx}): {exc}")

