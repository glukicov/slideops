#!/usr/bin/env python3
"""Regenerate the README imagery from the demo deck.

Development tooling, not part of either skill. Requires Chrome and Pillow
(`uv sync --dev`). Run `--help` for the arguments.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
from typing import Annotated

import typer

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw, ImageFont

from smoke_test import find_chrome, run_chrome

WIDTH, HEIGHT = 1280, 720
SCALE = 2
SLOPE = 0.6
DIVIDER = (195, 169, 74)
LIGHT_INK = (122, 127, 31)
ROOT_BLOCK_RE = re.compile(r"  :root\{.*?\n  \}", re.S)
LABEL_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
LABEL_SIZE = 26
CARD_TRIM = (HEIGHT - WIDTH // 2) // 2
LABEL_INSET = (CARD_TRIM + 40) * SCALE


def theme_block(themes_md: str, name: str, next_name: str) -> str:
    """Lift a preset's :root block out of the reference the skill ships, re-indented."""
    section = themes_md[themes_md.index(f"## {name}") : themes_md.index(f"## {next_name}")]
    match = re.search(r"```css\n(.*?)```", section, re.S)
    if not match:
        sys.exit(f"No CSS block found for {name} in themes.md")
    css = match.group(1).rstrip("\n")
    return "\n".join(("  " + line if line.strip() else line) for line in css.splitlines())


def render(chrome: Path, deck: Path, out: Path) -> Image.Image:
    run_chrome(
        chrome,
        f"--window-size={WIDTH},{HEIGHT}",
        f"--force-device-scale-factor={SCALE}",
        f"--screenshot={out}",
        f"file://{deck}#1",
    )
    if not out.is_file():
        sys.exit(f"Chrome produced no screenshot for {deck}")
    return Image.open(out).convert("RGB")


def split_diagonally(light: Image.Image, dark: Image.Image) -> Image.Image:
    if light.size != dark.size:
        sys.exit(f"Renders differ in size: {light.size} vs {dark.size}")
    width, height = light.size
    supersample = 2

    def boundary(y: float) -> float:
        return width / 2 + (height / 2 - y) * SLOPE

    mask = Image.new("L", (width * supersample, height * supersample), 0)
    ImageDraw.Draw(mask).polygon(
        [
            (0, 0),
            (boundary(0) * supersample, 0),
            (boundary(height) * supersample, height * supersample),
            (0, height * supersample),
        ],
        fill=255,
    )
    hero = Image.composite(light, dark, mask.resize((width, height), Image.Resampling.LANCZOS))

    draw = ImageDraw.Draw(hero)
    draw.line([(boundary(0), 0), (boundary(height), height)], fill=DIVIDER, width=3)
    if Path(LABEL_FONT).is_file():
        font = ImageFont.truetype(LABEL_FONT, LABEL_SIZE)
        draw.text((LABEL_INSET, LABEL_INSET), "LEDGER LIGHT", font=font, fill=LIGHT_INK)
        label = "LEDGER DARK"
        draw.text(
            (
                width - LABEL_INSET - draw.textlength(label, font=font),
                height - LABEL_INSET - LABEL_SIZE,
            ),
            label,
            font=font,
            fill=DIVIDER,
        )
    return hero


app = typer.Typer(rich_markup_mode="markdown", add_completion=False)


@app.command()
def main(
    repo_root: Annotated[
        Path | None,
        typer.Argument(help="Repository to render from. Defaults to the one this script lives in."),
    ] = None,
) -> None:
    """Render the demo deck's title slide in both themes and split them diagonally.

    The two renders come straight from the token blocks in references/themes.md, so the
    README shows the same slide in Ledger Light and Ledger Dark at once. Writes
    docs/hero.png (the diagonal split), docs/theme-light.png and docs/theme-dark.png.

    The hero is a generated artifact of the deck, so it rots exactly like a slide does:
    edit the title slide and this must be re-run.
    """
    root = repo_root.resolve() if repo_root is not None else Path(__file__).resolve().parent.parent
    deck_source = root / "skills" / "slideops" / "examples" / "skill-demo.html"
    themes_md = root / "skills" / "slideops" / "references" / "themes.md"
    docs = root / "docs"
    for required in (deck_source, themes_md):
        if not required.is_file():
            sys.exit(f"Not found: {required}")
    docs.mkdir(exist_ok=True)

    deck_html = deck_source.read_text()
    if not ROOT_BLOCK_RE.search(deck_html):
        sys.exit("The demo deck has no :root block to swap")
    dark_block = theme_block(themes_md.read_text(), "Ledger Dark", "Midnight")

    chrome = find_chrome()
    print(f"Chrome: {chrome}")

    with tempfile.TemporaryDirectory(prefix="slideops-hero-") as tmp:
        stage = Path(tmp)
        light_deck = stage / "light.html"
        dark_deck = stage / "dark.html"
        light_deck.write_text(deck_html)
        dark_deck.write_text(ROOT_BLOCK_RE.sub(lambda _: dark_block, deck_html, count=1))

        light = render(chrome, light_deck, stage / "light.png")
        dark = render(chrome, dark_deck, stage / "dark.png")

        split_diagonally(light, dark).save(docs / "hero.png", optimize=True)
        for name, image in (("theme-light", light), ("theme-dark", dark)):
            image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(docs / f"{name}.png", optimize=True)

    for name in ("hero.png", "theme-light.png", "theme-dark.png"):
        size = (docs / name).stat().st_size / 1024
        print(f"  docs/{name}: {size:.0f} KB")
    print("OK: README imagery regenerated from the demo deck")


if __name__ == "__main__":
    app()
