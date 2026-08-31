# Citations and freshness

A deck starts rotting the moment it is exported. Citations make that measurable: each
quoted snippet records where it came from and what the source looked like at the time, so
`scripts/check.py` can tell you later which slides are still true.

This is the difference between a deck that *claims* to be verified and one that can prove
it. Write citations as you build, not as a pass at the end.

## Citing a snippet

Two attributes on the `<pre>` (or on any element that carries quoted content):

```html
<pre class="code small"
     data-src="backend/app/main.py:40-58"
     data-sha256="a1b2c3d4e5f6">…HTML-escaped snippet…</pre>
```

- **`data-src`** is a repository-relative path, optionally with a 1-indexed inclusive line
  range: `path/to/file.py`, `path/to/file.py:42`, or `path/to/file.py:40-58`. Without a
  range, the whole file is the citation.
- **`data-sha256`** is the first 12 hex characters of the SHA-256 of the **source lines as
  they were when you built the deck**, joined with `\n`. Hash the source, not the slide:
  snippets are usually trimmed with `…`, so they never byte-match the file.

Never compute it by hand. `scripts/cite.py` prints the pair, warns when the lines are too
wide for the slide pattern, and with `--snippet` prints the source already HTML-escaped:

```console
$ python3 scripts/cite.py backend/app/main.py:40-58 --repo .
data-src="backend/app/main.py:40-58" data-sha256="a1b2c3d4e5f6"
```

A wrong hash is worse than a missing one: it surfaces months later as CHANGED, and by then
nobody can tell whether the code moved or the build was sloppy.

Cite anything you quote or assert from a specific place: code snippets, config blocks,
tables built from a source file, a diagram's underlying module. Prose that summarises a
whole subsystem does not need a citation; a number lifted from one line does.

## The Markdown carrier

A Markdown doc (see [`markdown.md`](markdown.md)) carries the same two attributes in an
HTML comment directly above the fence it vouches for, invisible when rendered:

````markdown
<!-- slideops data-src="backend/app/main.py:40-58" data-sha256="a1b2c3d4e5f6" -->
```python
...verbatim source...
```
````

`cite.py --md` prints the comment (and with `--snippet` the fenced source, no HTML
escaping needed). Citations attach to the nearest preceding heading, which is what the
report names instead of a slide number. The build stamp is a comment on line 1:

```markdown
<!-- slideops-build commit=a9c9c0d date=2026-08-24 repo=my-service -->
```

`cite.py --stamp doc.md` writes it, and `check.py` treats `.md` and `.html` targets
identically from there on: same statuses, same `--suggest`, same `--json` repair brief.

## Recording the build point

Once per deck, in the `<head>`:

```html
<meta name="slideops-build" content="commit=a9c9c0d date=2026-08-24 repo=my-service">
```

The commit is what lets `check` explain *how* a snippet changed rather than only that it
did: it reads the old lines from that commit and diffs them against today's, and lists the
commits responsible. Without it, you still get CURRENT/CHANGED, just no diff, no move
detection and no "who changed this". Write it with the script, which uses the repository's
real HEAD and today's real date rather than a remembered one:

```bash
python3 scripts/cite.py --stamp docs/slides/architecture.html --repo .
```

## Checking a deck later

```bash
python3 scripts/check.py docs/slides/architecture.html --repo .   # one deck
python3 scripts/check.py docs/slides/ --repo .                    # sweep a folder
python3 scripts/check.py docs/slides/ --repo . --quiet            # silent unless stale
python3 scripts/check.py docs/slides/ --repo . --suggest          # + diff, commits, the fix
python3 scripts/check.py docs/slides/ --repo . --json             # repair brief for an agent
```

A directory is swept recursively, skipping HTML that carries no citations. The run is
standard library only: no model, no network, no tokens.

| Status | Meaning | What to do |
|---|---|---|
| `CURRENT` | cited lines are byte-identical | nothing |
| `MOVED` | same content, new line numbers | update `data-src`, leave the slide's text alone |
| `CHANGED` | the cited lines differ | read the diff, decide whether the slide's claim still holds, re-quote |
| `MISSING` | the file is gone | the slide is probably obsolete; `git log --diff-filter=D -- <path>` finds where it went |
| `UNVERIFIED` | no hash, or the build commit is not in this repo | re-cite the snippet |

Exit code is 1 when anything is stale, and `--exit-zero` forces 0 for report-only jobs. How
to wire that into a pull request, a scheduled refresh, or an advisory agent hook (and which
decks deserve it at all) is in [`automation.md`](automation.md).

## Updating a stale deck

Repair the slides that drifted; do not rebuild the deck. The full workflow, including how
to triage each status, is in SKILL.md § Refreshing an existing deck. In short:

1. `--suggest` (for a human) or `--json` (for an agent) prints, per stale citation, what
   changed, **which commits changed it**, the corrected `data-src` and `data-sha256`, and
   the current source HTML-escaped and ready to paste.
2. Read the diff and the commit subjects, then decide whether the slide's **claim** is
   still true. A renamed variable usually just needs a re-quote; a deleted branch of logic
   may invalidate the whole slide. `MOVED` never needs a prose change at all.
3. Replace the snippet, update both attributes, and re-trim to the width budget
   (style-guide.md § Code snippets). Both scripts warn when lines are too wide for the
   pattern you used.
4. Re-stamp and re-verify: `python3 scripts/cite.py --stamp <deck> --repo .`, then `check`
   until clean, then re-screenshot the slides you touched (a longer snippet can push
   content under the nav pill).

A deck whose citations all pass is not automatically correct: the prose around a snippet
can still be wrong, and `check` cannot see that. It tells you what has *definitely* drifted,
which is the part humans reliably miss.
