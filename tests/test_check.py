"""Unit tests for the freshness checker's parsing and classification logic.

These cover the pure functions: how a citation is parsed out of a deck, how source lines
are sliced and hashed, and what the JSON payload promises an agent. The end-to-end
behaviour against a real git repository lives in test_freshness.py.
"""

from __future__ import annotations

from pathlib import Path

import check


class TestParseSrc:
    def test_path_only(self) -> None:
        assert check.parse_src("app/main.py") == ("app/main.py", None, None)

    def test_single_line_becomes_a_one_line_range(self) -> None:
        assert check.parse_src("app/main.py:42") == ("app/main.py", 42, 42)

    def test_range(self) -> None:
        assert check.parse_src("app/main.py:40-58") == ("app/main.py", 40, 58)

    def test_surrounding_whitespace_is_ignored(self) -> None:
        assert check.parse_src("  app/main.py:1-2  ") == ("app/main.py", 1, 2)

    def test_windows_style_path_is_not_mistaken_for_a_range(self) -> None:
        path, start, end = check.parse_src("app/main.py")
        assert (path, start, end) == ("app/main.py", None, None)


class TestSliceLines:
    text = "a\nb\nc\nd\n"

    def test_whole_file_when_no_range(self) -> None:
        assert check.slice_lines(self.text, None, None) == ["a", "b", "c", "d"]

    def test_inclusive_one_indexed(self) -> None:
        assert check.slice_lines(self.text, 2, 3) == ["b", "c"]

    def test_past_the_end_is_rejected(self) -> None:
        assert check.slice_lines(self.text, 3, 99) is None

    def test_zero_start_is_rejected(self) -> None:
        assert check.slice_lines(self.text, 0, 2) is None

    def test_inverted_range_is_rejected(self) -> None:
        assert check.slice_lines(self.text, 3, 2) is None


class TestHashLines:
    def test_is_stable_and_truncated(self) -> None:
        digest = check.hash_lines(["def f():", "    return 1"])
        assert len(digest) == check.HASH_LENGTH
        assert digest == check.hash_lines(["def f():", "    return 1"])

    def test_differs_on_whitespace(self) -> None:
        assert check.hash_lines(["    return 1"]) != check.hash_lines(["return 1"])


class TestFindCitations:
    def test_attaches_the_citation_to_its_slide(self) -> None:
        deck = """
        <!-- 6: ARCHITECTURE -->
        <pre data-src="app/main.py:1-2" data-sha256="abc123abc123">x</pre>
        """
        (citation,) = check.find_citations(deck)
        assert citation.slide_index == 6
        assert citation.display_slide == "7"
        assert citation.slide_label == "ARCHITECTURE"
        assert citation.recorded_sha == "abc123abc123"

    def test_hyphenated_label_keeps_its_attribution(self) -> None:
        deck = '<!-- 4: RATE-LIMIT -->\n<pre data-src="a.py:1" data-sha256="abc123">x</pre>'
        (citation,) = check.find_citations(deck)
        assert citation.slide_label == "RATE-LIMIT"
        assert citation.display_slide == "5"

    def test_prose_mentioning_the_attribute_is_not_a_citation(self) -> None:
        deck = '<p>Add data-src="path:1-2" to each snippet.</p>'
        assert check.find_citations(deck) == []

    def test_citation_without_a_hash_is_still_found(self) -> None:
        (citation,) = check.find_citations('<pre data-src="a.py:1-2">x</pre>')
        assert citation.recorded_sha is None

    def test_later_slide_comment_wins(self) -> None:
        deck = '<!-- 0: TITLE -->\n<!-- 1: DEEP-DIVE -->\n<pre data-src="a.py:1" data-sha256="abc123">x</pre>'
        (citation,) = check.find_citations(deck)
        assert citation.slide_label == "DEEP-DIVE"


