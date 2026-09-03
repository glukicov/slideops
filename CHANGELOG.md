# 📋 Changelog

<sub>[← README](README.md) · [Install](docs/install.md) · [Freshness](docs/freshness.md) · [Development](docs/development.md) · **Changelog**</sub>

## [1.1.2](https://github.com/glukicov/slideops/releases/tag/v1.1.2) - 2026-09-03

A build leaves one file behind: the deck, or the doc.

- **No more companion `README.md`.** Step 6 used to have the agent write or extend a
  shared readme next to the deck, one section per deck in the folder. That sidecar carried
  no citations, so it was the one artifact `check.py` could not keep honest, and it went
  stale the first time a deck was edited. What it held (coverage, slide count, navigation
  keys, how the file is structured for later edits) is now reported in the final message
  instead, and touching an index the repo already keeps is the user's call.
- **Markdown mode says the same thing**, so a cited doc no longer grows an uncited
  neighbour either.
- The intake no longer asks about the output folder's readme conventions, and the Step 4
  cleanup rule now expects nothing but the deck and an optional PDF.

## [1.1.1](https://github.com/glukicov/slideops/releases/tag/v1.1.1) - 2026-08-31

Both PDF exports now number their pages.

- **Markdown doc PDFs** carry a centred `page / total` footer, drawn by a CSS paged-media
  `@page { @bottom-center }` margin box, so the count stays right however Chrome breaks
  the content. The bottom margin widened to `20mm` to make room for it.
- **Deck PDFs** carry the same footer as a translucent pill overlaid on each page, at the
  `bottom: 18px` the deck's own HUD counter vacates during export. Margin boxes are no
  help there: the pages are full-bleed screenshots printed at zero `@page` margin.
- **Both are verified, not assumed.** Each footer is real text, so the render-back pass
  extracts it and fails the export unless every page carries its own number. That is the
  only thing that catches a Chrome too old for margin boxes, which drops the doc footer
  silently and produces a PDF that is otherwise perfect.

## [1.1.0](https://github.com/glukicov/slideops/releases/tag/v1.1.0) - 2026-08-31

Markdown documentation mode: the citation and freshness mechanism now writes docs, not
only decks.

- **Markdown carrier.** A doc carries citations as HTML comments above fenced snippets
  (`<!-- slideops data-src="…" data-sha256="…" -->`) and the build stamp as a comment on
  line 1. Invisible on GitHub, native syntax highlighting, `mermaid` fences render with
  no download.
- **`check.py`** parses `.md` docs (fence-masked, so docs quoting the syntax never
  miscount), attributes citations to the nearest heading, sweeps `.md` and `.html`
  together, and reports `section N` for docs. JSON deck objects gain `"kind"`.
- **`cite.py --md`** prints ready-to-paste comments and language-tagged fenced snippets
  (the fence outgrows backtick runs in the source); `--stamp` on a `.md` writes the line-1
  comment stamp.
- **New skill prose**: `references/markdown.md` (the docs-mode contract),
  `references/markdown-pdf.md` (verified print-paginated PDF export), and
  `assets/template.md`.
- **Worked example**: `examples/skill-demo.md`, cited against this repository and checked
  by CI on both uv and bare Python; the smoke test also prints it to a verified PDF.
- The freshness lifecycle tests now run every drift scenario against both carriers.

## [1.0.1](https://github.com/glukicov/slideops/releases/tag/v1.0.1) - 2026-08-31

- **Fix: strict YAML parsers dropped the `slideops` skill.** The unquoted frontmatter
  description contained a colon-space, a ScannerError in every strict parser, so
  `npx skills add glukicov/slideops` found only `slides-to-pdf`. The description is now
  quoted, `validate.py` strict-parses every SKILL.md frontmatter so this class of bug
  fails the build, and the README gained the skills.sh badge plus the one-line
  `npx skills add glukicov/slideops` install path.

## [1.0.0](https://github.com/glukicov/slideops/releases/tag/v1.0.0) - 2026-08-24

First public release, MIT licensed. Two skills: `slideops` (repository to slide deck) and
`slides-to-pdf` (any hash-navigated HTML deck to a verified PDF).

**Install and updates**
- Ships as a Claude Code plugin, and the repository is its own marketplace:
  `/plugin marketplace add glukicov/slideops` then `/plugin install slideops@slideops`.
  Claude Code then refreshes new versions in the background. Bumping `version` in
  `.claude-plugin/plugin.json` is what delivers an update to installed users, so
  `validate.py` fails the build if it ever disagrees with the skill's `metadata.version`.
- Also installable as a git checkout with symlinks (`git pull` to update) or as a plain
  copy of `skills/*` (a pinned snapshot). See the README's Updating table.
- **Runs on Codex, Copilot CLI and OpenCode too**, which all read `~/.agents/skills`.
  `./install.sh` places both skills where each agent looks, and CI asserts that it does.
  No porting is involved: the frontmatter is the subset all four accept, and the scripts
  are standard library only, so there's nothing to install anywhere. Claude Code is the
  only one of the four with a marketplace, and so the only install that updates itself.
