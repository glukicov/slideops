# Markdown Documentation Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach the slideops skill to generate single-file Markdown documentation whose fenced snippets carry the same `data-src`/`data-sha256` citations as slide decks, so `check.py` can report exactly which sections drifted and an agent regenerates only those.

**Architecture:** Markdown is a second *carrier* for the existing citation engine. Citations are HTML comments (`<!-- slideops data-src="…" data-sha256="…" -->`) directly above fenced code blocks; the build stamp is `<!-- slideops-build commit=… date=… repo=… -->` on line 1. `check.py` gains a fence-masking Markdown scanner that attributes citations to the nearest heading; `cite.py` gains `--md` output and `.md` stamping. All status logic, diffing, and the `--json` repair brief are untouched.

**Tech Stack:** Python 3.14. Shipped scripts (`skills/slideops/scripts/`) are standard library only + `argparse`. Dev harness uses pytest, typer, ruff, ty (NOT mypy).

**Spec:** `docs/superpowers/specs/2026-08-31-markdown-support-design.md`

## Global Constraints

- No third-party imports in `skills/**/scripts/` (CI runs them on bare python3).
- `.claude-plugin/plugin.json` `version` must equal `skills/slideops/SKILL.md` `metadata.version` → both become `1.1.0`.
- No em dashes in Markdown/HTML prose outside code fences/`<pre>`.
- ruff line-length 120; verify with `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest && uv run python scripts/validate.py`.
- `.md` handling must not change any behaviour for `.html` decks (existing tests stay green untouched).
- Editing `skills/slideops/assets/template.html` or `references/diagrams.md` breaks the demo deck's citations; this plan never touches those lines.

---

### Task 1: check.py reads Markdown docs

**Files:**
- Modify: `skills/slideops/scripts/check.py`
- Test: `tests/test_check.py`

**Interfaces:**
- Produces: `mask_fences(text: str) -> str` (same length/offsets, fenced regions blanked), `find_citations_md(doc_text: str) -> list[Citation]`, `MD_CITATION_RE`, `MD_BUILD_META_RE`, `is_markdown(path: Path) -> bool`; `DeckReport` gains `kind: str` (`"deck"` or `"doc"`); `parse_build_meta(text, *, markdown=False)`.

- [ ] **Step 1: Write failing tests** in `tests/test_check.py` (new classes `TestMaskFences`, `TestFindCitationsMd`, `TestMdBuildMeta`):

```python
DOC = """<!-- slideops-build commit=abc1234 date=2026-08-31 repo=demo -->
# Title

## The request path

<!-- slideops data-src="app/main.py:40-58" data-sha256="a1b2c3d4e5f6" -->
```python
def main() -> int: ...
```

## Teaching the syntax

```markdown
<!-- slideops data-src="fake/example.py:1-2" data-sha256="000000000000" -->
```
"""

class TestMaskFences:
    def test_fenced_content_is_blanked_but_offsets_survive(self) -> None:
        masked = check.mask_fences(DOC)
        assert len(masked) == len(DOC)
        assert "def main" not in masked
        assert "## The request path" in masked

class TestFindCitationsMd:
    def test_citation_attaches_to_the_nearest_heading(self) -> None:
        (c,) = check.find_citations_md(DOC)
        assert c.src == "app/main.py:40-58"
        assert c.recorded_sha == "a1b2c3d4e5f6"
        assert c.slide_label == "The request path"

    def test_examples_inside_fences_are_not_citations(self) -> None:
        assert len(check.find_citations_md(DOC)) == 1

class TestMdBuildMeta:
    def test_comment_stamp_parses_like_the_meta_tag(self) -> None:
        build = check.parse_build_meta(DOC, markdown=True)
        assert build == {"commit": "abc1234", "date": "2026-08-31", "repo": "demo"}
```

- [ ] **Step 2:** `uv run pytest tests/test_check.py -k "MaskFences or Md" -v` → FAIL (attributes missing).
- [ ] **Step 3: Implement** in `check.py`:

```python
MD_SUFFIXES = {".md", ".markdown"}
MD_CITATION_RE = re.compile(
    r'<!--\s*slideops\s+data-src="(?P<src>[^"]+)"(?:\s+data-sha256="(?P<sha>[0-9a-f]{6,64})")?\s*-->', re.I
)
MD_BUILD_META_RE = re.compile(r"<!--\s*slideops-build\s+(?P<content>[^>]*?)\s*-->", re.I)
MD_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*$", re.M)

def is_markdown(path: Path) -> bool: ...

def mask_fences(text: str) -> str:
    # line loop; a fence opens on ```/~~~ (>=3), closes on a same-char run at least as long;
    # fence delimiter lines and fenced content are replaced char-for-char with spaces (newlines kept)

def find_citations_md(doc_text: str) -> list[Citation]:
    # scan mask_fences(doc_text); headings enumerated in order become the (position, index, label)
    # anchors; the existing nearest-preceding-anchor loop attributes each MD_CITATION_RE match