class TestLocateMoved:
    def test_finds_the_block_at_its_new_position(self) -> None:
        current = "import os\n\ndef f():\n    return 1\n"
        assert check.locate_moved(current, ["def f():", "    return 1"]) == (3, 4)

    def test_returns_none_when_the_block_is_gone(self) -> None:
        assert check.locate_moved("def g():\n    return 2\n", ["def f():"]) is None

    def test_returns_none_when_the_block_is_longer_than_the_file(self) -> None:
        assert check.locate_moved("one line\n", ["a", "b", "c"]) is None


class TestStaleness:
    def test_only_real_drift_counts_as_stale(self) -> None:
        def citation(status: str) -> check.Citation:
            return check.Citation(
                src="a.py",
                path="a.py",
                start=None,
                end=None,
                recorded_sha=None,
                slide_index=0,
                slide_label="X",
                status=status,
            )

        assert citation("CHANGED").is_stale
        assert citation("MOVED").is_stale
        assert citation("MISSING").is_stale
        assert not citation("CURRENT").is_stale
        assert not citation("UNVERIFIED").is_stale


class TestCitationJson:
    def _citation(self, status: str) -> check.Citation:
        return check.Citation(
            src="a.py:1-2",
            path="a.py",
            start=1,
            end=2,
            recorded_sha="abc123",
            slide_index=3,
            slide_label="X",
            status=status,
            detail="d",
            diff=["-old", "+new"],
            commits=["deadbee subject"],
            current_lines=["new"],
        )

    def test_current_citation_stays_compact(self) -> None:
        payload = self._citation("CURRENT")
        assert "diff" not in check.citation_json(payload)
        assert "current_source" not in check.citation_json(payload)

    def test_stale_citation_carries_the_repair_brief(self) -> None:
        payload = check.citation_json(self._citation("CHANGED"))
        assert payload["diff"] == ["-old", "+new"]
        assert payload["commits"] == ["deadbee subject"]
        assert payload["current_source"] == ["new"]
        assert payload["suggested_sha256"] == check.hash_lines(["new"])

    def test_moved_citation_suggests_the_new_range(self) -> None:
        citation = self._citation("MOVED")
        citation.new_range = (10, 11)
        payload = check.citation_json(citation)
        assert payload["suggested_src"] == "a.py:10-11"
        assert payload["new_range"] == [10, 11]


class TestParseBuildMeta:
    def test_reads_the_recorded_build(self) -> None:
        html = '<meta name="slideops-build" content="commit=a9c9c0d date=2026-08-24 repo=svc">'
        assert check.parse_build_meta(html) == {"commit": "a9c9c0d", "date": "2026-08-24", "repo": "svc"}

    def test_missing_meta_is_empty(self) -> None:
        assert check.parse_build_meta("<html></html>") == {}


class TestCollectDecks:
    def test_directory_skips_html_without_citations(self, tmp_path: Path) -> None:
        (tmp_path / "deck.html").write_text('<pre data-src="a.py:1" data-sha256="abc123">x</pre>')
        (tmp_path / "coverage.html").write_text("<html><body>a coverage report</body></html>")
        decks, problems = check.collect_decks([tmp_path])
        assert [d.name for d in decks] == ["deck.html"]
        assert problems == []

    def test_explicit_file_is_always_included(self, tmp_path: Path) -> None:
        plain = tmp_path / "plain.html"
        plain.write_text("<html></html>")
        decks, problems = check.collect_decks([plain])
        assert decks == [plain]
        assert problems == []

    def test_duplicates_are_collapsed(self, tmp_path: Path) -> None:
        deck = tmp_path / "deck.html"
        deck.write_text('<pre data-src="a.py:1" data-sha256="abc123">x</pre>')
        decks, _ = check.collect_decks([deck, tmp_path])
        assert len(decks) == 1

    def test_missing_target_is_reported(self, tmp_path: Path) -> None:
        decks, problems = check.collect_decks([tmp_path / "nope.html"])
        assert decks == []
        assert "not found" in problems[0]

    def test_empty_directory_is_reported(self, tmp_path: Path) -> None:
        _, problems = check.collect_decks([tmp_path])
        assert "no decks with citations" in problems[0]
