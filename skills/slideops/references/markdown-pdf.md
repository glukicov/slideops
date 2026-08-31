# Markdown doc to PDF

Exports a doc built by [`markdown.md`](markdown.md) as a paginated PDF. The pipeline
differs from the slides-to-pdf skill in one structural way: a doc is a flowing document,
so there are no per-page screenshots. Convert the Markdown to HTML, wrap it in print
CSS, and let Chrome's own print pagination break the pages. The verification step is the
same, because headless Chrome cannot rasterize a local PDF to check its own output.

Inputs to establish up front: the doc path, the output path (default: next to the `.md`,
same basename, `.pdf`), and whether the doc contains `mermaid` fences (they need
pre-rendering; see step 2).

## 1. Find Chrome and make a staging directory

Chrome discovery and the staging rules are in
[`verification.md`](verification.md): always a fresh per-export directory, never a
fixed shared path, and do not add `--no-sandbox` (you may be printing a doc you did not
author).

```bash
DOC="/absolute/path/to/doc.md"
STAGE=$(mktemp -d -t mdpdf)
```

## 2. Convert the Markdown to HTML

Use any GitHub-flavored converter already available (`pandoc`, `marked`, a Python
`markdown-it` install). If none is installed, one npx download does it, the same network
opt-in the skill uses for Mermaid:

```bash
npx --yes marked --gfm -i "$DOC" -o "$STAGE/body.html"
```

Two fix-ups on the produced body, both mechanical:

- **Relative image paths** break the moment the HTML lives in `$STAGE`. Rewrite each
  `src` to an absolute `file://` path resolved from the doc's own directory.
- **Mermaid fences** come out as plain `<code class="language-mermaid">` blocks, which
  print as source text. Pre-render each one to SVG with mermaid-cli exactly as
  [`diagrams.md`](diagrams.md) § Render recipe does for decks, and replace the
  code block with the inline SVG. If the user declined network access, say so and leave
  the fence as a code block rather than dropping it.

The citation comments need no handling: HTML comments are invisible in print.

## 3. Wrap in print CSS and print

```bash
python3 - "$STAGE" <<'EOF'
from pathlib import Path
import sys

stage = Path(sys.argv[1])
body = (stage / "body.html").read_text()
(stage / "print.html").write_text(f"""<!doctype html><meta charset="utf-8"><style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font: 11pt/1.55 -apple-system, "Segoe UI", Roboto, sans-serif;
          max-width: 100%; margin: 0; }}
  h1, h2, h3 {{ line-height: 1.25; page-break-after: avoid; }}
  pre {{ font: 8.5pt/1.45 ui-monospace, "SF Mono", Consolas, monospace;
         padding: 8pt 10pt; border: 0.5pt solid #ccc; border-radius: 4pt;
         white-space: pre-wrap; page-break-inside: avoid; }}
  img, svg {{ max-width: 100%; }}
  table {{ border-collapse: collapse; }}
  td, th {{ border: 0.5pt solid #999; padding: 3pt 8pt; }}
</style>
{body}""")
EOF

"$CHROME" --headless=new --disable-gpu \
  --print-to-pdf="$STAGE/output.pdf" --no-pdf-header-footer \
  "file://$STAGE/print.html"
```

## 4. Verify by rendering the PDF back to images

Identical to the slides-to-pdf verification, and just as mandatory: render every page
back to an image with pypdfium2 (throwaway venv if it is not installed), then actually
view the first page, the last page, and every page that should contain an image or a
diagram. The classic silent failure is a broken image path producing a right-looking
page count with a blank page in the middle.

```bash
python3 -m venv "$STAGE/venv" && "$STAGE/venv/bin/pip" install --quiet pypdfium2 Pillow
"$STAGE/venv/bin/python" - "$STAGE" <<'EOF'
import sys
import pypdfium2 as pdfium

stage = sys.argv[1]
pdf = pdfium.PdfDocument(f"{stage}/output.pdf")
print("page count:", len(pdf))
for i in range(len(pdf)):
    pdf[i].render(scale=1.5).to_pil().save(f"{stage}/check-{i + 1:02d}.png")
EOF
```

## 5. Ship and clean up

Copy the verified `output.pdf` to the output path, delete `$STAGE` entirely, and note in
your summary that the PDF is a snapshot: `check.py` verifies the `.md`, and a re-export
after a repair is how the PDF catches up.
