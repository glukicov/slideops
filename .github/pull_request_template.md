## What this changes, and why

<!-- The why matters more than the what: the diff already says what. -->

## How you know it works

<!--
The gate, or the part of it that touches this change:

    uv run ruff check . && uv run ruff format --check .
    uv run ty check
    uv run pytest
    uv run python scripts/validate.py
    uv run python scripts/smoke_test.py   # anything touching the template, themes or export

CI runs all of it anyway. This box is for what CI cannot see: what you looked at, on which
deck, and what convinced you.
-->

## Checks that are easy to miss

<!-- Delete the lines that do not apply. -->

- [ ] No new import in `skills/slideops/scripts/`. Those two files run on a stranger's bare
      `python3` with nothing installed, and CI has a job that proves it.
- [ ] `dist/skill-demo.pdf` is not in the diff. It is a release asset, not a tracked file,
      and a plugin pays to download the tree on every update.
- [ ] If this ships a change to users: `.claude-plugin/plugin.json` and the skill's
      `metadata.version` bumped together, and a CHANGELOG entry.
- [ ] If the deck or the template changed: the demo deck re-rendered, and
      `scripts/make_hero.py` re-run if the title slide moved.
- [ ] No em dashes in prose. `skills/slideops/references/style-guide.md` has the
      replacements.
