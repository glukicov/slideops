# SlideOps

[![CI](https://github.com/glukicov/slideops/actions/workflows/ci.yml/badge.svg)](https://github.com/glukicov/slideops/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/glukicov/slideops?color=7a7f1f)](https://github.com/glukicov/slideops/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue)](pyproject.toml)
[![Zero dependencies](https://img.shields.io/badge/dependencies-none-success)](.github/workflows/ci.yml)
[![Agent Skill](https://img.shields.io/badge/Claude%20Code-Agent%20Skill-D97757)](https://agentskills.io/specification)

**Generate a deck from your code in minutes. Find out in milliseconds when it stops being
true. Then rebuild only the slides that drifted.**

![The same slide rendered in Ledger Light and Ledger Dark, split diagonally](docs/hero.png)

*The demo deck is 17 slides about SlideOps, built by SlideOps: open the
[HTML](skills/slideops/examples/skill-demo.html) or the
[PDF](https://github.com/glukicov/slideops/releases/latest/download/skill-demo.pdf).*

Writing documentation isn't the bottleneck any more. Keeping it true is. The deck that said
we run two database migrations still says two, a year after we started running ten 😅.

SlideOps is a pair of [Agent Skills](https://agentskills.io/specification) for Claude Code
and compatible coding agents. It treats a generated document the way you'd treat generated
code: it's built from a source, and it records which source it came from.

![The demo deck's overview grid](docs/overview.png)

*Press Esc in any deck for the overview grid.*

## Install

**Claude Code.** This repo is its own marketplace, so two lines are the whole setup, and
it's the only install that keeps itself up to date:

```
/plugin marketplace add glukicov/slideops
/plugin install slideops@slideops
```

**Codex, Copilot CLI, OpenCode**, or a plain checkout:

```bash
git clone https://github.com/glukicov/slideops && cd slideops
./install.sh
```

All four agents read `SKILL.md` and nothing needs porting between them. For the symlink and
snapshot installs, the per-agent table and how updates reach you, see
**[docs/install.md](docs/install.md)**.

## Use

Open a repository and say:

> make slides about this repo

SlideOps scans the repo first, then asks one compact set of questions: which topic (it
proposes concrete candidates it found, each with a "why now"), audience, length, theme and
extras. You get an outline to approve before it writes any HTML.

If you already know what you want, skip the intake:

> deep dive on the auth subsystem, Ledger Dark theme, 15 slides, with a PDF

Months later, in the same repository:

> is the architecture deck still accurate?

The agent sweeps the deck folder and triages by status. It re-quotes whatever merely moved,
and flags the slides whose *claim* might no longer hold. It repairs what drifted instead of
regenerating the deck, so the pacing and narrative you signed off on the first time survive.

## Features

- **Freshness checking.** `scripts/check.py` sweeps a whole `docs/slides/` folder and
  reports which slides cite code that has changed, moved or vanished since the deck was
  built, then suggests the fix or hands an agent a JSON repair brief. No model, no network,
  no tokens: standard library Python, and it runs in milliseconds.
- **One self-contained file per deck.** No build step, no CDN, works offline, attaches to
  an email.
- **Navigation:** arrow keys, click-to-advance, URL hash deep links, an Esc-toggled
  overview grid, and speaker notes on `N` (never visible in screenshots or exports).
- **13 slide patterns:** title, agenda, section divider, prose + cards, reference table,
  before/after code, annotated snippet (half and full width), flow diagram, lane
  comparison, image + caption, chat bubbles, closing.
- **4 themes, one block each.** Every color derives from a single `:root` token block via
  `color-mix()`, so switching theme is one replacement: **Ledger Light** (default),
  **Ledger Dark**, **Midnight**, **Graphite**. Or point it at a brand's real CSS values and
  map those onto the token roles.

  | Ledger Light (default) | Ledger Dark |
  |---|---|
  | ![Ledger Light](docs/theme-light.png) | ![Ledger Dark](docs/theme-dark.png) |

  *Same deck, same markup, same content.*

- **Mermaid diagrams** pre-rendered to inline SVG at build time and themed from the deck's
  own tokens, so the deck stays dependency-free.
- **Verified PDF export.** The companion skill renders the finished PDF back to images and
  checks the pages, because a PDF can have the right page count and still hand you blank
  images.

## Documentation

| | |
|---|---|
| [docs/install.md](docs/install.md) | Every install path, all four agents, updating, requirements, what gets installed |
| [docs/freshness.md](docs/freshness.md) | Citations, the status table, the cost model, where to automate, the accuracy contract, what never reaches a slide |
| [docs/development.md](docs/development.md) | Working on this repository: the gate, CI guards, generated artifacts, releasing |
| [CHANGELOG.md](CHANGELOG.md) | What changed in each release |

Inside the skill, `skills/slideops/references/` holds the specifications the agent reads:
freshness, automation, style, themes, diagrams and verification.

## Credits

Prior art worth knowing: [frontend-slides](https://github.com/zarazhangrui/frontend-slides)
for visual-first theme selection, and
[presentation-skills](https://github.com/ktundwal/presentation-skills) for pioneering the
render-then-look visual QA loop that SlideOps also relies on. What SlideOps adds is the
*Ops* half: content grounded in a repository, and a cheap way to ask later whether it still
holds.

## Licence

MIT. See [LICENSE](LICENSE). Use it, fork it, ship it commercially; attribution is the only
condition. The decks you generate are your own content either way.
