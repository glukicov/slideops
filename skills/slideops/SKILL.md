---
name: slideops
description: 'Use when the user asks for slides, a slide deck, or a presentation about a code repository, one of its subsystems, a feature, an architecture area, or its recent changes. Triggers include "make slides", "build a slide deck", "create a presentation", "HTML slides for this repo", "overview deck", "team update slides", "slides for our latest changes", or naming a topic and asking for a deck about it. Also use when the user asks whether an existing deck still matches the code, or wants one rechecked, refreshed, or kept in sync automatically: "is this deck still accurate", "check the slides against the code", "did anything we documented change", "refresh the architecture deck", "these docs are stale", "fail the build when the deck stops matching the code", or asks to wire that check into CI, a pull request, or an agent hook.'
license: MIT
compatibility: Needs a headless Chrome or Chromium binary (Playwright cache or system install) and Python 3 for the verification pass. Reads the target repository with git. Network access only if you opt into Mermaid diagrams (one npx download) or brand-colour extraction; everything else works offline.
metadata:
  author: Gleb Lukicov
  version: 1.0.1
---

# SlideOps: generate a deck from a repository, and keep it true

This skill has two jobs, and the second one is the point.

**Build**: turn a repository into a deck whose every claim came from the code, not from a
model's impression of the code. **Keep in sync**: make that deck able to prove, months
later, whether it still matches the repository, cheaply enough that nobody has to
remember to care.

The mechanism joining them is a citation. Every quoted snippet records the file, the line
range, and a hash of those source lines at build time, and the deck records the commit it
was built from. That turns "is this deck still accurate?" from a question somebody has to
answer by reading into a command that answers itself:

```bash
python3 scripts/check.py docs/slides/ --repo .
```

Standard library only. No model, no network, no tokens, milliseconds to run. Two scripts
ship with this skill and do all of it: [`scripts/cite.py`](scripts/cite.py) writes the
citations while you build, and [`scripts/check.py`](scripts/check.py) reads them back
afterwards. Writing the citations as you go (Step 3) is therefore not optional decoration:
it is the entire reason the deck can be maintained instead of rewritten. See
[`references/freshness.md`](references/freshness.md) for the mechanism and
[`references/automation.md`](references/automation.md) for wiring it into pull requests,
scheduled refreshes, and agent hooks.

## Which job is this?

