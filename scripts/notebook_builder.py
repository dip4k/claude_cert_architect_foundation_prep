"""
Jupyter Notebook Builder Utility for Claude Certification Practice Exercises.
Generates compliant, richly documented .ipynb notebooks for all domains and task statements.
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent


def to_source_lines(text: str) -> List[str]:
    """Convert multi-line string into lines preserving trailing newlines."""
    lines = text.strip().split("\n")
    return [line + "\n" if i < len(lines) - 1 else line for i, line in enumerate(lines)]


def markdown_cell(content: str, cell_id: Optional[str] = None) -> Dict[str, Any]:
    """Construct a Jupyter markdown cell."""
    return {
        "cell_type": "markdown",
        "id": cell_id or uuid.uuid4().hex[:8],
        "metadata": {},
        "source": to_source_lines(content),
    }


def code_cell(code: str, cell_id: Optional[str] = None) -> Dict[str, Any]:
    """Construct a Jupyter code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id or uuid.uuid4().hex[:8],
        "metadata": {},
        "outputs": [],
        "source": to_source_lines(code),
    }


def make_notebook(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wrap cell list in standard Jupyter notebook schema."""
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def save_notebook(domain_name: str, ts_slug: str, cells: List[Dict[str, Any]]) -> List[Path]:
    """
    Save notebook under:
    1. domain[X]/[ts_slug]/notebook.ipynb
    2. domain[X]/[ts_slug]/[ts_slug].ipynb
    3. domain[X]/[ts_slug].ipynb
    """
    nb_dict = make_notebook(cells)
    content = json.dumps(nb_dict, indent=1, ensure_ascii=False)

    domain_dir = REPO_ROOT / domain_name
    ts_dir = domain_dir / ts_slug
    ts_dir.mkdir(parents=True, exist_ok=True)

    paths = [
        ts_dir / "notebook.ipynb",
        ts_dir / f"{ts_slug}.ipynb",
        domain_dir / f"{ts_slug}.ipynb",
    ]

    for p in paths:
        p.write_text(content, encoding="utf-8")

    print(f" Saved notebook for {domain_name}/{ts_slug} to {len(paths)} locations")
    return paths
