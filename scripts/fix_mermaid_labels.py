"""Set root-level htmlLabels: false on Mermaid flowcharts so GitHub does not clip node text."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".venv", ".git", "node_modules"}
FRONT = ["---", "config:", "  htmlLabels: false", "---"]
HEAD = re.compile(r"^\s*(flowchart|graph)\b")
LEGACY_MD = re.compile(r"config:(\r?\n)  flowchart:\r?\n    htmlLabels: false")
LEGACY_NB = re.compile(r'\r?\n[ ]*"  flowchart:\\n",(?=\r?\n[ ]*"    htmlLabels: false)')


def add_md(lines: list[str]) -> tuple[list[str], int]:
    out, n = [], 0
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() == "```mermaid" and i + 1 < len(lines) and HEAD.match(lines[i + 1]):
            out.extend(FRONT)
            n += 1
    return out, n


def add_nb(lines: list[str]) -> tuple[list[str], int]:
    out, n = [], 0
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip() == '"```mermaid\\n",' and i + 1 < len(lines):
            if HEAD.match(lines[i + 1].strip().lstrip('"')):
                indent = line[: len(line) - len(line.lstrip())]
                out.extend(f'{indent}"{f}\\n",' for f in FRONT)
                n += 1
    return out, n


def main() -> None:
    changed = 0
    for p in ROOT.rglob("*"):
        if p.suffix not in {".md", ".ipynb"} or SKIP & set(p.relative_to(ROOT).parts):
            continue
        text = p.read_bytes().decode("utf-8")
        new = LEGACY_MD.sub(r"config:\1  htmlLabels: false", text)
        new = LEGACY_NB.sub("", new).replace('"    htmlLabels: false\\n",', '"  htmlLabels: false\\n",')
        if "htmlLabels: false" not in new:
            nl = "\r\n" if "\r\n" in new else "\n"
            lines, n = (add_md if p.suffix == ".md" else add_nb)(new.split(nl))
            new = nl.join(lines) if n else new
        if new != text:
            p.write_bytes(new.encode("utf-8"))
            changed += 1
    print("files changed:", changed, file=sys.stderr)


if __name__ == "__main__":
    main()
