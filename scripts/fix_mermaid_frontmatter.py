"""Insert SVG-label frontmatter into Mermaid flowcharts so GitHub does not clip node text."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".venv", ".git", "node_modules"}
FRONT = ["---", "config:", "  flowchart:", "    htmlLabels: false", "---"]
HEAD = re.compile(r"^\s*(flowchart|graph)\b")


def process_md(lines: list[str]) -> tuple[list[str], int]:
    out, n, i = [], 0, 0
    while i < len(lines):
        out.append(lines[i])
        if lines[i].strip() == "```mermaid" and i + 1 < len(lines) and HEAD.match(lines[i + 1]):
            out.extend(FRONT)
            n += 1
        i += 1
    return out, n


def process_ipynb(lines: list[str]) -> tuple[list[str], int]:
    out, n = [], 0
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() == '"```mermaid\\n",' and i + 1 < len(lines):
            nxt = lines[i + 1].strip().lstrip('"')
            if HEAD.match(nxt):
                indent = line[: len(line) - len(line.lstrip())]
                out.extend(f'{indent}"{f}\\n",' for f in FRONT)
                n += 1
    return out, n


def main() -> None:
    total = 0
    for p in ROOT.rglob("*"):
        if p.suffix not in {".md", ".ipynb"} or SKIP & set(p.relative_to(ROOT).parts):
            continue
        text = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in text else "\n"
        lines = text.split(nl)
        fn = process_md if p.suffix == ".md" else process_ipynb
        new, n = fn(lines)
        if n:
            p.write_text(nl.join(new), encoding="utf-8", newline="")
            total += n
            print(f"{n:3d} {p.relative_to(ROOT)}", file=sys.stderr)
    print("total", total)


if __name__ == "__main__":
    main()
