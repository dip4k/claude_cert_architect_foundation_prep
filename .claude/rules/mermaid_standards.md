---
paths:
  - "**/*.md"
  - "**/*.ipynb"
---

# GitHub Mermaid Rendering Standards (October 2026)

All Mermaid diagrams in Markdown files and Jupyter notebooks must follow these standards to ensure 100% reliable rendering on GitHub:

1. **Quoted Node Labels**:
   - Always wrap node labels containing spaces, parentheses, brackets, colons, hyphens, or math symbols in double quotes:
     - ✅ `NodeA["Client Request (HTTPS)"]`
     - ❌ `NodeA[Client Request (HTTPS)]` (unquoted parentheses break parser)

2. **No Raw HTML Tags Inside Labels**:
   - Do not use `<b>`, `</b>`, `<i>`, or `<span>` inside node labels. Use clean text or Markdown backticks.
   - For line breaks within labels, use `<br>` inside double-quoted strings:
     - ✅ `NodeB["Step 1: Auth Gate<br>(Verified ID)"]`

3. **No Fragile Init Directives**:
   - Never include `%%{init: {"flowchart": {"htmlLabels": true, "padding": 20}}}%%`. GitHub's theme engine manages layout padding natively.

4. **SVG Labels via Frontmatter**:
   - Every `flowchart` starts with this frontmatter so node text is not clipped (HTML label width is mis-measured). Use the root-level key; `flowchart.htmlLabels` is deprecated:
     `---` / `config:` / `  htmlLabels: false` / `---`
   - Apply or repair it across the repo with `scripts/fix_mermaid_labels.py`.

5. **Explicit Flow Direction**:
   - Always declare an explicit diagram orientation: `flowchart TD` (top-down) or `flowchart LR` (left-to-right).

6. **Safe Edge Syntax**:
   - Format edge text with valid syntax: `-->|"Link Text"|` or `-- "Link Text" -->`.
   - Never leave unquoted special characters in transition labels.
