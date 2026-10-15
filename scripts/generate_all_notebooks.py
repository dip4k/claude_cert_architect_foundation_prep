"""
Master Notebook Generator & Comprehensive Validation Suite.
Generates all 30 Task Statement notebooks across Domains 1 to 5,
and verifies schema validity and offline execution for every notebook.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.build_domain1_notebooks as d1
import scripts.build_domain2_notebooks as d2
import scripts.build_domain3_notebooks as d3
import scripts.build_domain4_notebooks as d4
import scripts.build_domain5_notebooks as d5


def generate_all() -> None:
    print("=" * 60)
    print("🚀 GENERATING ALL DOMAIN NOTEBOOKS (DOMAINS 1 - 5)")
    print("=" * 60)
    d1.main()
    d2.main()
    d3.main()
    d4.main()
    d5.main()
    print(" All domain notebooks generated.\n")


def validate_all_notebooks() -> None:
    print("=" * 60)
    print("🔬 VALIDATING AND EXECUTING ALL NOTEBOOK CODE CELLS OFFLINE")
    print("=" * 60)

    domains = ["domain1", "domain2", "domain3", "domain4", "domain5"]
    notebook_files = []
    for d in domains:
        d_path = REPO_ROOT / d
        for nb in sorted(d_path.rglob("*.ipynb")):
            notebook_files.append(nb)

    print(f"Discovered {len(notebook_files)} notebook files across 5 domains.")

    # We validate execution on the canonical 'notebook.ipynb' in each TS folder
    canonical_notebooks = [nb for nb in notebook_files if nb.name == "notebook.ipynb"]
    print(f"Validating execution for {len(canonical_notebooks)} canonical Task Statement notebooks...\n")

    passed_count = 0
    for nb_path in canonical_notebooks:
        rel_path = nb_path.relative_to(REPO_ROOT)
        with open(nb_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Schema checks
        assert data.get("nbformat") == 4, f"{rel_path}: Invalid nbformat"
        assert "cells" in data, f"{rel_path}: Missing cells"
        cell_types = {c["cell_type"] for c in data["cells"]}
        assert "markdown" in cell_types, f"{rel_path}: Missing markdown cells"
        assert "code" in cell_types, f"{rel_path}: Missing code cells"

        # 2. Execution check
        ns: dict = {}
        code_cells = [c for c in data["cells"] if c["cell_type"] == "code"]
        for idx, cell in enumerate(code_cells, start=1):
            code_text = "".join(cell.get("source", []))
            try:
                exec(code_text, ns)
            except Exception as exc:
                print(f"❌ Execution failed in {rel_path} cell {idx}:\n{exc}")
                raise

        passed_count += 1
        print(f" PASS: {rel_path} ({len(code_cells)} code cells executed cleanly)")

    print("\n" + "=" * 60)
    print(f" ALL {passed_count} TASK STATEMENT NOTEBOOKS FULLY VALIDATED & EXECUTED OFFLINE!")
    print("=" * 60)


if __name__ == "__main__":
    generate_all()
    validate_all_notebooks()
