#!/usr/bin/env python3
"""End-to-end smoke test: render the example deck and export a verified PDF.

Requires a Chromium binary (Playwright cache or system install), plus pypdfium2 and
Pillow for the PDF check. Development tooling for this repository; the skills themselves
depend on nothing. Run `--help` for the arguments.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

WIDTH, HEIGHT = 1280, 720
MIN_PNG_BYTES = 5_000


def find_chrome() -> Path:
    caches = [Path.home() / "Library/Caches/ms-playwright", Path.home() / ".cache/ms-playwright"]
    candidates: list[Path] = []
    for cache in caches:
        if cache.is_dir():
            for name in ("chrome", "Chromium", "Google Chrome for Testing", "headless_shell"):
                candidates += [p for p in cache.glob(f"chromium*/**/{name}") if p.is_file()]
    preferred = [p for p in candidates if "headless_shell" not in p.name]
    candidates = preferred or candidates
    if candidates:
        return sorted(candidates)[-1]

    for system in (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
    ):
        if system.exists():
            return system
    sys.exit("No Chrome/Chromium found. Install one, e.g. npx playwright install chromium")


def run_chrome(chrome: Path, *args: str) -> None:
    result = subprocess.run(
        [str(chrome), "--headless=new", "--disable-gpu", "--hide-scrollbars", *args],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        sys.exit(f"Chrome failed ({result.returncode}): {result.stderr.strip()[:500]}")


app = typer.Typer(rich_markup_mode="markdown", add_completion=False)


@app.command()
def main(
    repo_root: Annotated[
        Path | None,
        typer.Argument(help="Repository to test. Defaults to the one this script lives in."),
    ] = None,
    pdf_out: Annotated[
        Path | None,
        typer.Option(
            "--pdf-out", help="Keep the verified PDF here instead of discarding it with the staging directory."
        ),
    ] = None,
) -> None:
    """Render every slide of the example deck, then export a PDF and verify it.

    Proves the two things a broken change breaks first: every slide renders to a non-blank
    image, and the PDF pipeline produces one page per slide with real pixels on each. CI
    runs exactly this.

    --pdf-out is how the release asset is built. The demo PDF is a build artifact rather
    than a tracked file, so it is never in the repository that a /plugin install downloads.
    """
    root = repo_root.resolve() if repo_root is not None else Path(__file__).resolve().parent.parent
    pdf_out = pdf_out.resolve() if pdf_out is not None else None
    deck = root / "skills" / "slideops" / "examples" / "skill-demo.html"
    if not deck.is_file():
        sys.exit(f"Example deck not found: {deck}")

    stage = root / ".smoke"
    stage.mkdir(exist_ok=True)
    chrome = find_chrome()
    print(f"Chrome: {chrome}")

    slide_count = len(re.findall(r'<section class="slide', deck.read_text()))
    print(f"Deck: {deck.name}, {slide_count} slides")
    if slide_count == 0:
        sys.exit("Deck contains no slides")

    export = stage / "export.html"
    export.write_text(
        deck.read_text().replace(
            "</head>",
            "<style>.hud,.progress,.hint{display:none !important;}</style></head>",
            1,
        )
    )

    for index in range(1, slide_count + 1):
        shot = stage / f"slide-{index:02d}.png"
        run_chrome(
            chrome,
            f"--window-size={WIDTH},{HEIGHT}",
            "--force-device-scale-factor=2",
            f"--screenshot={shot}",
            f"file://{export}#{index}",
        )
        if not shot.is_file():
            sys.exit(f"Slide {index} produced no screenshot")
        if shot.stat().st_size < MIN_PNG_BYTES:
            sys.exit(f"Slide {index} rendered blank ({shot.stat().st_size} bytes)")
    print(f"Rendered {slide_count} non-blank slides")

    pages = "\n".join(f'<div class="page"><img src="slide-{i:02d}.png"></div>' for i in range(1, slide_count + 1))
    (stage / "print.html").write_text(
        f"""<style>
  @page {{ size: {WIDTH}px {HEIGHT}px; margin: 0; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  .page {{ width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; page-break-after: always; }}
  .page:last-child {{ page-break-after: auto; }}
  .page img {{ width: {WIDTH}px; height: {HEIGHT}px; display: block; }}
</style>
{pages}"""
    )

    pdf_path = stage / "output.pdf"
    run_chrome(
        chrome,
        f"--print-to-pdf={pdf_path}",
        "--no-pdf-header-footer",
        f"file://{stage / 'print.html'}",
    )
    if not pdf_path.is_file():
        sys.exit("PDF was not produced")

    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.exit("pypdfium2 is required to verify the PDF: pip install pypdfium2 Pillow")

    pdf = pdfium.PdfDocument(pdf_path)
    if len(pdf) != slide_count:
        sys.exit(f"PDF has {len(pdf)} pages, expected {slide_count}")

    for page_index in {0, len(pdf) // 2, len(pdf) - 1}:
        image = pdf[page_index].render(scale=0.5).to_pil()
        colours = image.convert("RGB").getcolors(maxcolors=256)
        if colours is not None and len(colours) <= 1:
            sys.exit(f"PDF page {page_index + 1} rendered blank")
    print(f"PDF verified: {len(pdf)} pages, sampled pages have real content")

    if pdf_out is not None:
        pdf.close()
        pdf_out.parent.mkdir(parents=True, exist_ok=True)
        pdf_out.write_bytes(pdf_path.read_bytes())
        print(f"Wrote {pdf_out} ({pdf_out.stat().st_size / 1_048_576:.1f} MB)")

    print("OK: render and export smoke test passed")


if __name__ == "__main__":
    app()
