# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

SlideOps is not an application: it is two **Agent Skills** (markdown + two Python scripts)
that get installed onto other people's machines, plus the development harness that proves
they work. Almost every rule below follows from that split:

- `skills/slideops/` and `skills/slides-to-pdf/` — **shipped**. Standard library only.
- `scripts/`, `tests/`, `pyproject.toml` — **development harness**. Never installed, free
  to use third-party deps (`typer`, `pypdfium2`, `Pillow`).

The repo is also its own Claude Code plugin marketplace (`.claude-plugin/`), so the same
tree is both the source and the distribution channel.

## Commands

```bash
uv sync --dev                # setup; uv fetches Python 3.14 from .python-version
uv run ruff check .          # lint
uv run ruff format --check . # format
uv run ty check              # types — this repo uses ty, NOT mypy
uv run pytest                # unit + freshness end-to-end tests
uv run python scripts/validate.py     # frontmatter, template invariants, manifest versions
uv run python scripts/smoke_test.py   # render every slide, export and verify a PDF (needs Chromium)
```

Single test: `uv run pytest tests/test_freshness.py::test_a_deleted_file_reports_missing`.

CI runs all of the above plus two guards that are easy to trip locally:

```bash
# the demo deck's citations must still match this repo
uv run python skills/slideops/scripts/check.py skills/slideops/examples/skill-demo.html --repo .
# the shipped scripts must run on bare python3 with nothing installed
python3 skills/slideops/scripts/check.py skills/slideops/examples/skill-demo.html --repo .
```

`uv run pre-commit install` wires ruff, ty, pytest and validate.py into every commit.

## The citation mechanism (the core idea)

A deck is a single self-contained HTML file. Every quoted snippet carries
`data-src="path/file.py:40-58"` and `data-sha256="<12 hex>"`, and the `<head>` carries
`<meta name="slideops-build" content="commit=… date=… repo=…">`. Those two facts are what
make a generated document checkable later:

- **`skills/slideops/scripts/cite.py`** writes them (at build time, and `--stamp` for the
  build meta). Hashes and dates are never typed by hand — a wrong one is worse than none.
- **`skills/slideops/scripts/check.py`** reads them back and re-reads the repository,
  classifying each citation `CURRENT` / `MOVED` / `CHANGED` / `MISSING` / `UNVERIFIED`.
  `--json` emits a full repair brief (diff, causing commits, corrected attributes) so an
  agent can fix only the drifted slides without re-reading the repo.

Everything else in `skills/slideops/` — `SKILL.md`, `assets/template.html`, the six
`references/*.md` specs — is the prose contract an agent follows to produce decks that
carry those attributes. `SKILL.md` is the entry point and delegates detail to
`references/`; keep that split rather than growing SKILL.md.

## Invariants enforced by tooling

Break one of these and CI fails, usually far from where you edited:

1. **No third-party imports in `skills/**/scripts/`.** The portability job installs the
   skill the way a user does and runs it on bare Python. Shipped scripts use `argparse`;
   dev scripts in `scripts/` use `typer`.
2. **`.claude-plugin/plugin.json` `version` must equal `skills/slideops/SKILL.md`'s
   `metadata.version`.** Bumping that version is the only thing that delivers an update to
   installed users; `validate.py` fails if the two disagree.
3. **Theme colors live in exactly one `:root` block per HTML file.** `validate.py` rejects
   any color literal outside it (outside `<pre>`/`<svg>`), because "switch theme" must stay
   a single block replacement.
4. **`assets/template.html` keeps its `<!-- SLIDES START -->` / `<!-- SLIDES END -->`
   markers and `[DECK TITLE]` placeholder**; example decks must contain no leftover
   placeholders, no `.img-placeholder`, and no em dashes in prose.
5. **`examples/skill-demo.html` cites this repository.** It currently quotes
   `skills/slideops/assets/template.html` and `skills/slideops/references/diagrams.md`, so
   editing those lines makes the CI citation step fail. The fix is to re-cite with
   `cite.py`, re-stamp with `cite.py --stamp`, and commit the deck — the same repair loop
   the skill prescribes to users, applied to ourselves.

## Generated artifacts

Regenerate rather than hand-edit; both rot like a slide does:

- `docs/hero.png`, `docs/theme-light.png`, `docs/theme-dark.png` ← `scripts/make_hero.py`
  (renders the demo deck's title slide in both themes, reading the token blocks straight
  from `references/themes.md`). Re-run after editing the title slide or a theme.
- `dist/skill-demo.pdf` ← `scripts/smoke_test.py --pdf-out dist/skill-demo.pdf`. Untracked
  on purpose (6.6 MB); it is attached to the GitHub release, which is where the README
  links.

## Tests

`tests/test_freshness.py` is the load-bearing one: it builds a throwaway git repo, cites a
snippet, then shifts / edits / deletes the code and asserts the status reported. The
project's claim is that a document can prove it still matches the code, so changes to
`check.py`'s status logic belong there first.
