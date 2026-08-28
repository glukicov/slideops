# 🛠️ Developing SlideOps

<sub>[← README](../README.md) · [Install](install.md) · [Freshness](freshness.md) · **Development** · [Changelog](../CHANGELOG.md)</sub>

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](../.pre-commit-config.yaml)

The skills themselves are dependency-free. Everything below is for working *on* this
repository and never ships inside a skill. It builds on Python 3.14, one version with no
matrix, which `uv` fetches for you.

## Setup and the gate

```bash
uv sync --dev                # one-time setup, Python 3.14
uv run pre-commit install    # optional: lint, format, types and tests before each commit

uv run ruff check .          # lint
uv run ruff format .         # format
uv run ty check              # types
uv run pytest                # unit tests + the freshness end-to-end tests
uv run python scripts/validate.py     # frontmatter, template invariants, no stray colours
uv run python scripts/smoke_test.py   # render every slide, export and verify a PDF
uv run python scripts/make_hero.py    # regenerate the README imagery from the demo deck
```

## Generated artifacts

Two things in this repository are built rather than written, and both rot the way a slide
does.

```bash
uv run python scripts/smoke_test.py --pdf-out dist/skill-demo.pdf
```

The demo PDF isn't tracked. It's 6.6 MB, and every `/plugin install` and every background
update would pay for it, so the command above builds it and it gets attached to the GitHub
release instead. The README links `releases/latest/download/skill-demo.pdf`, which stays
valid as long as the asset keeps its filename.

`make_hero.py` renders the demo deck's title slide in both themes, straight from the token
blocks in `references/themes.md` rather than from hard-coded values, and splits them along
the diagonal. Edit the title slide and you have to re-run it. Its label inset comes from the
2:1 crop that LinkedIn and Medium apply to a shared image, so the corner labels survive
being shared.

The rule the skill applies to a deck applies here too: if a file can be regenerated from its
source, it's an artifact, not a source.

## Two guards worth knowing about

CI runs the whole gate on every push and pull request, plus:

- **`tests/test_freshness.py`** builds a throwaway git repository, moves code around, edits
  it and deletes it, then asserts the status the tools report. The claim of this project is
  that a document can prove it still matches the code, so the prover has its own test.
- **The portability job** copies `skills/slideops/` the way a user installs it and runs both
  scripts on bare Python with nothing installed, then does it again through `./install.sh`.
  If either script ever grows a dependency, that job fails and the standard-library-only
  promise breaks before anyone ships it.

## Two rules for the shipped scripts

`skills/slideops/scripts/check.py` and `cite.py` get copied onto other people's machines and
run with whatever `python3` is there, with nothing installed.

1. **Standard library only.** No third-party imports, ever. The dev scripts in `scripts/`
   use `typer` for argument parsing; the shipped ones use `argparse` and always will.
2. **Conservative syntax.** They aren't pinned to an old target any more, but they still run
   under interpreters much older than 3.14, and copy-installs have no step that could fetch
   anything. If that guarantee ever needs enforcing again, ruff's `per-file-target-version`
   does it without a build matrix.

## Releasing

> [!IMPORTANT]
> Bumping `version` in `.claude-plugin/plugin.json` is what delivers an update to installed
> users. `scripts/validate.py` fails the build if it ever disagrees with the skill's own
> `metadata.version`, so the two move together.

One thing that's deliberately *not* a pre-commit hook: the deck freshness check.
Documentation drift is a review-time concern, so it runs on pull requests instead. See
[`skills/slideops/references/automation.md`](../skills/slideops/references/automation.md).
