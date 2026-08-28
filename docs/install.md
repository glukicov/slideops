# 📦 Installing SlideOps

<sub>[← README](../README.md) · **Install** · [Freshness](freshness.md) · [Development](development.md) · [Changelog](../CHANGELOG.md)</sub>

Four ways in, depending on which agent you use and whether you want updates to arrive on
their own. If you're on Claude Code, take the first one.

## Claude Code plugin: the only install that updates itself

```
/plugin marketplace add glukicov/slideops
/plugin install slideops@slideops
```

This repository is its own marketplace, so those two lines are the whole setup. Claude Code
checks for new versions in the background after a session starts and prompts you to run
`/reload-plugins` when one lands.

> [!TIP]
> One thing worth doing once: third-party marketplaces have **auto-update off by default**.
> Turn it on in `/plugin` → **Marketplaces**, or you'll only get new versions when you run
> `/plugin marketplace update slideops` by hand.

## Git checkout you can pull

```bash
git clone https://github.com/glukicov/slideops ~/src/slideops
ln -s ~/src/slideops/skills/slideops      ~/.claude/skills/slideops
ln -s ~/src/slideops/skills/slides-to-pdf ~/.claude/skills/slides-to-pdf
```

Symlinks mean `git pull` updates the installed skill immediately, with no copying.

## Plain copy: a pinned snapshot that never changes under you

```bash
git clone https://github.com/glukicov/slideops
cp -R slideops/skills/* ~/.claude/skills/          # or <your-repo>/.claude/skills/
```

## Codex, Copilot CLI, OpenCode, and anything else that reads `SKILL.md`

```bash
git clone https://github.com/glukicov/slideops && cd slideops
./install.sh                # symlink; --copy for a snapshot, --dry-run to look first
```

Two destinations cover four agents, because `~/.agents/skills` has become a shared
convention:

| Agent | Reads | Marketplace? |
|---|---|---|
| **Claude Code** | `~/.claude/skills`, plus plugins | Yes, use the plugin install above |
| **Codex** | `~/.agents/skills`, repo `.agents/skills` | No skill marketplace; a directory is the install |
| **Copilot CLI** | `~/.agents/skills`, `~/.copilot/skills`, repo `.github/skills` or `.claude/skills` | No |
| **OpenCode** | `~/.agents/skills`, `~/.claude/skills`, `~/.config/opencode/skills` | Plugin registries exist, but skills install by path |

Nothing needs porting between them. SlideOps' frontmatter (`name`, `description`,
`license`, `compatibility`, `metadata`) is the common subset all four accept. No
`allowed-tools` is declared, so each agent applies its own confirmation rules to the shell
commands. And the two Python scripts are standard library only, so there's no build step
and nothing to install anywhere.

## Updating

| Install method | How you get a new version |
|---|---|
| **Plugin** | Automatic. Claude Code refreshes in the background and prompts for `/reload-plugins`. Force it with `/plugin marketplace update slideops` |
| **Clone + symlink** | `cd ~/src/slideops && git pull` |
| **Plain copy** | Re-clone and re-copy. Nothing tells you a new version exists |
| **`./install.sh`** | `git pull` in the clone, or re-run `./install.sh --copy`. Watch releases to hear about one |

Every release is listed in [CHANGELOG.md](../CHANGELOG.md) and tagged. The plugin's
`version` is what gates updates for installed users, so it's bumped on every release and CI
fails if it ever disagrees with the skill's own `metadata.version`.

## Requirements

- **Headless Chrome** for the visual verification pass and PDF export. Any Playwright
  Chromium cache or system Chrome install works; the skill discovers it across macOS and
  Linux, and falls back to `npx playwright install chromium`.
- **`npx` with network access** only if you want Mermaid diagrams (one-time fetch of
  `@mermaid-js/mermaid-cli`). Everything else is offline.
- **Python** to run the shipped scripts. They import only the standard library, so they
  need an interpreter and nothing else. Developing on this repository needs 3.14, which
  `uv sync --dev` fetches for you.

## What gets installed

<details>
<summary><b>The full tree, annotated</b> — two skills, two scripts, six reference files</summary>

<br>

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
└── examples/skill-demo.html # a deck about the skill, built by the skill

skills/slides-to-pdf/        # companion skill, usable standalone
└── SKILL.md                 # any hash-navigated HTML deck → verified page-per-slide PDF
```

</details>

The scripts ship **inside** the skill, so `~/.claude/skills/slideops/scripts/check.py`
exists on any machine that installed it. If a repository owns decks, vendor `check.py` into
its own `tools/` as well. It's a single dependency-free file, and your CI shouldn't depend
on a skill being installed.
