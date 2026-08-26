---
name: slides-to-pdf
description: Use when the user asks to convert, export, or save an HTML slide deck as a PDF ("save the slides as PDF", "export the deck to PDF", "make a PDF of the presentation"). Works on decks built by the SlideOps (slideops) skill and on any single-file HTML deck that shows one slide per URL hash (#1, #2, ...).
license: MIT
compatibility: Needs a headless Chrome or Chromium binary (Playwright cache or system install), Python 3, and pypdfium2 for PDF verification (already installed, or one pinned pip download into a throwaway venv). Works offline otherwise. macOS and Linux; Windows untested.
metadata:
  author: Gleb Lukicov
  version: 1.0.0
---

# Slides to PDF

Converts a JS-driven, one-slide-per-screen HTML deck into a paginated PDF: one page per
slide, pixel-identical to the browser rendering. There is no native "print to PDF" for
such decks (printing captures only the visible slide), so the pipeline is: screenshot
every slide at 2x with headless Chrome, wrap the screenshots in a print-paginated page,
print that to PDF, then verify the PDF by rendering it back to images.

Inputs to establish up front (ask only if not obvious):

- **Deck path**, the literal that marks one slide (default `<section class="slide"`), and
  the deck's canvas size (default 1280x720). Read the deck's own CSS to confirm both
  before you start; a wrong size silently letterboxes or crops every page.
- **Output path**: default next to the HTML, same basename, `.pdf`.
- **Chrome-only UI to hide**: for SlideOps decks this is `.hud,.progress,.hint`;
  for other decks, identify the fixed nav/progress elements a printed page shouldn't show.

## 1. Find Chrome and make a staging directory

```bash
find_chrome() {
  local base c
  for base in "$HOME/Library/Caches/ms-playwright" "$HOME/.cache/ms-playwright"; do
    [ -d "$base" ] || continue
    c=$(find "$base" -maxdepth 6 -type f \
          \( -name chrome -o -name Chromium -o -name "Google Chrome for Testing" \) \
          2>/dev/null | grep -v headless_shell | sort -V | tail -1)
    [ -n "$c" ] && { printf '%s\n' "$c"; return; }
  done
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "$(command -v google-chrome || true)" "$(command -v chromium || true)"; do
    [ -x "$c" ] && { printf '%s\n' "$c"; return; }
  done
}
CHROME=$(find_chrome)
[ -x "$CHROME" ] || { npx --yes playwright install chromium; CHROME=$(find_chrome); }
"$CHROME" --version   # sanity-check; quote "$CHROME" everywhere (macOS path has spaces)

DECK="/absolute/path/to/deck.html"
STAGE=$(mktemp -d -t slidespdf)   # or a per-deck subdir of your session scratchpad

# Per-deck settings. The defaults match SlideOps decks; change all three for a foreign one.
SLIDE_MATCH='<section class="slide'   # the literal that starts one slide element
W=1280; H=720                         # the deck's canvas size in CSS pixels
CHROME_SANDBOX_ARGS=()                # see "Sandbox" below before adding --no-sandbox

N=$(grep -c "$SLIDE_MATCH" "$DECK")
[ "$N" -gt 0 ] || { echo "No slides matched $SLIDE_MATCH; check the selector"; exit 1; }
echo "$N slides at ${W}x${H}"
```

Never reuse a fixed staging path: parallel exports collide. Everything below writes into
`$STAGE`; the directory is deleted at the end.

**Sandbox.** These commands deliberately do not pass `--no-sandbox`. You may be rendering
a deck you did not author, and the sandbox is what contains a malicious payload. Add it to
`CHROME_SANDBOX_ARGS` only when Chrome cannot start as root in a container that cannot
grant user namespaces, and tell the user you did; running as a non-root user is the better
fix.

## 2. Build an export copy

Two reasons not to screenshot the deck in place: relative image paths (`../img/...`)
break the moment screenshots need the HTML somewhere else, and the printed pages must not
show interactive-only chrome (nav buttons, progress bar, hints). Decks whose images are
inlined as `data:` URIs skip the path problem but still need the chrome hidden — build
the export copy either way:

```bash
IMG_DIR="/absolute/path/to/the/deck's/image/folder"   # any path is fine for an image-free deck
CHROME_HIDE='.hud,.progress,.hint'                    # SlideOps chrome; change for a foreign deck
python3 - "$DECK" "$STAGE" "$IMG_DIR" "$CHROME_HIDE" <<'EOF'
import sys
from pathlib import Path

deck, stage, img_dir, hide = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
content = deck.read_text()
content = content.replace('src="../img/', f'src="file://{img_dir}/')
content = content.replace('</head>',
    f'<style>{hide}{{display:none !important;}}</style></head>', 1)
(stage / "export.html").write_text(content)
EOF
```

Adapt the `src="../img/` prefix to the deck's actual relative-path shape, and the hidden
selectors to the deck's actual chrome.

## 3. Screenshot every slide at 2x, wrap, print

```bash
for i in $(seq 1 $N); do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars "${CHROME_SANDBOX_ARGS[@]}" \
    --window-size=$W,$H --force-device-scale-factor=2 \
    --screenshot="$STAGE/slide-$(printf "%02d" $i).png" \
    "file://$STAGE/export.html#${i}"
done
```

(`$W`/`$H` drive both the screenshots and the `@page` rule below, so a foreign deck only
needs those two numbers changed.)

```bash
python3 - "$STAGE" "$N" "$W" "$H" <<'EOF'
import sys
from pathlib import Path

stage, n, w, h = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
pages = "\n".join(
    f'<div class="page"><img src="slide-{i:02d}.png"></div>' for i in range(1, n + 1))
(stage / "print.html").write_text(f'''<style>
  @page {{ size: {w}px {h}px; margin: 0; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  .page {{ width: {w}px; height: {h}px; overflow: hidden; page-break-after: always; }}
  .page:last-child {{ page-break-after: auto; }}
  .page img {{ width: {w}px; height: {h}px; display: block; }}
</style>
{pages}''')
EOF

"$CHROME" --headless=new --disable-gpu "${CHROME_SANDBOX_ARGS[@]}" \
  --print-to-pdf="$STAGE/output.pdf" --no-pdf-header-footer \
  "file://$STAGE/print.html"
```

## 4. Verify: headless Chrome cannot rasterize a local PDF

`chrome --headless=new --screenshot` against a `file://…pdf` URL produces a blank/dark
image (no PDF viewer in headless mode); don't trust it as a check. Render the PDF back to
images with a real PDF library in a throwaway venv:

```bash
python3 -m venv "$STAGE/venv"
"$STAGE/venv/bin/pip" install --quiet pypdfium2 Pillow
"$PDFPY" - "$STAGE" <<'EOF'
import sys
import pypdfium2 as pdfium
stage = sys.argv[1]
pdf = pdfium.PdfDocument(f"{stage}/output.pdf")
print("page count:", len(pdf))          # must equal the slide count
for i in range(len(pdf)):
    pdf[i].render(scale=1.5).to_pil().save(f"{stage}/check-{i+1:02d}.png")
EOF
```

Then **view a representative sample** with your image tool: the first page, the last
page, and every page that embeds an image. A PDF can have the right page count while
every image page is silently blank (the relative-path gotcha step 2 exists to prevent);
only rendering pages back to images catches that.

## 5. Ship and clean up

Copy the verified `output.pdf` to the output path (default: next to the HTML, `.pdf`
extension), then delete the entire `$STAGE` directory. Nothing but the PDF should remain.

## Companion skill

Decks in this format are produced by the **SlideOps** (`slideops`) skill, whose Step 5 defers
to this skill for PDF export. This skill is self-contained: it does not require
slideops to be installed.
