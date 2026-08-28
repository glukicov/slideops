# The Ops half: build once, stay in sync

Generating a deck is the easy part now. This page is about the other half: knowing whether
anyone should still trust it six months later.

It's the tour, not the specification. Attribute formats, how the hash is computed and what
each status means to the agent all live in
[`skills/slideops/references/freshness.md`](../skills/slideops/references/freshness.md),
which ships inside the skill and wins if the two ever disagree.

## The mechanism

Every quoted snippet records where it came from and what that source looked like at build
time, and the deck records the commit it was built from:

```html
<pre class="code" data-src="backend/app/main.py:40-58" data-sha256="a1b2c3d4e5f6">…</pre>
```

```html
<meta name="slideops-build" content="commit=077a837 date=2026-08-26 repo=slideops">
```

That's it. That one attribute pair is what turns a document into something you can maintain
instead of something you rewrite from scratch.

## Two commands, very different costs

| | Command | Cost |
|---|---|---|
| **Detect** | `check.py docs/slides/ --repo .` | Standard library only. No model, no network, **no tokens** |
| **Repair** | hand `check.py --json` to your agent | Tokens, and a review. Scoped to the slides that drifted |

This asymmetry is the whole design. If keeping documentation in sync means an agent
re-reads your repository on every commit, you've built something that costs real money,
adds latency, and gets quietly switched off within a month.

```console
$ python3 check.py docs/slides/ --repo .
  slide   7  PIPELINE     backend/app/main.py:40-58        CURRENT
  slide  12  MIGRATIONS   backend/alembic/env.py:18-31     MOVED      same content, now at lines 22-35
  slide  15  RATE-LIMIT   backend/app/middleware/rate.py   CHANGED    4 line(s) differ

1 current, 2 stale, 3 cited in total.
```

## The statuses, and why the distinction matters

| Status | Means | What to do |
|---|---|---|
| `CURRENT` | The cited lines still hash the same | Nothing |
| `MOVED` | Same content, different line numbers | Update two attributes; the prose is still true |
| `CHANGED` | The logic at that path is different | A human decides whether the claim survives |
| `MISSING` | The file is gone | The slide may be describing something that no longer exists |
| `UNVERIFIED` | No hash, or a build commit this repo doesn't have | A build defect, not drift |

`MOVED` versus `CHANGED` is the distinction I care about most, and it's what makes this
worth automating. Code shifting thirty lines down isn't a documentation problem, and a tool
that can't tell the two apart produces noise people learn to ignore.

`--suggest` prints the diff, the commits responsible, and the corrected citation. `--json`
is a complete repair brief: for every stale citation it carries the status, the unified
diff, the commits that caused it, the corrected `data-src` and `data-sha256`, and the
current source. An agent never has to re-read the repository to work out what changed.

## Writing citations

```console
$ python3 skills/slideops/scripts/cite.py app/main.py:40-58 --repo .
data-src="app/main.py:40-58" data-sha256="a1b2c3d4e5f6"
```

`cite.py` writes those attributes and stamps the build commit, so no hash is ever computed
by hand. A wrong hash is worse than a missing one. It surfaces months later as `CHANGED`,
and nobody can tell whether the code moved or the build was sloppy, which is why the skill
never asks you or the agent to work one out.

## Automate the detection, not the repair

The exit code is 1 when anything is stale and `--exit-zero` forces a report-only run, so
the natural home is a pull request to `main`:

```yaml
- name: Are the decks still true?
  run: python3 tools/slideops-check.py docs/slides/ --repo . --suggest --exit-zero
       | tee -a "$GITHUB_STEP_SUMMARY"
```

Deliberately not a blocking pre-commit hook. Code moves fast, and a docs check on the fast
path just teaches everyone to pass `--no-verify`. Drift is a review-time concern.

Pull-request checks, scheduled refreshes, advisory agent hooks, and the rule for which
decks deserve automation at all (a sprint update is *supposed* to freeze) are in
[`skills/slideops/references/automation.md`](../skills/slideops/references/automation.md).

## What a clean check doesn't prove

`check` verifies that quoted source still matches the code. It can't see that the prose
around a snippet has quietly become wrong, that a slide is missing a subsystem added last
quarter, or that an architecture diagram is now fiction. It tells you what has *definitely*
drifted, which is the part humans reliably miss, and it leaves you a smaller, human-sized
problem.

That's the *Ops* half. The point was never "AI made slides". The point is a document that
can prove it's current, and tell you exactly where it isn't.

## The accuracy contract

Drift checking only matters if the slide was true the day it was built. This is what makes
a generated deck safe to present:

| Always | Never |
|---|---|
| Code snippets copied verbatim from real files, then HTML-escaped | Fabricate a chart or invent numbers for a caption |
| Aggregate stats recomputed from the raw data | Reword a quoted line to make it fit the slide |
| "Shipped" claims grounded in actual commits via `git log` | Checkmark planned work as if it shipped |
| Diagrams traced through real imports and call sites | Trust a doc the code contradicts |

When a repository's own docs contradict its code, the code wins and the disagreement
becomes a note on the slide. The rules the agent follows are in
[`skills/slideops/references/style-guide.md`](../skills/slideops/references/style-guide.md).

## What it won't put on a slide

Decks leave the repository, so SlideOps treats everything on a slide as public. It won't
read secrets, keys, credentials files, production logs or real customer data for slide
content. It redacts tokens, private hostnames and personal data out of anything it does
quote, asks before including a detail that looks sensitive, and ends the verification pass
with a redaction scan over the HTML, the PDF, the speaker notes and every embedded image.
The intake asks who will see the deck, because an internal standup and a conference talk
are different bars.

Chrome keeps its sandbox on throughout, and nothing in the skills passes `--no-sandbox`.
Downloads are pinned and optional: Mermaid is opt-in, the PDF verifier reuses an existing
install when it finds one, and neither is required to build a deck.
