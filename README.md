# SlideOps

[![CI](https://github.com/glukicov/slideops/actions/workflows/ci.yml/badge.svg)](https://github.com/glukicov/slideops/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/glukicov/slideops?color=7a7f1f)](https://github.com/glukicov/slideops/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue)](pyproject.toml)
[![Zero dependencies](https://img.shields.io/badge/dependencies-none-success)](.github/workflows/ci.yml)
[![Agent Skill](https://img.shields.io/badge/Claude%20Code-Agent%20Skill-D97757)](https://agentskills.io/specification)

**Generate a deck from your code once. Then find out, in milliseconds, the day it stops
being true.**

Documentation is not hard to write any more. It is hard to *keep*. The deck that said we
run two database migrations still says two, a year after we started running ten, and the
only way anyone finds out is in front of an audience.

SlideOps is a pair of [Agent Skills](https://agentskills.io/specification) for Claude Code
and compatible coding agents that treats a generated document the way you treat generated
code: it is built from a source, it records what source it came from, and there is a
command that tells you when the two have diverged.

```console
$ python3 check.py docs/slides/ --repo .
  slide   7  PIPELINE     backend/app/main.py:40-58        CURRENT
  slide  12  MIGRATIONS   backend/alembic/env.py:18-31     MOVED      same content, now at lines 22-35
  slide  15  RATE-LIMIT   backend/app/middleware/rate.py   CHANGED    4 line(s) differ

1 current, 2 stale, 3 cited in total.
```

No model, no network, no tokens: standard library Python, and it runs in milliseconds.
Tokens are spent only when you decide to *repair* something, and only on the slides that
actually drifted.

![The same slide rendered in Ledger Light and Ledger Dark, split diagonally](docs/hero.png)

*One slide, one file, two themes. The split is not a mock-up: it is the same title slide
rendered twice, because switching theme means replacing a single `:root` block. The demo
deck (`skills/slideops/examples/skill-demo.html`) is a 17-slide deck about SlideOps, built by
SlideOps. Open the HTML, or read the
[PDF](https://github.com/glukicov/slideops/releases/latest/download/skill-demo.pdf), which
is attached to each release rather than tracked here: it is a build artifact, so the repo
you install stays small.*

![The demo deck's overview grid](docs/overview.png)

*Press Esc in any deck for the overview grid.*

## The accuracy contract

This is the part that makes a generated deck safe to present:

| Always | Never |
|---|---|
| Code snippets copied verbatim from real files, then HTML-escaped | Fabricate a chart or invent numbers for a caption |
| Aggregate stats recomputed from the raw data | Reword a quoted line to make it fit the slide |
| "Shipped" claims grounded in actual commits via `git log` | Checkmark planned work as if it shipped |
| Diagrams traced through real imports and call sites | Trust a doc the code contradicts |

When a repository's own docs contradict its code, the code wins and the drift becomes a
note on the slide.

## Install

**As a Claude Code plugin (recommended, and the only install that updates itself):**

```
/plugin marketplace add glukicov/slideops
/plugin install slideops@slideops
```

This repo is its own marketplace, so those two lines are the whole setup. Claude Code
checks for new versions in the background after a session starts and prompts you to run
`/reload-plugins` when one lands. See [Updating](#updating).

**As a git checkout you can pull:**

```bash
git clone https://github.com/glukicov/slideops ~/src/slideops
ln -s ~/src/slideops/skills/slideops      ~/.claude/skills/slideops
ln -s ~/src/slideops/skills/slides-to-pdf ~/.claude/skills/slides-to-pdf
```

Symlinks mean `git pull` updates the installed skill immediately, with no copying.

**As a plain copy (a pinned snapshot that never changes under you):**

```bash
git clone https://github.com/glukicov/slideops
cp -R slideops/skills/* ~/.claude/skills/          # or <your-repo>/.claude/skills/
```

**For Codex, Copilot CLI, OpenCode and anything else that reads `SKILL.md`:**

```bash
git clone https://github.com/glukicov/slideops && cd slideops
./install.sh                # symlink; --copy for a snapshot, --dry-run to look first
```

Two destinations cover four agents, because `~/.agents/skills` has become a shared
convention:

| Agent | Reads | Marketplace? |
|---|---|---|
| **Claude Code** | `~/.claude/skills`, plus plugins | Yes — use the plugin install above |
| **Codex** | `~/.agents/skills`, repo `.agents/skills` | No skill marketplace; a directory is the install |
| **Copilot CLI** | `~/.agents/skills`, `~/.copilot/skills`, repo `.github/skills` or `.claude/skills` | No |
| **OpenCode** | `~/.agents/skills`, `~/.claude/skills`, `~/.config/opencode/skills` | Plugin registries exist, but skills install by path |

Claude Code is the only one of the four with a marketplace for this, which is why it is the
only install that updates itself. Everywhere else, `git pull` in the clone updates a
symlinked install immediately, and re-running `./install.sh --copy` updates a copied one.

Nothing needs porting between them. SlideOps' frontmatter (`name`, `description`,
`license`, `compatibility`, `metadata`) is the common subset all four accept, no
`allowed-tools` is declared, so each agent applies its own confirmation rules to the shell
commands, and the two Python scripts are standard library only — there is no build step and
no dependency to install anywhere.

## Updating

| Install method | How you get a new version |
|---|---|
| **Plugin** | Automatic. Claude Code refreshes in the background and prompts for `/reload-plugins`. Force it with `/plugin marketplace update slideops`. Auto-update is off by default for third-party marketplaces, so turn it on once in `/plugin` → **Marketplaces** |
| **Clone + symlink** | `cd ~/src/slideops && git pull` |
| **Plain copy** | Re-clone and re-copy. Nothing tells you a new version exists |
| **`./install.sh`** | `git pull` in the clone, or re-run `./install.sh --copy`. Watch releases to hear about one |

Every release is listed in [CHANGELOG.md](CHANGELOG.md) and tagged. The plugin's `version`
is what gates updates for installed users, so it is bumped on every release and CI fails if
it ever disagrees with the skill's own `metadata.version`.

## Use

Open a repository and say:

> make slides about this repo

SlideOps scans the repo first, then asks one compact set of questions: which topic (it
proposes concrete candidates it found, each with a "why now"), audience, length, theme,
and extras. It shows you an outline before writing any HTML.

Or skip the intake by being specific:

> deep dive on the auth subsystem, Ledger Dark theme, 15 slides, with a PDF

Months later, in the same repository:

> is the architecture deck still accurate?

The agent sweeps the deck folder, and if anything drifted it triages by status: re-quote
what merely moved, and flag for you the slides whose *claim* may no longer hold. It repairs
what drifted rather than regenerating the deck, so the pacing and narrative you reviewed
the first time survive.

## What ships

```
.claude-plugin/
├── plugin.json              # name + version: bumping version is what ships an update
└── marketplace.json         # this repo is its own marketplace

skills/slideops/             # the main skill
├── SKILL.md                 # build: orient → intake → research → cite → verify
│                            # sync:  check → triage → repair only what drifted
├── assets/template.html     # 13 slide patterns, navigation, the theme block
├── scripts/
│   ├── check.py             # which slides no longer match the code (stdlib only)
│   └── cite.py              # write a citation, stamp the build commit
├── references/
│   ├── freshness.md         # the citation mechanism and the status table
│   ├── automation.md        # PR checks, scheduled refreshes, advisory agent hooks
│   ├── style-guide.md       # writing rules and the grep checks that enforce them
│   ├── themes.md            # 4 theme presets, font stacks, brand extraction
│   ├── diagrams.md          # Mermaid → inline SVG, and when to use flow boxes instead
│   └── verification.md      # cross-platform Chrome discovery, screenshot loop
└── examples/skill-demo.html # a deck about the skill, built by the skill (+ PDF)

skills/slides-to-pdf/        # companion skill, usable standalone
└── SKILL.md                 # any hash-navigated HTML deck → verified page-per-slide PDF
```

The scripts ship **inside** the skill, so `~/.claude/skills/slideops/scripts/check.py`
exists on any machine that installed it. A repository that owns decks should vendor
`check.py` into its own `tools/` as well: it is a single dependency-free file, and the
repo's CI should not depend on a skill being installed.

## Features

- **Freshness checking.** `scripts/check.py` sweeps a whole `docs/slides/` folder and
  reports which slides cite code that has changed, moved, or vanished since the deck was
  built, then suggests the fix or hands an agent a JSON repair brief.
- **One self-contained file per deck.** No build step, no CDN, works offline, attaches to
  an email.
- **Navigation:** arrow keys, click-to-advance, URL hash deep links, an Esc-toggled
  overview grid, and speaker notes on `N` (never visible in screenshots or exports).
- **13 slide patterns:** title, agenda, section divider, prose + cards, reference table,
  before/after code, annotated snippet (half and full width), flow diagram, lane
  comparison, image + caption, chat bubbles, closing.
- **4 themes, one block each.** Every color derives from a single `:root` token block via
  `color-mix()`, so switching theme is one replacement: **Ledger Light** (default),
  **Ledger Dark**, **Midnight**, **Graphite** — or extract a brand's real CSS values and
  map them onto the token roles.

  | Ledger Light (default) | Ledger Dark |
  |---|---|
  | ![Ledger Light](docs/theme-light.png) | ![Ledger Dark](docs/theme-dark.png) |

  Same deck, same markup, same content. Only the token block changed.
- **Mermaid diagrams** pre-rendered to inline SVG at build time and themed from the deck's
  own tokens, so the deck stays dependency-free.
- **Verified PDF export.** The companion skill renders the finished PDF back to images and
  checks the pages, because a PDF can have the right page count and silently blank images.

## The Ops half: build once, stay in sync

Every quoted snippet records where it came from and what that source looked like at build
time, and the deck records the commit it was built from:

```html
<pre class="code" data-src="backend/app/main.py:40-58" data-sha256="a1b2c3d4e5f6">…</pre>
```

That one attribute pair is what turns a document into something maintainable instead of
something you rewrite. Two commands use it, and they cost very different things:

| | Command | Cost |
|---|---|---|
| **Detect** | `check.py docs/slides/ --repo .` | Standard library only. No model, no network, **no tokens** |
| **Repair** | hand `check.py --json` to your agent | Tokens, scoped to the slides that drifted |

`check` distinguishes **MOVED** (code shifted down thirty lines: update two attributes,
leave the prose alone) from **CHANGED** (the logic is different: a human decides whether
the claim survives). `--suggest` prints the diff, the commits responsible, and the
corrected citation. `--json` is a complete repair brief an agent can act on without
re-reading the repository.

```console
$ python3 skills/slideops/scripts/cite.py app/main.py:40-58 --repo .
data-src="app/main.py:40-58" data-sha256="a1b2c3d4e5f6"
```

`cite.py` writes those attributes and stamps the build commit, so no hash is ever computed
by hand. A wrong hash is worse than a missing one: it surfaces months later as CHANGED and
nobody can tell whether the code moved or the build was sloppy.

### Automate the detection, not the repair

The exit code is 1 when anything is stale and `--exit-zero` forces a report-only run, so
the natural home is a pull request to `main`:

```yaml
- name: Are the decks still true?
  run: python3 tools/slideops-check.py docs/slides/ --repo . --suggest --exit-zero
       | tee -a "$GITHUB_STEP_SUMMARY"
```

Deliberately **not** a blocking pre-commit hook. Code moves fast, and a docs check on the
fast path just teaches everyone to pass `--no-verify`. Drift is a review-time concern.
Pull-request checks, scheduled refreshes, advisory agent hooks, and the rule for which
decks deserve automation at all (a sprint update is *supposed* to freeze) are in
[`skills/slideops/references/automation.md`](skills/slideops/references/automation.md).

That is the *Ops* half: not "AI made slides", but a document that can prove it is current
and tell you precisely where it is not.

## What it will not put on a slide

Decks leave the repository, so SlideOps treats everything on a slide as public. It refuses
to read secrets, keys, credentials files, production logs, or real customer data for slide
content; it redacts tokens, private hostnames, and personal data out of anything it does
quote; it asks before including a detail that looks sensitive; and the verification pass
ends with a redaction scan over the HTML, the PDF, the speaker notes, and every embedded
image. The intake asks who will see the deck, because an internal standup and a conference
talk are different bars.

Chrome runs **with its sandbox on** throughout; nothing in the skills passes
`--no-sandbox`. Downloads are pinned and optional: Mermaid is opt-in, the PDF verifier
reuses an existing install when there is one, and neither is required to build a deck.

## Development

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](.pre-commit-config.yaml)

The skills themselves are dependency-free. The tooling below is for working *on* this
repository and never ships inside a skill. It builds on Python 3.14 — one version, no
matrix — which `uv` fetches for you.

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

uv run python scripts/smoke_test.py --pdf-out dist/skill-demo.pdf   # the release asset
```

The demo PDF is not tracked. It is 6.6 MB, and every `/plugin install` would pay for it on
every update, so it is built by the command above and attached to the release instead. The
same rule the skill applies to a deck applies here: a file that can be regenerated from the
source is an artifact, not a source.

`make_hero.py` renders the demo deck's title slide in both themes, straight from the token
blocks in `references/themes.md`, and splits them along the diagonal. The hero is a
generated artifact of the deck, so it goes stale exactly like a slide does: edit the title
slide and re-run it.

CI runs all of it on every push and pull request, plus two guards worth knowing about:

- **`tests/test_freshness.py`** builds a throwaway git repository, moves code around, edits
  it and deletes it, and asserts the status the tools report. The claim here is that a
  document can prove it still matches the code, so the prover has its own test.
- **The portability job** copies `skills/slideops/` the way a user installs it and runs both
  scripts on bare Python with nothing installed, then does it again through `./install.sh`.
  If either script ever grows a dependency, that job fails and the promise that the skills
  are standard library only is broken before anyone ships it.
Note what is deliberately *not* a pre-commit hook: the deck freshness check. Documentation
drift is a review-time concern, so it runs on pull requests instead. See
[`skills/slideops/references/automation.md`](skills/slideops/references/automation.md).

## Requirements

- **Headless Chrome** for the visual verification pass and PDF export. Any Playwright
  Chromium cache or system Chrome install works; the skill discovers it across macOS and
  Linux, and falls back to `npx playwright install chromium`.
- **`npx` with network access** only if you want Mermaid diagrams (one-time fetch of
  `@mermaid-js/mermaid-cli`). Everything else is offline.
- **Python 3.14**, which `uv sync --dev` installs. The shipped scripts import only the
  standard library, so they need an interpreter and nothing else.

## Credits

Prior art worth knowing: [frontend-slides](https://github.com/zarazhangrui/frontend-slides)
for visual-first theme selection, and
[presentation-skills](https://github.com/ktundwal/presentation-skills) for pioneering the
render-then-look visual QA loop that SlideOps also relies on. SlideOps' distinct
contribution is the *Ops* half: content grounded in a repository, verified claim by claim.

## Licence

MIT. See [LICENSE](LICENSE). Use it, fork it, ship it commercially; attribution is the
only condition. The decks you generate are your own content either way.