```

`parse_build_meta` gains `markdown: bool = False` and searches `MD_BUILD_META_RE` over the masked text when true. `check_deck` routes on `is_markdown(deck)` and sets `report.kind`. `DeckReport` gets `kind: str = "deck"`.

- [ ] **Step 4:** targeted tests PASS, then full `uv run pytest tests/test_check.py` PASS.
- [ ] **Step 5:** Commit: `feat: check.py parses Markdown citation comments and headings`.

### Task 2: check.py sweeps and reports Markdown docs

**Files:**
- Modify: `skills/slideops/scripts/check.py` (`looks_like_deck`, `collect_decks`, `print_deck`, `print_suggestions`, `emit_json`)
- Test: `tests/test_check.py::TestCollectDecks` and a small md report test

**Interfaces:**
- Consumes: Task 1's `is_markdown`, `mask_fences`, regexes.
- Produces: directory sweeps include `*.md` carrying a stamp or citation (fence-masked, so docs merely showing the syntax are skipped); reports print `section` instead of `slide` for docs; JSON deck objects gain `"kind"`.

- [ ] **Step 1: Failing tests:** a citation-bearing `.md` in a swept directory is found; a plain `README.md` and a `.md` whose only "citation" sits inside a fence are skipped; `print_deck` output for a doc says `section`.
- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: Implement:** `collect_decks` rglobs `*.html` + `*.md`; `looks_like_deck` masks fences for md files before probing either regex pair; `print_deck`/`print_suggestions` derive the noun from `report.kind`; `emit_json` adds `"kind"`.
- [ ] **Step 4:** `uv run pytest tests/test_check.py -v` → PASS.
- [ ] **Step 5:** Commit: `feat: check.py sweeps Markdown docs and reports sections`.

### Task 3: cite.py --md output

**Files:**
- Modify: `skills/slideops/scripts/cite.py`
- Test: `tests/test_cite.py`

**Interfaces:**
- Produces: `cite_one(ref, repo, show_snippet, markdown=False)`; CLI flag `--md`. With `--md`: prints `<!-- slideops data-src="…" data-sha256="…" -->`; with `--snippet` also a fenced block (language from suffix via `FENCE_LANGS`, fence longer than any backtick run, no HTML escaping); width warnings suppressed.

- [ ] **Step 1: Failing tests** (capsys):

```python
def test_md_flag_prints_a_ready_to_paste_comment(tmp_repo, capsys): ...  # startswith "<!-- slideops data-src="
def test_md_snippet_is_fenced_with_the_language(tmp_repo, capsys): ...   # "```python" fence, raw '<' unescaped
def test_fence_grows_past_backtick_runs_in_the_source(tmp_repo, capsys): ...  # source holds ```; fence is ````
def test_md_suppresses_width_warnings(tmp_repo, capsys): ...             # 100-char line, empty stderr
```

- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: Implement** (`FENCE_LANGS` dict, `fence_for(lines)` helper, thread `markdown` through `main`).
- [ ] **Step 4:** `uv run pytest tests/test_cite.py -v` → PASS.
- [ ] **Step 5:** Commit: `feat: cite.py --md prints comment citations and fenced snippets`.

### Task 4: cite.py stamps .md files

**Files:**
- Modify: `skills/slideops/scripts/cite.py` (`stamp`)
- Test: `tests/test_cite.py::TestStamp`

**Interfaces:**
- Produces: `--stamp doc.md` writes `<!-- slideops-build commit=… date=… repo=… -->` as line 1 (replaces an existing line-1 stamp, otherwise inserts above the current first line). HTML behaviour unchanged. A stamp-shaped comment deeper in the file (e.g. a fenced example) is never touched.

- [ ] **Step 1: Failing tests:** insert into a fresh doc → line 1 is the stamp, old content intact; re-stamp replaces line 1 without duplicating; a doc whose only stamp-shaped text is inside a fence gets a new line-1 stamp and the fenced example survives byte-for-byte.
- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: Implement:** branch in `stamp()` on suffix; match `^<!--\s*slideops-build[^>]*-->` only at position 0.
- [ ] **Step 4:** tests PASS.
- [ ] **Step 5:** Commit: `feat: cite.py --stamp writes the comment stamp into Markdown docs`.

### Task 5: Markdown freshness lifecycle end-to-end

**Files:**
- Test: `tests/test_freshness.py`

**Interfaces:**
- Consumes: everything from Tasks 1-4 via the CLIs (`check.main`, `cite.main` invoked as the existing DeckRepo harness does).

- [ ] **Step 1:** Extend the throwaway-git-repo harness with a `write_doc()` sibling of the deck writer (same cited `src/app.py` lines, doc form). Add tests mirroring the HTML ones: fresh doc all CURRENT; shifted lines MOVED with new range; edited line CHANGED with diff + causing commit in `--json`; deleted file MISSING; missing hash UNVERIFIED; applying the JSON `suggested_src`/`suggested_sha256` back into the doc makes it CURRENT; a directory sweep finds the doc and the deck together.
- [ ] **Step 2:** run → new tests FAIL only if Tasks 1-4 left a gap; fix in the scripts, not by weakening tests.
- [ ] **Step 3:** `uv run pytest` (full suite) → PASS.
- [ ] **Step 4:** Commit: `test: Markdown doc freshness lifecycle end-to-end`.

### Task 6: template.md and validate.py coverage

**Files:**
- Create: `skills/slideops/assets/template.md`
- Modify: `scripts/validate.py`

**Interfaces:**
- Produces: `check_markdown(path: Path, *, is_template: bool)` wired into `main()` for `assets/template.md` and `examples/*.md`. Template keeps a `[DOC TITLE]` placeholder; examples must have no unfilled `[...]` placeholders, balanced fences, no em dashes in prose, no malformed `<!-- slideops` comments (comment without `data-src=`).

- [ ] **Step 1:** Write `template.md`: `[DOC TITLE]` H1 under a `PATTERN:` comment header, worked citation-comment + fence example, a `mermaid` fence, an image pattern, section guidance comments mirroring template.html's tone.
- [ ] **Step 2:** Implement `check_markdown` in validate.py; wire into `main()`.
- [ ] **Step 3:** `uv run python scripts/validate.py` → OK. Temporarily break a fence in template.md → FAIL line appears → revert.
- [ ] **Step 4:** Commit: `feat: Markdown doc template and validate.py checks`.

### Task 7: Skill prose and version 1.1.0

**Files:**
- Create: `skills/slideops/references/markdown.md`
- Modify: `skills/slideops/SKILL.md` (description triggers, docs-mode routing, `metadata.version: 1.1.0`), `skills/slideops/references/freshness.md` (Markdown carrier section), `.claude-plugin/plugin.json` (1.1.0 + description), `.claude-plugin/marketplace.json` (description)

**Interfaces:**
- Consumes: the CLI surfaces exactly as shipped in Tasks 1-4 (`--md`, comment stamp, section reports).

- [ ] **Step 1:** Write `references/markdown.md` (~130 lines): when to choose docs over slides; intake differences (no theme/length/PDF; ask output path, default `<repo>/docs/<topic-slug>.md`; Mermaid fences render natively on GitHub, no npx); build loop (copy template.md, cite-as-you-write with `cite.py --md --snippet`, images must be real artifacts with repo-relative links); stamp; verify (`check.py`, fence balance); ship (companion README section, the keep-honest command); refresh (same status triage, sections instead of slides).
- [ ] **Step 2:** SKILL.md: add a "Markdown documentation instead of slides" routing block after "Which job is this?", extend the frontmatter description with docs triggers (stay under 1024 chars), bump version. freshness.md: add the comment syntax beside the `<pre>` syntax. Bump both manifests.
- [ ] **Step 3:** `uv run python scripts/validate.py` → OK (this catches a version mismatch and broken relative links).
- [ ] **Step 4:** Commit: `feat: Markdown docs mode contract, SKILL.md routing, v1.1.0`.

### Task 8: Example doc, CI wiring, self-citation test

**Files:**
- Create: `skills/slideops/examples/skill-demo.md`
- Modify: `.github/workflows/ci.yml` (both citation-check steps), `tests/test_freshness.py` (example-doc test)

**Interfaces:**
- Consumes: all previous tasks, committed (citations must hash the committed final code).

- [ ] **Step 1:** After Task 7's commit, build `skill-demo.md` by following `references/markdown.md` for real: a doc about the Markdown mode itself, citing current lines of `check.py`/`cite.py` with `uv run python skills/slideops/scripts/cite.py <ref> --repo . --md --snippet`, one Mermaid diagram of the cite→check→repair loop, one image (`../../../docs/hero.png`), stamped with `--stamp`.
- [ ] **Step 2:** `uv run python skills/slideops/scripts/check.py skills/slideops/examples/skill-demo.md --repo .` → every citation CURRENT. Also `python3` (bare) same command.
- [ ] **Step 3:** Add `test_the_example_doc_still_matches_this_repository` beside the deck twin; extend both ci.yml citation steps to include the `.md` example.
- [ ] **Step 4:** `uv run pytest` → PASS; `uv run python scripts/validate.py` → OK.
- [ ] **Step 5:** Commit: `feat: shipped Markdown example doc, checked in CI`.

### Task 9: README, full verification, PR

**Files:**
- Modify: `README.md`

- [ ] **Step 1:** Add a short "Markdown docs, same guarantee" section to README.md (what it is, the carrier snippet, the same check command).
- [ ] **Step 2:** Full sweep: `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest && uv run python scripts/validate.py && uv run python scripts/smoke_test.py` plus both bare-python3 example checks.
- [ ] **Step 3:** Commit, push `feature/markdown`, open the PR against `main` with `gh pr create` (body: summary, carrier format, test evidence, v1.1.0 note).
