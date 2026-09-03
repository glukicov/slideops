# Markdown documentation mode

Sometimes the right artifact is not a deck: the user wants a document that lives in the
repository, renders on GitHub, and gets read top to bottom. This mode produces a single
self-contained Markdown file with the same guarantee as a deck: every quoted snippet
carries a citation, so `scripts/check.py` can prove later which sections still match the
code and hand an agent a repair brief for only the parts that drifted.

Choose this mode when the user says "markdown docs", "a document, not slides",
"README-style documentation", or asks for docs "that know when they go stale". Everything
about research rigor, confidentiality, and real-content-only carries over from SKILL.md
unchanged; this file covers only what differs.

## The carrier format

Two comment forms carry the same facts the HTML attributes carry in a deck. Both are
invisible in rendered Markdown.

The build stamp owns line 1 of the file:

```markdown
<!-- slideops-build commit=a8bde99 date=2026-08-31 repo=my-service -->
```

Each citation sits directly above the fence it vouches for:

````markdown
<!-- slideops data-src="app/main.py:40-58" data-sha256="a1b2c3d4e5f6" -->
```python
def main() -> int:
    ...
```
````

`data-src` and `data-sha256` mean exactly what they mean in decks (see
[`freshness.md`](freshness.md)): repository-relative path with an optional 1-indexed
inclusive line range, and the first 12 hex chars of the SHA-256 of the source lines at
build time. Hash the source, never a trimmed snippet, and never by hand:

```bash
python3 scripts/cite.py app/main.py:40-58 --repo . --md --snippet
```

prints the ready-to-paste comment plus the source in a language-tagged fence, unescaped
(Markdown needs no HTML escaping, and the fence grows automatically when the source
itself contains backtick fences). Stamp once, when the doc is otherwise finished:

```bash
python3 scripts/cite.py --stamp docs/architecture.md --repo .
```

Citations attach to the nearest preceding heading, the way deck citations attach to
slide comments. The freshness report names that heading when a citation drifts, so keep
headings specific: "The request path" locates a repair; "Details" does not.

## Intake differences

The Step 0 orientation pass and the compact intake carry over, with these swaps:

- **No theme, no length, no PDF questions.** Markdown has no slide budget and GitHub
  renders it; drop intake items 3 and 4, and the PDF toggle.
- **Output path**: default `<repo>/docs/<topic-slug>.md`. Ask only if the repo has an
  established docs layout that suggests otherwise.
- **Diagrams are free.** GitHub renders `mermaid` fences natively, so Mermaid needs no
  download and no opt-in here. Still trace the real call path before drawing one.
- The outline checkpoint still applies: propose the heading structure before writing.

## Build

1. Copy [`assets/template.md`](../assets/template.md) to the output path. It shows the
   pattern for cited snippets, Mermaid fences, images, and tables. Replace every
   bracketed placeholder with real content and delete the guidance comments.
2. **Cite every quoted snippet as you write it** with `cite.py --md --snippet`, never by
   hand. Cite anything quoted or asserted from one specific place; prose summarising a
   whole subsystem needs no citation.
3. **Images must be real artifacts** (a chart the repo's own tooling produced, a real
   screenshot), linked by a path that resolves from the doc's location. Crop and re-read
   screenshots per the confidentiality rule. Never fabricate an image.
4. Prose rules from [`style-guide.md`](style-guide.md) that are not slide-layout rules
   still apply: sentence case headings, no em dashes, no invented numbers, tag accuracy.
5. Stamp the doc with `cite.py --stamp` once content is final.

## Verify

1. `python3 scripts/check.py docs/<doc>.md --repo .` must report every citation CURRENT.
   CHANGED or UNVERIFIED on build day is a build defect: fix it with `cite.py` now.
2. Fences must balance and every `slideops` comment must sit directly above its fence;
   a preview render (GitHub, or any Markdown viewer) catches a broken fence instantly.
3. Confirm every image link resolves from the doc's committed location, not from your
   working directory.

## Ship, and keep it honest

**The doc is the only file you leave behind.** Do not write a companion `README.md`, index
or summary file beside it, and do not link it into an existing one unless the user asks:
the doc's own title and build stamp already say what it covers and where it came from, and
an uncited sidecar is the one file `check.py` cannot keep honest. Report what the doc
covers, and where you wrote it, in your final message instead.

Tell the user how to find out when the doc goes stale, exactly as with a deck:

```bash
python3 scripts/check.py docs/ --repo . --suggest
```

Directory sweeps pick up `.md` docs and `.html` decks together, skipping files that
carry no citations. The automation recipes in [`automation.md`](automation.md) apply
verbatim: the same vendored `check.py`, the same report-only pull request check, the
same evergreen-vs-snapshot decision.

## Optional PDF export

If the user asks for a PDF of the doc, follow [`markdown-pdf.md`](markdown-pdf.md): a
Markdown-to-HTML conversion, a print-CSS wrap, Chrome's native print pagination, a centred
`page / total` footer on every page, and the same render-back verification the
slides-to-pdf skill uses. Offer it the way decks offer PDF export; do not produce one
unasked.

## Refreshing a stale doc

The deck workflow in SKILL.md § Refreshing an existing deck applies with one word
swapped: repair sections, not slides.

1. `check.py <doc-or-folder> --repo . --json` is the complete repair brief: per stale
   citation it names the section heading, the status, the diff, the causing commits, and
   the corrected attributes.
2. Triage by status exactly as for decks: MOVED updates two attributes and touches no
   prose; CHANGED means read the diff and decide whether the section's claim still
   holds; MISSING usually means the section is obsolete (ask before deleting);
   UNVERIFIED means re-cite.
3. Rewrite only the sections that drifted, re-stamp, and run `check.py` until clean. No
   screenshots to redo: the rendered doc is the artifact.
