# Markdown documentation support (v1.1.0)

Date: 2026-08-31. Branch: `feature/markdown`.

## Problem

SlideOps proves a *slide deck* still matches the code it quotes. Users also want plain
Markdown documentation with the same guarantee: generated from the real repository, with
images and Mermaid diagrams, and carrying per-snippet hashes so a later check can point at
exactly the sections that drifted and an agent can regenerate only those parts.

## Decisions (confirmed with Gleb, 2026-08-31)

1. **Extend the existing `slideops` skill** rather than shipping a third skill. One
   citation engine, one install; the shipped scripts learn `.md` alongside `.html`.
2. **Citations are HTML comments above fenced code blocks.** Invisible on GitHub, native
   syntax highlighting, Mermaid fences render without any download.
3. Release as **1.1.0** (`SKILL.md` `metadata.version` and `.claude-plugin/plugin.json`
   bumped together, per the validate.py invariant).

## The Markdown carrier format

A generated doc is a single self-contained `.md` file. The two facts that make it
checkable are carried as comments, everything else is ordinary Markdown:

```markdown
<!-- slideops-build commit=a8bde99 date=2026-08-31 repo=my-service -->
# Service architecture

## The request path

<!-- slideops data-src="app/main.py:40-58" data-sha256="a1b2c3d4e5f6" -->
```python
def main() -> int:
    ...
```
```

- The build stamp is the first line of the file; same `key=value` payload as the HTML
  `<meta>`.
- Each citation comment sits directly above the fence it vouches for. `data-src` and
  `data-sha256` have exactly the meaning they have in decks (repo-relative path,
  optional 1-indexed inclusive range, first 12 hex chars of SHA-256 over the source
  lines joined with `\n`). Hash the source, never the possibly-trimmed snippet.
- Citations attach to the nearest preceding Markdown heading, the way deck citations
  attach to the nearest `<!-- N: LABEL -->` slide comment. Reports and the JSON repair
  brief name the section, so a repair touches only that section.
- Anything inside a code fence is masked before scanning: a doc that *teaches* this
  syntax (like the skill's own references) never miscounts its examples as citations.

## Changes by component

### `skills/slideops/scripts/check.py` (shipped, stdlib only)

- `MD_CITATION_RE` for the comment form; `BUILD_META_RE` gains the comment alternative.
- `.md`/`.markdown` files route through a fence-masking scanner that collects headings
  (position, ordinal, text) and citation comments; the existing HTML path is untouched.
- `collect_decks` sweeps `*.md` next to `*.html`, still filtered by "carries a build
  stamp or a citation", so companion READMEs are skipped.
- Human-readable output says `section` for docs and `slide` for decks; the JSON payload
  keeps its existing keys.

### `skills/slideops/scripts/cite.py` (shipped, stdlib only)

- `--md` prints the full ready-to-paste comment instead of bare attributes; with
  `--snippet` it prints a fenced block: language inferred from the file extension, no
  HTML escaping, fence grown longer than any backtick run in the content.
- Slide width warnings (65/95 columns) are suppressed under `--md`; GitHub scrolls.
- `--stamp` detects a `.md` target and inserts/updates the comment stamp at the top of
  the file instead of a `<head>` meta.

### Skill prose

- `assets/template.md`: lightweight skeleton with a `[DOC TITLE]` placeholder, section
  patterns, a Mermaid fence and a worked citation example.
- `references/markdown.md`: the docs-mode contract (intake differences, build loop,
  verification, shipping, the refresh workflow in section terms).
- `references/freshness.md`: gains the Markdown carrier syntax next to the HTML one.
- `SKILL.md`: routes "markdown docs" requests to the new reference, adds triggers to the
  description, bumps `metadata.version` to 1.1.0.

### Development harness (free to use third-party deps)

- `scripts/validate.py`: validates `template.md` (placeholder present) and example
  `.md` files: no unfilled placeholders, balanced fences, no em dashes in prose,
  well-formed `slideops` comments.
- `.github/workflows/ci.yml`: both citation-check steps (uv job and bare-python3
  portability job) also check `examples/skill-demo.md`.
- Tests:
  - `tests/test_cite.py`: `--md` output, fenced `--snippet`, fence growth, `.md` stamp
    insert and update.
  - `tests/test_check.py`: md citation/build-meta parsing, heading attribution, fence
    masking, `.md` directory sweep.
  - `tests/test_freshness.py`: the full Markdown lifecycle against a throwaway git repo:
    fresh doc CURRENT, shifted lines MOVED with the new range, edited lines CHANGED with
    diff and commits, deleted file MISSING, no-hash UNVERIFIED, suggested fix restores
    CURRENT, and the shipped example doc matches this repository.

### Example and release

- `skills/slideops/examples/skill-demo.md`: a real generated doc about this repository,
  built by following `references/markdown.md`, citing real lines, stamped, with one
  Mermaid diagram and one image.
- `.claude-plugin/plugin.json` and `marketplace.json`: version 1.1.0, descriptions
  mention Markdown docs.
- `README.md`: short section introducing the Markdown mode.

## PDF export (added 2026-08-31, on Gleb's request)

Markdown docs mirror the full deck path, PDF included. Unlike slides-to-pdf there are no
per-slide screenshots: the recipe in `references/markdown-pdf.md` converts the `.md` to
HTML (GFM converter, one npx download at most), rewrites relative image paths to
absolute `file://` ones, pre-renders `mermaid` fences to SVG per diagrams.md, wraps the
body in print CSS, prints with headless Chrome's native pagination, and verifies by
rendering the PDF back to images with pypdfium2 (headless Chrome cannot rasterize a
local PDF). `scripts/smoke_test.py` proves the wrap-print-verify pipeline in CI against
the example doc.

## Out of scope

- DOCX export (the `.md` and its PDF are the artifacts).
- Multi-file doc sites; one request produces one file, like one deck.
- Changing the HTML deck pipeline in any behavioural way.

## Testing strategy

TDD throughout: each script change lands as a failing test first. The load-bearing test
is the Markdown lifecycle in `test_freshness.py`, because the project's claim is that a
document can prove it still matches the code; the example doc plus the CI citation step
then applies that claim to this repository itself, the same way the demo deck does.
