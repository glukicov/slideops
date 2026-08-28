# Contributing

Issues and pull requests are welcome. If it is a question rather than a defect, the
[Discussions tab](https://github.com/glukicov/slideops/discussions) is the better door:
it keeps the issue count meaning what it looks like it means.

## Setup and the gate

[`docs/development.md`](docs/development.md) is the real document. The short version:

```bash
uv sync --dev                # Python 3.14, which uv fetches for you
uv run pre-commit install    # runs the gate below before each commit

uv run ruff check . && uv run ruff format --check .
uv run ty check
uv run pytest
uv run python scripts/validate.py
uv run python scripts/smoke_test.py     # needs Chrome; renders every slide and verifies a PDF
```

CI runs all of it on every pull request, on a single Python version with no matrix.

## Three things that are easy to break by accident

1. **The shipped scripts import the standard library and nothing else.**
   `skills/slideops/scripts/check.py` and `cite.py` get copied onto other people's
   machines and run with whatever `python3` is there, with nothing installed. The dev
   scripts under `scripts/` may use `typer` and friends; the shipped two use `argparse`
   and always will. CI has a job that runs them on bare Python so this cannot quietly
   change.

2. **The demo PDF stays out of the tree.** It is 6.6 MB, it can be rebuilt from the deck,
   and a plugin is downloaded on install and on every update. Build it with
   `uv run python scripts/smoke_test.py --pdf-out dist/skill-demo.pdf` and attach it to the
   release instead. If a pull request adds it back, that is the thing to flag.

3. **Two versions move together.** `.claude-plugin/plugin.json` and the skill's own
   `metadata.version` in `SKILL.md`. Bumping `plugin.json` is what actually delivers an
   update to installed users, and `scripts/validate.py` fails the build if the two
   disagree.

## Style

`skills/slideops/references/style-guide.md` is the writing standard the skill enforces on
generated decks, and this repository follows it too. The rule people trip over first: no em
dashes in prose. Replace them contextually rather than with a single substitute character.

## Pull requests

`main` requires a pull request and three green checks. Squash is the only merge button, so
one pull request becomes one commit on `main`, which is what makes the changelog writable
from the log.
