"""
Unit tests validating GitHub Mermaid diagram rendering standards across all Markdown files and Jupyter notebooks.
Ensures zero rendering failures, valid quotes, escaped HTML/TAGSTART characters, and proper frontmatter.
"""

import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", ".venv-win", ".git", "node_modules"}


def validate_mermaid_block(code: str, origin: str) -> list[str]:
    issues = []
    lines = code.split("\n")

    in_frontmatter = False
    content_lines = []
    has_frontmatter = False
    frontmatter_lines = []

    for idx, raw_l in enumerate(lines):
        stripped = raw_l.strip()
        if idx == 0 and stripped == "---":
            in_frontmatter = True
            has_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            else:
                frontmatter_lines.append(stripped)
            continue
        content_lines.append((idx + 1, raw_l))

    first_cmd = ""
    for _, raw_l in content_lines:
        line = raw_l.strip()
        if line and not line.startswith("%%"):
            first_cmd = line.split()[0]
            break

    is_flowchart = first_cmd in ("flowchart", "graph")
    is_sequence = first_cmd == "sequenceDiagram"

    if is_flowchart:
        if not has_frontmatter:
            issues.append(f"{origin}: Missing frontmatter (config: htmlLabels: false) on flowchart")
        else:
            fm_text = "\n".join(frontmatter_lines)
            if "htmlLabels: false" not in fm_text:
                issues.append(f"{origin}: Frontmatter missing 'htmlLabels: false'")

    subgraph_count = 0
    end_count = 0
    par_count = 0

    for line_no, raw_l in content_lines:
        line = raw_l.strip()
        if not line:
            continue
        if line.startswith("%%"):
            if "%%{init:" in line:
                issues.append(f"{origin} L{line_no}: Prohibited %%{{init: directive: {line}")
            continue

        if is_flowchart:
            if line.startswith("subgraph"):
                subgraph_count += 1
            elif line == "end":
                end_count += 1
        elif is_sequence:
            if line.startswith("par "):
                par_count += 1
            elif line == "end":
                if par_count > 0:
                    par_count -= 1
                else:
                    end_count += 1

        # Check for odd number of quotes
        clean_q = line.replace('\\"', '')
        q_count = clean_q.count('"')
        if q_count % 2 != 0:
            issues.append(f"{origin} L{line_no}: Odd number of double quotes ({q_count}): {line}")

        # Check for stray double quote inside single quotes or brackets
        if re.search(r"['`][^'`\"]*\"[^'`\"]*['`]", line):
            issues.append(f"{origin} L{line_no}: Stray double quote inside quotes: {line}")

        # Check for disallowed raw HTML tags
        html_tags = re.findall(r'<(?!/?br\b)[a-zA-Z/][^>]*>', line)
        if html_tags:
            issues.append(f"{origin} L{line_no}: Disallowed HTML tags {html_tags}: {line}")

        # Check for unescaped < in line (causes TAGSTART error in Mermaid unless <br>)
        clean_line = re.sub(r'<\/?br\s*\/?>', '', line, flags=re.IGNORECASE)
        if '<' in clean_line:
            issues.append(f"{origin} L{line_no}: Unescaped '<' (causes TAGSTART error in Mermaid): {line}")

        if is_flowchart:
            # Check edge labels: -->|Label|
            edge_labels = re.findall(r'\|([^|\n]+)\|', line)
            for el in edge_labels:
                if not (el.startswith('"') and el.endswith('"')):
                    if any(c in el for c in " ():,;-/<>"):
                        issues.append(f"{origin} L{line_no}: Edge label not enclosed in quotes: |{el}|")

            # Check unquoted bracket labels
            line_no_quotes = re.sub(r'"[^"]*"', '""', line)
            unquoted_brackets = re.findall(r'\b([A-Za-z0-9_]+)\[([^"\]\n][^\]\n]*)\]', line_no_quotes)
            for node_id, inner in unquoted_brackets:
                if inner != "" and any(c in inner for c in " ():,;-/"):
                    issues.append(f"{origin} L{line_no}: Node '{node_id}' has unquoted bracket label: [{inner}]")

    if is_flowchart and subgraph_count != end_count:
        issues.append(f"{origin}: Subgraph mismatch: {subgraph_count} subgraph(s) vs {end_count} end(s)")

    return issues


def test_all_mermaid_diagrams_render_cleanly():
    """Scan all markdown files and notebooks to verify all Mermaid diagrams pass GitHub standards."""
    all_issues = []
    total_diagrams = 0

    for p in REPO_ROOT.rglob("*"):
        if any(skip in p.parts for skip in SKIP_DIRS):
            continue
        if p.suffix == ".md":
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = list(re.finditer(r"```mermaid\r?\n(.*?)```", text, re.DOTALL))
            for i, m in enumerate(matches, 1):
                total_diagrams += 1
                origin = f"{p.relative_to(REPO_ROOT)} (diag {i})"
                all_issues.extend(validate_mermaid_block(m.group(1), origin))

        elif p.suffix == ".ipynb":
            text = p.read_text(encoding="utf-8", errors="ignore")
            try:
                nb = json.loads(text)
            except Exception:
                continue
            diag_idx = 0
            for c_idx, cell in enumerate(nb.get("cells", [])):
                if cell.get("cell_type") == "markdown":
                    src = "".join(cell.get("source", []))
                    matches = list(re.finditer(r"```mermaid\r?\n(.*?)```", src, re.DOTALL))
                    for m in matches:
                        total_diagrams += 1
                        diag_idx += 1
                        origin = f"{p.relative_to(REPO_ROOT)} (cell {c_idx}, diag {diag_idx})"
                        all_issues.extend(validate_mermaid_block(m.group(1), origin))

    assert total_diagrams > 100, f"Expected >100 diagrams, found {total_diagrams}"
    if all_issues:
        pytest.fail(f"Found {len(all_issues)} Mermaid diagram issues across repository:\n" + "\n".join(all_issues))