- Skills live under `skills/<name>/SKILL.md`, the layout the plugin system expects.

I built this by having independent agents follow the skill verbatim and file friction
reports, three rounds deep, until a cold run produced a deck with zero failures. Seven
decks went up against a real repository along the way, and the fixes below came out of
those runs rather than out of speculation.

**The workflow**
- Guided intake: the skill scans the repository before asking anything, then proposes
  concrete deck topics with a "why now" for each, alongside audience, length, theme, and
  extras. Existing decks in the output folder reshape the proposals.
- An outline checkpoint before any HTML is written, with explicit conditions for skipping
  it (an outline was already given, or the run is non-interactive).
- The accuracy contract: verbatim snippets, recomputed stats, git-grounded "shipped"
  claims, traced diagrams, and code-wins-over-docs when a repository contradicts itself.
- Verification as a required step: every slide screenshotted and inspected, structural
  balance checked, style rules enforced by grep.

**The template**
- 13 copy-and-fill slide patterns, each documented with when to use it.
- Fully tokenized theming: every color derives from one `:root` block through
  `color-mix()`, so a theme change is a single block replacement.
- Four presets: Ledger Light (default), Ledger Dark, Midnight, Graphite, plus a
  brand-extraction path.
- Esc-toggled overview grid (deep-linkable as `#overview`), speaker notes via
  `<aside class="notes">` and `N`, link-aware click-to-advance, progress bar and counter.
- Grids default to content height, which was the single root cause of every layout bug
  found in early test builds.

**Diagrams and export**
- Mermaid rendered to inline SVG at build time, themed from the deck's own tokens, with a
  decision table for when built-in flow boxes are the better choice.
- `slides-to-pdf`: page-per-slide PDF at 2x, verified by rendering the finished PDF back
  to images (a PDF can have the right page count and silently blank image pages).

**Freshness (the Ops half)**
- Citations: quoted snippets carry `data-src="path:start-end"` and a `data-sha256` of the
  source lines at build time; the deck records its build commit in a meta tag.
- `skills/slideops/scripts/check.py` reports each citation as CURRENT / MOVED / CHANGED /
  MISSING / UNVERIFIED, telling a pure line-number shift apart from a real content
  change. It sweeps whole folders (`check.py docs/slides/`), and it's standard library
  only: no model, no network, no tokens.
- `--suggest` prints the diff, the commits responsible, the corrected citation and the
  current source ready to paste. `--json` emits a full repair brief for an agent.
  `--quiet` stays silent when nothing drifted; `--exit-zero` makes a report-only CI job.
- `skills/slideops/scripts/cite.py` writes citation attributes and stamps the build commit from
  real HEAD and date, so no hash is ever computed by hand.
- Both scripts ship **inside** the skill, so they exist wherever the skill is installed.
- A first-class refresh workflow in SKILL.md: triage by status and repair only the slides
  that drifted, rather than regenerating the deck.
- `references/freshness.md` documents the mechanism and `references/automation.md` the
  wiring (pull-request checks, scheduled refreshes, advisory hooks, and which decks
  deserve automation at all). CI checks the example deck's own citations on every push.

**Safety**
- A confidentiality rule in the always-loaded part of the skill: default exclusions for
  secrets, credentials, production logs, and customer data; redaction of tokens, private
  hosts, and personal data from anything quoted; ask-before-including for judgement calls;
  and a redaction scan over the finished HTML, PDF, notes, and embedded images.
- The intake asks who will see the deck, so the redaction bar matches the audience.
- Chrome keeps its sandbox: no `--no-sandbox` anywhere by default, with a documented
  fallback for containers that can't grant user namespaces.
- Pinned, optional downloads: `mermaid-cli` is version-pinned and skipped when already
  installed, and the PDF verifier reuses an existing `pypdfium2` before creating a venv.

**Tooling** (development only, never shipped inside a skill)
- `uv`-managed toolchain in `pyproject.toml`: `ruff` (lint + format), `ty` (types),
  `pytest`, and `pre-commit` hooks that run all of it before a commit.
- `tests/` covers the citation parser, the status classification, the JSON repair brief,
  and an end-to-end suite that builds a throwaway git repository, moves code, edits it and
  deletes it, then asserts the status the tools report.
- `scripts/validate.py` and `scripts/smoke_test.py` for skill structure and the render/PDF
  pipeline. `smoke_test.py --pdf-out PATH` keeps the verified PDF, which is how the demo
  PDF is built for the release: it's an artifact of the deck, so it's attached to each
  release instead of tracked here, and a `/plugin install` doesn't download 6.6 MB it can
  regenerate.
- CI also installs the skill the way a user does, both by hand and through
  `install.sh`, and runs both scripts on bare Python, so the standard-library-only promise
  can't quietly break.
- Python 3.14, a single version with no build matrix, for the repository and every CI job.
- `compatibility:` frontmatter on both skills; no `allowed-tools`, deliberately.

**Cross-platform**
- Chrome discovery searches macOS and Linux Playwright caches and system installs, then
  falls back to installing Chromium.
- Per-deck staging directories, so parallel deck builds never collide.
