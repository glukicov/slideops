# Style guide

Apply these rules as you write each slide, not as a cleanup pass afterward.

## Language

**Sentence case, always.** Slide titles, kickers, tags, table headers, section-divider
labels: all sentence case (`Six orchestrator modes`, not `SIX ORCHESTRATOR MODES`). The
template's CSS has no forced `text-transform: uppercase` anywhere; don't add it back.

**No em dashes ( — ) in prose, anywhere.** Replace them contextually, not with a single
blanket substitution:

| Context | Original em-dash pattern | Replacement |
|---|---|---|
| Label, then elaboration | `Pushed — every run` | `Pushed: every run` |
| Parenthetical aside | `a bundle — local or hosted — can be onboarded` | `a bundle, local or hosted, can be onboarded` |
| Short badge/tag text | `Live — last 100 calls` | `Live · last 100 calls` |
| Joining two short nouns in a heading | `Talk to the assistant — and the loop` | `Talk to the assistant & the improvement loop` |
| Mid-sentence emphasis break | `stays the default — legacy` | `stays the default: legacy` |

Verbatim code snippets are the one place an em dash may legitimately survive: if a real
source line you are quoting contains one, prefer trimming that line (comments are usually
the culprit and usually trimmable) over rewording the snippet; never edit quoted code just
to satisfy the character rule. Practical check: every `grep -n "—" deck.html` hit must be
inside a `<pre>` snippet copied verbatim from source; prose hits are bugs.

**En dashes ( – ) for genuine numeric/date ranges are fine and expected**:
`Aug 17–20`, `140–165`. Don't touch these; they aren't the same character or the same
problem.

**Concise, technical, no marketing language.** Short declarative sentences. Numbers and file
paths over adjectives. If you can cut a word without losing meaning, cut it.

**Prefer assertion titles.** When a slide makes a claim, the title states the claim
(`Every write is replicated off-box`, not `Replication overview`); the audience should get
the point from titles alone. Plain topic labels are fine for reference slides (tables,
pattern lists) that don't argue anything.

**No emoji in slide prose.** The only emoji in a deck is the one the chat-bubble pattern
ships (💬). If source material you're summarizing contains emoji, paraphrase around them;
in verbatim snippets, prefer quoting lines without them.

## Content accuracy: the rule that matters most

**Every code snippet, file path, command, config field, and number on a slide must be
copy-verified against the real repository before it's typed onto a slide.** Concretely,
that means before you write a snippet:

- `view`/`grep` the real file and copy from it; don't reconstruct a class or config from
  memory or from a similar-looking example elsewhere.
- If you reference a field name (e.g. a dataclass attribute), confirm it exists in the
  actual class definition, not just in a doc that describes it (docs drift; code wins).
- If you claim a skill/CLI does something ("say to the assistant: ... → does X"), find the
  actual skill file or `--help` text that makes that true, and match your bubble's
  arrow-text to what it actually says.
- If you build a chart, generate it from the tool's own real plotting/reporting code against
  real data on disk, not a hand-drawn approximation. If you can't get real data, use a
  different slide pattern instead of a fake chart.
- If you report an aggregate stat (a mean, a percentile, a count of "successful" items),
  recompute it yourself from the real underlying data and state your filter explicitly (e.g.
  "the N most recent **successful** calls", and if asked to double check, actually
  cross-verify every item's status field against the raw source, not just trust the
  aggregation code once).

A wrong or invented technical detail is far worse than a slide with less detail on it.

## Code snippets on slides

- **Cite it**: every snippet carries `data-src` and `data-sha256` (references/freshness.md).
  An uncited snippet cannot be checked later, which defeats the point of quoting it.
- **Escape first**: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;` in every snippet. Unescaped
  generics/arrows/includes corrupt the surrounding markup silently.
- **Line width budget**: `pre.code` clips overflow silently (`overflow:hidden`). At the
  `small` size, a half-width column (the two-column patterns) fits roughly **65
  characters** per line; a full-width `pre` fits roughly **95**. Measure your longest line
  before choosing a pattern; if real lines exceed the half-width budget, use a full-width
  `pre` with explanation cards above/below instead of beside.
- **Trim with `…`**, never reword. Dropping whole lines (imports, long comments) and
  dedenting a nested snippet are fine; rewrapping a long line, truncating within a line,
  dropping type annotations, or any other edit inside a line counts as rewording and is
  not. When the load-bearing line itself exceeds every width budget, don't quote it at
  all: cite it as `path:line`, quote the shorter surrounding lines verbatim, and explain
  the long one in a card beside the snippet.

## Tags and severity: don't editorialize

The template ships five tag classes: `tag-new`, `tag-major`, `tag-existing`, `tag-optional`,
`tag-critical`. Use them to state a fact, never to dramatize one:

- Don't call something "breaking" unless it truly breaks a **shipped, relied-upon**
  contract. A schema/format change with no prior external consumers is a new version, not a
  breaking one: label it with the version number (`tag-major`, text like `v1.0.0`), not the
  word "breaking".
- On a roadmap/closing slide, distinguish **shipped** from **planned** unmistakably: shipped
  items use `.list-check` (✓), unshipped/planned items use `.list-todo` (→) with an explicit
  `(not yet shipped)` qualifier next to the heading. Mixing these (e.g. checkmarking planned
  work) reads as a false claim of completion.

## Images: real artifacts only

Every image on a slide must be a genuine artifact: a real screenshot, a real chart the
project's own tooling produced from real data, a real terminal/editor capture. Caption it
with real numbers pulled from that same image or its underlying data; never a plausible
guess. If a useful visual doesn't exist yet, generate it by actually invoking the project's
own real code path (reusing its existing plotting/export functions is strongly preferred
over writing new ad hoc plotting code), or pick a non-image slide pattern instead.

Images normally reference files by relative path. A deck that will be distributed
standalone, away from the folder its images live in, should embed them as base64
`data:image/png;base64,…` URIs instead, so the single HTML file stays self-contained
(at roughly +33% of the image bytes; keep such decks to a handful of images).

## Density and pacing

Roughly **one idea per slide**. A table, a diagram, a code comparison, and a prose point
each deserve their own slide rather than being stacked together to save slide count. Use
section-divider slides (the `section-slide` pattern) as breathing room between major topics
in a multi-topic deck. In a focused single-topic deck, kickers are usually landmark enough:
add dividers only when its sub-topics each run 3+ slides; never in a lightning update.

## Theming

The template is fully tokenized: every color derives (via `color-mix`) from the single
`:root` block at the top, so **switching theme = replacing that one block**. Preset
palettes and font options live in `references/themes.md`; offer them in the intake.

If the user names a brand or reference site instead: **fetch it for real** (use your
web-fetch tool to pull the site and read its actual CSS) and extract its literal hex/rgba
values; don't approximate a palette from a verbal description or a vague memory of the
brand. Map the extracted values onto the token roles per themes.md § Mapping a brand.

Two invariants, checked with the same grep:

```bash
grep -nE "rgba?\(|hsla?\(|oklch\(|hwb\(|#[0-9a-fA-F]{3,6}\b" deck.html
```

1. Every hit must be inside the `:root` block, inside an inlined SVG (whose colors are
   baked at render time; re-render Mermaid diagrams after any theme swap, see
   `references/diagrams.md`), or inside a verbatim `<pre>` snippet whose real source
   contains the literal (quoted code is never edited to satisfy this rule, same as the
   em-dash carve-out). A literal anywhere else is a bug: replace it with a token or a
   `color-mix` of one, in the template too if that's where it came from.
2. After a swap, zero old-palette values remain outside inlined SVGs and verbatim
   snippets.