- The user wants a **new deck**: start at Step 0 below.
- The user is asking whether an existing deck is **still accurate**, wants one
  **refreshed**, or wants the check **automated**: go straight to
  [Refreshing an existing deck](#refreshing-an-existing-deck) near the end. Do not rebuild
  a deck from scratch because a few slides drifted.

---

Produces a single self-contained HTML slide deck (no build step, no CDN dependencies):
one 1280×720 slide per screen, click/arrow-key/URL-hash navigation, a progress bar and
slide counter, an Esc-toggled overview grid (deep-linkable as `#overview`), optional
per-slide speaker notes (`<aside class="notes">`, toggled with N, invisible in exports),
and, on request, a paginated PDF export. Every slide is grounded in the real repository:
real code snippets, real commands, real screenshots, real numbers. Nothing is invented
to fill space.

A worked example ships with the skill: [`examples/skill-demo.html`](examples/skill-demo.html)
is a 17-slide deck about this skill, built by this skill, showing the patterns, all four
theme presets on real decks, and an inlined Mermaid diagram.

Two starting points, chosen with the user up front:

- **General overview**: what the project is, how to install/set it up, how to run it,
  its main features, its architecture at a glance. Mirrors a README/onboarding walkthrough.
- **Focused topic**: one subsystem, one recent change, one architecture decision, one
  workflow. Goes deep rather than wide.

---

## Step 0: Orient, then ask

Spend ~2 minutes scanning the repo **before asking anything**, so every question you ask
is concrete and every option you offer actually exists: read the README and the
manifest(s) that define the product (per-app in a monorepo), run `git log --oneline -15`
and glance at the top-level tree and `docs/`, and check whether `docs/slides/` already has
decks (its `README.md` shows the local conventions). Do not start slide research yet; this
pass is only to ask good questions. The scan itself may hit stale doc pointers; note them
and move on (Step 1's code-wins rule deals with drift later).

What you find shapes the candidates:

- **Existing decks remove or reframe candidates.** A topic an existing deck already covers
  is off the proposal list, unless meaningful commits have landed since that deck's date,
  in which case offer "update the existing X deck" as its own candidate. Disclose the
  existing decks in one line at the top of the intake.
- **Skip meta noise in "why now".** Recent commits about tooling, docs, or slide decks
  themselves don't justify a deck; reach back to the most recent *product* activity, and
  don't re-justify a candidate with work an existing deck already presents.

Then ask everything in **one compact intake** (use your environment's structured-question
tool if it has one; otherwise a single message with lettered options). Mark the default
in each list, skip any item the user already answered, and never exceed these six:

1. **Topic.** Propose 3-4 concrete candidates you found in the scan, each with a one-line
   "why now" (e.g. "v2.3 shipped last week: a what's-new deck", "the `sync/` subsystem is
   the largest and undocumented: a deep dive", "no onboarding doc exists: a general
   overview"), plus "something else: tell me". Never ask a bare "what should the deck be
   about?": the scan is what makes this question answerable in one click. Mark as default
   the candidate you would genuinely bet the user wants given the repo's core domain and
   its deck history (a core subsystem with zero coverage usually beats a
   recently-changed-but-already-presented area), not mechanically the most recent change.
2. **Audience and venue.** New joiners (onboarding) · team sprint/standup · stakeholder or
   exec review · conference/meetup. This drives jargon level, pacing, and the Sizing row.
3. **Length.** Offer the Sizing table rows as time slots ("5-min lightning ≈ 8-15 slides",
   "20-min deep dive ≈ 12-20", "45-min onboarding ≈ 20-35").
4. **Design.** Theme menu from [`references/themes.md`](references/themes.md): Ledger
   Light (default) · Ledger Dark · midnight · graphite · match a brand (ask for the URL/style
   guide; fetch it for real per [`references/style-guide.md`](references/style-guide.md)
   § Theming, never invent colors from a description). Optionally a font choice
   (themes.md § Font options) if the user signals caring about typography. If the user
   hesitates between themes or asks to see them, show rather than tell: copy the
   template, swap in each candidate preset's `:root` block, screenshot the title slide
   of each (the recipe in [`references/verification.md`](references/verification.md)),
   and present the images side by side before they choose.
5. **Scope and sensitive data.** Confirm what the deck may draw on and who will see it:
   "internal team" and "conference talk" are different redaction bars. Name anything
   off-limits up front (unannounced features, customer names, internal hostnames). The
   defaults in "The confidentiality rule" below apply regardless of the answer.
6. **Extras.** Three independent toggles, so don't letter them as alternatives: state the
   defaults and ask the user to object to any ("PDF export: no · Mermaid diagrams: built-in
   flow boxes only (Mermaid needs one-time `npx` network access, see
   [`references/diagrams.md`](references/diagrams.md)) · output:
   `<repo>/docs/slides/<topic-slug>-<date>.html`"). The output folder's shared companion
   `README.md` gets one section per deck; append or update your deck's section, never
   overwrite another's.

For "what changed" style decks, also pin the **recency window** (a date range or "since
the last release") and resolve it with `git log` before writing anything, not from memory.

**The outline checkpoint.** After the first research pass, show the user a proposed
**topic list and slide flow** (like a table of contents) and get a thumbs-up *before*
writing any HTML: this is the single highest-leverage checkpoint. Building 25 slides
around the wrong 6 topics wastes far more time than a 30-second review would have.
Skip the checkpoint only when one of these observable conditions holds:

- the user already gave you an explicit topic list or outline (not just scope/audience), or
- you are running non-interactively (no user available to answer): proceed, and say in
  your final summary that the outline was not reviewed.

## The confidentiality rule (applies to every step)

A deck is a document that leaves the repository: it gets emailed, screen-shared, and
posted. Treat everything you put on a slide as public from the moment it is written.

**Never read for slide content, and never quote:** `.env` and any `*.env*`, key/certificate
files (`*.pem`, `*.key`, `id_rsa*`, `*.p12`, service-account JSON), `secrets/`,
`credentials*`, `.npmrc`/`.pypirc`/`.netrc`, CI secret definitions, production logs,
database dumps, fixtures containing real customer data, and any path the repository's own
ignore files exclude. If a file you need is on this list, describe its *shape* ("a service
account JSON, mounted at runtime") instead of its content.

**Redact even from files that are safe to quote:** credentials, tokens, API keys, private
hostnames and internal URLs, IP addresses, account and customer identifiers, personal
names and emails that are not public contributors, and precise infrastructure paths where
a generic description carries the same meaning. Replace with a clear placeholder
(`<project-id>`, `db.internal.example`), never a plausible-looking fake.

**Ask when it is the user's call, not yours:** if a slide would be materially weaker
without a detail that looks sensitive (an internal hostname in a diagram, a real customer
count, an unannounced feature name), ask the user before including it, and say what you
are about to expose. Silence is not consent.

**Screenshots carry more than you think.** A screenshot of a terminal, dashboard, or
editor also captures window titles, file trees, branch names, ticket numbers, other
tabs, and notifications. Crop to the region that makes the point, and read the image back
before embedding it.

Verification includes a redaction scan of the finished artifacts: see
[`references/verification.md`](references/verification.md) § Redaction scan.

## Step 1: Research (never skip, never approximate)

The deck is only as credible as its weakest verified claim. For every slide you plan to
write:

- **Respect the confidentiality rule below** when choosing what to open and what to quote:
  secrets, credentials, production logs, and real customer data are out of scope for slide
  content even when they would be interesting.
- **Read the real files.** README(s), package manifest (`pyproject.toml`, `package.json`,
  `go.mod`, …), the actual source of anything you plan to quote or diagram, existing
  architecture docs, existing agent-instruction files (`CLAUDE.md`, `.agents/skills/`,
  `.claude/skills/`, and similar: these often already describe real user-facing
  capabilities accurately, a goldmine for "say to your assistant" style bubbles).
- **Prefer code intelligence / grep+view over guessing.** If you're about to describe a
  class, a config schema, a CLI flag, or a directory layout, go find it and read it. If you
  can't find where a claim comes from, don't make the claim.
- **When the repo's own docs contradict its code, the code wins.** Docs drift; verify any
  doc-sourced claim against the current source before putting it on a slide, and if the
  drift is itself notable, say so on the slide rather than repeating the stale claim.
- **For "what's new" / recent-changes decks:** use `git log --oneline --since=... -- path`
  (and `git log -p` for real diff content) to ground every "shipped this month" claim in an
  actual commit, not a vague impression. Cross-check version bumps (e.g. `pyproject.toml`
  history) against the commits that produced them. A file added inside your window may
  already be deleted again by a later commit: `git show <commit>:<path>` recovers it, and
  the deletion may itself be worth a slide note.
- **For architecture/flow diagrams:** trace the real call path (imports, function calls,
  the actual sequence a request follows) rather than inferring structure from the file tree
  alone. A plausible-looking but wrong diagram is worse than a smaller, correct one. For
  rendering (built-in flow boxes vs pre-rendered Mermaid SVG), see
  [`references/diagrams.md`](references/diagrams.md).
- **For screenshots/plots:** use only real artifacts: a real chart the repo's own tooling
  produced, a real trace/log screenshot, a real terminal output. If a genuinely useful image
  doesn't exist yet, either generate it by actually running the repo's own code (reuse its
  existing plotting/export/reporting functions against real data on disk rather than
  writing new ad hoc plotting code) or fall back to a non-image pattern; never fabricate
  a fake chart.
- **Delegate research for large/unfamiliar repos.** If the repo is large or you're
  unfamiliar with it, a read-only exploration sub-agent pass ("find the CLI entry points,
  the README, the test/dataset conventions, and any existing architecture docs") is worth
  it before drafting the topic list, if your environment provides sub-agents. Don't
  delegate the actual slide writing: that needs your own judgment about pacing and what's
  genuinely interesting.

## Step 2: Draft the topic list

Before writing HTML, sketch the flow as a short outline (title → agenda → N sections, each
with 2-6 slides → close) and share it per the outline checkpoint above. A well-paced deck
opens with a title slide, an agenda, and 2-3 "the project in one picture" slides (what it
is, one or two real results/screenshots), then either a section-divider-led deep dive per
topic (for a general/multi-topic deck) or straight into content (for a focused deck), and
ends on a closing/roadmap slide. Typical density: **1 idea per slide**; resist cramming two
ideas onto one slide just to save a slide.

### Sizing

Section dividers count toward the slide budget.

| Deck type | Rough slide count | Section dividers? |
|---|---|---|
| Lightning update (one topic, one meeting) | 8-15 | No, straight into content |
| Focused deep dive (one subsystem/feature) | 12-20 | Optional, only if it has 2+ sub-topics |
| General overview / onboarding | 20-35 | Yes, one per major section |

## Step 3: Build

1. Copy [`assets/template.html`](assets/template.html) to the output path. It already has
   the full verified CSS + navigation JS; do not rewrite either from scratch. All slide
   markup lives between the `<!-- SLIDES START -->` and `<!-- SLIDES END -->` markers;
   everything outside them stays untouched (a scripted splice against those markers is the
   easiest way to replace the body in one pass), with two exceptions: set the `<head>`'s
   `<title>` to the real deck title, and swap the `:root` theme block if the user chose a
   non-default theme ([`references/themes.md`](references/themes.md)).
2. Work through your topic list slide by slide, copying the matching `PATTERN:` block from
   the template for each slide (title, agenda, section-divider, prose+cards, image+caption,
   table, before/after code, single annotated snippet, flow diagram, chat-bubble examples,
   lane comparison, closing: see the template's own comments for when to use which) and
   replacing every bracketed placeholder with real, verified content. Delete every pattern
   block you didn't end up using; delete the illustrative comments too once real content
   replaces them.
3. **Cite every snippet as you write it**, with the script, never by hand:

   ```bash
   python3 scripts/cite.py app/main.py:40-58 --repo <repo> --snippet
   ```

   It prints the `data-src` / `data-sha256` pair to paste onto the `<pre>`, warns when the
   lines are too wide for the pattern you chose, and with `--snippet` prints the source
   already HTML-escaped. Stamp the build commit once, when the deck is otherwise finished:

   ```bash
   python3 scripts/cite.py --stamp <deck.html> --repo <repo>
   ```

   A hand-computed hash is worse than no hash: it silently reports CHANGED months later
   and nobody can tell whether the code moved or the build was sloppy. Same for the date,
   which is easy to invent and impossible to verify afterwards. Cite anything you quote or
   assert from one place; prose summarising a whole subsystem needs no citation. See
   [`references/freshness.md`](references/freshness.md).
4. **HTML-escape every verbatim snippet**: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`
   inside `<pre>`/`<code>`. Unescaped source code (generics, arrows, includes) silently
   corrupts the markup downstream. Mind snippet line width too: see
   [`references/style-guide.md`](references/style-guide.md) § Code snippets.
5. Follow every rule in [`references/style-guide.md`](references/style-guide.md) as you
   write: sentence case, no em dashes in prose, tag accuracy, real-content-only, rather
   than fixing it all in a pass at the end.
6. Keep slide numbering visible to yourself: an HTML comment `<!-- N: LABEL -->` above each
   `<section class="slide">`. Comments are 0-indexed; the URL hash and the on-screen
   counter are 1-indexed. Worked example: `<!-- 6: ARCHITECTURE -->` is display slide 7,
   reached at `deck.html#7`. **Renumber the comments any time you insert or delete a
   slide**, and when the user later says "slide 12", re-derive which section that is from
   the file itself (`grep -n '<!-- [0-9]*:' deck.html`) rather than trusting a remembered
   count: a stale comment index is a fast path to editing the wrong slide.

## Step 4: Verify (every single slide, every single edit)

Do not consider the deck done until you've actually looked at it. This is not optional
polish: run for the first time on any deck, this step reliably catches real bugs: broken
image paths, text overlapping the nav pill, tables overflowing their card, stale slide
numbering, wrong aggregate numbers.

1. **Render every slide to an image** with headless Chrome and look at each one. Chrome
   discovery is platform-dependent: use the cross-platform recipe in
   [`references/verification.md`](references/verification.md), which also covers staging
   directories (always a fresh per-deck directory, never fixed shared paths: parallel deck
   builds collide) and a faster batched screenshot loop.
2. View each screenshot. Check specifically for: text clipped by or overlapping the bottom
   nav pill, cards/boxes stretching to fill unexpected empty space (add the `fill` class
   only where stretching is wanted; the grids default to content height), tables or code
   blocks overflowing their container, and images that failed to load (a small
   broken-image icon with visible alt text, almost always a relative-path problem: see the
   PDF workflow note in verification.md).
3. **Check citations resolve** before shipping: `python3 scripts/check.py <deck> --repo <repo>`
   should report every citation CURRENT. Anything else means the deck is already stale on
   the day it was built: CHANGED means you quoted something and then it moved under you (or
   the hash was hand-computed), UNVERIFIED means a snippet has no hash at all. Both are
   build defects, not future problems. Fix them now with `scripts/cite.py`.
4. **Check structural balance** after every edit: a stray unclosed `<div>` breaks
   everything downstream silently:
   ```bash
   python3 -c "
   import re
   c = open('deck.html').read()
   print('section:', len(re.findall(r'<section class=\"slide', c)), len(re.findall(r'</section>', c)))
   print('div:', len(re.findall(r'<div', c)), len(re.findall(r'</div>', c)))
   "
   ```
5. Fix what you find, re-screenshot *those* slides, confirm the fix. Clean up every temp
   screenshot/scratch file when you're done: nothing but the deck (+ optional PDF, +
   README) should remain.

## Step 5: Optional PDF export

If asked for a PDF, use the companion **slides-to-pdf** skill (distributed alongside this
one; its SKILL.md is the full self-contained recipe if it isn't installed as a skill).
It screenshots every slide at 2x, prints a page-per-slide PDF, and verifies the result by
rendering the PDF back to images, which is required because headless Chrome cannot
rasterize a local PDF for a visual check and image pages can be silently blank.

## Step 6: Ship it, and say how to keep it honest

Write (or extend) the companion `README.md` next to the deck. Re-read it immediately
before appending: another build may have changed it since your scan. One section per deck
in the folder, each covering: what the deck covers, slide count, how to view/navigate it, and,
since decks get edited slide-by-slide over many follow-up requests, a one-paragraph note
on how the file is structured for future edits (the pattern-block/comment-numbering
conventions above).

Tell the user, in your final message and in the README section, how to find out when the
deck has gone stale:

```bash
python3 scripts/check.py <deck-or-folder> --repo <repo> --suggest
```

Then **ask whether this deck should be kept in sync**, and make it concrete rather than
leaving it as a suggestion. The answer depends on what kind of document it is, so say so:

- **Evergreen** (onboarding, architecture, anything linked from a README): offer to add
  the pull-request check from [`references/automation.md`](references/automation.md).
  Report-only first (`--exit-zero`), so it annotates a PR without blocking anyone. Vendor
  `check.py` into the repo (`tools/slideops-check.py`), because it is one dependency-free
  standard-library file and the deck's repo should not depend on a skill being installed.
- **A snapshot** (sprint update, "what shipped in March", a conference talk): recommend
  *not* automating it. It describes a moment and is supposed to freeze. Say this out loud
  rather than silently skipping it.

Do not propose blocking every commit. A docs check on the fast path trains people to pass
`--no-verify`, and drift is a review-time concern. The reasoning, the workflow files, the
advisory hook variants, and the delegated-refresh recipe are all in
[`references/automation.md`](references/automation.md).

## Refreshing an existing deck

When the user asks whether a deck is still accurate, or wants one brought back in line,
**repair it; do not rebuild it**. A rebuild throws away the pacing, the narrative and the
review that went into the original, and costs far more than fixing three slides.

1. **Detect, for free.** Sweep the folder and read the result:

   ```bash
   python3 scripts/check.py docs/slides/ --repo . --json
   ```

   This costs no tokens and no model call. The JSON is a complete repair brief: per stale
   citation it carries the status, the unified diff, the commits that caused it, the
   corrected `data-src`/`data-sha256`, and the current source. Read that instead of
   re-reading the repository. If nothing is stale, say so and stop: that is the common
   case and it should be cheap.

2. **Triage by status**, because they need different work:
   - `MOVED`: the code is identical, only the line numbers shifted. Update the two
     attributes. **Do not touch the slide's prose**, and do not re-verify visually: nothing
     rendered changed.
   - `CHANGED`: read the diff *and the commit subjects*. A rename needs a re-quote; a
     deleted branch of logic may have killed the claim the slide makes. Decide about the
     claim first, then the snippet.
   - `MISSING`: the file is gone. The slide is probably obsolete. Find where it went
     (`git log --diff-filter=D -- <path>`) and ask the user before deleting a slide.
   - `UNVERIFIED`: no hash was recorded. Re-cite it with `scripts/cite.py` so it is
     checkable from now on.

3. **Repair only what drifted.** Edit those slides, re-trim snippets to the width budget
   ([`references/style-guide.md`](references/style-guide.md) § Code snippets), and leave
   every other slide alone.

4. **Re-stamp and re-verify.** `python3 scripts/cite.py --stamp <deck> --repo .`, then
   `check.py` until clean, then re-screenshot **only the slides you touched** (Step 4): a
   longer snippet can push content under the nav pill. Re-export the PDF only if one exists.

5. **Report what changed and why.** Name the slides you edited, the commits that caused
   the drift, and anything you judged still-true-despite-the-diff. That last category is
   where a human may disagree with you, so surface it rather than burying it.
