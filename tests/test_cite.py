"""Unit tests for the citation writer.

The point of cite.py is that no hash and no build date is ever typed by hand, so these
check that it produces exactly what check.py will later verify, and that it refuses rather
than guesses when a reference does not resolve.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import check
import cite

SOURCE = "def helper():\n    return 1\n\n\ndef rate_limit(n):\n    return n * 2\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway git repository with one committed source file."""
    (tmp_path / "app.py").write_text(SOURCE)
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "test@example.com"),
        ("config", "user.name", "Test"),
        ("add", "-A"),
        ("commit", "-qm", "initial"),
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    return tmp_path


class TestParseRef:
    def test_range(self) -> None:
        assert cite.parse_ref("app/main.py:40-58") == ("app/main.py", 40, 58)

    def test_single_line(self) -> None:
        assert cite.parse_ref("app/main.py:7") == ("app/main.py", 7, 7)

    def test_no_range(self) -> None:
        assert cite.parse_ref("app/main.py") == ("app/main.py", None, None)


class TestCiteOne:
    def test_emits_attributes_check_will_accept(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert cite.cite_one("app.py:5-6", repo, show_snippet=False) is True
        printed = capsys.readouterr().out.strip()
        expected = check.hash_lines(SOURCE.splitlines()[4:6])
        assert printed == f'data-src="app.py:5-6" data-sha256="{expected}"'

    def test_whole_file_citation_has_no_range(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert cite.cite_one("app.py", repo, show_snippet=False) is True
        assert 'data-src="app.py"' in capsys.readouterr().out

    def test_snippet_is_html_escaped(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (repo / "generic.py").write_text("items: list[int] = []\nif a < b and c > d:\n    pass\n")
        cite.cite_one("generic.py:2", repo, show_snippet=True)
        out = capsys.readouterr().out
        assert "&lt;" in out and "&gt;" in out
        assert "if a < b" not in out

    def test_missing_file_fails(self, repo: Path) -> None:
        assert cite.cite_one("nope.py:1-2", repo, show_snippet=False) is False

    def test_range_past_the_end_fails(self, repo: Path) -> None:
        assert cite.cite_one("app.py:900-901", repo, show_snippet=False) is False

    def test_warns_when_lines_are_too_wide(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (repo / "wide.py").write_text("x = '" + "y" * 200 + "'\n")
        cite.cite_one("wide.py:1", repo, show_snippet=False)
        assert "full-width budget" in capsys.readouterr().err


class TestCiteMarkdown:
    def test_md_flag_prints_a_ready_to_paste_comment(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert cite.cite_one("app.py:5-6", repo, show_snippet=False, markdown=True) is True
        printed = capsys.readouterr().out.strip()
        expected = check.hash_lines(SOURCE.splitlines()[4:6])
        assert printed == f'<!-- slideops data-src="app.py:5-6" data-sha256="{expected}" -->'

    def test_md_snippet_is_fenced_with_the_language_and_not_escaped(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (repo / "generic.py").write_text("items: list[int] = []\nif a < b and c > d:\n    pass\n")
        cite.cite_one("generic.py:2", repo, show_snippet=True, markdown=True)
        out = capsys.readouterr().out
        assert "```python\n" in out
        assert out.rstrip().endswith("```")
        assert "if a < b" in out
        assert "&lt;" not in out

    def test_fence_grows_past_backtick_runs_in_the_source(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (repo / "notes.md").write_text("Use a fence:\n```\ncode\n```\n")
        cite.cite_one("notes.md", repo, show_snippet=True, markdown=True)
        out = capsys.readouterr().out
        assert "````markdown\n" in out
        assert out.rstrip().endswith("````")

    def test_unknown_extension_gets_a_bare_fence(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (repo / "data.xyz").write_text("payload\n")
        cite.cite_one("data.xyz:1", repo, show_snippet=True, markdown=True)
        assert "```\npayload\n```" in capsys.readouterr().out

    def test_md_suppresses_width_warnings(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (repo / "wide.py").write_text("x = '" + "y" * 200 + "'\n")
        cite.cite_one("wide.py:1", repo, show_snippet=False, markdown=True)
        assert capsys.readouterr().err == ""


class TestStampMarkdown:
    def test_inserts_the_stamp_as_the_first_line(self, repo: Path) -> None:
        doc = repo / "doc.md"
        doc.write_text("# Title\n\nBody.\n")
        assert cite.stamp(doc, repo) == 0
        first, rest = doc.read_text().split("\n", 1)
        assert first.startswith("<!-- slideops-build commit=")
        assert first.endswith(" -->")
        assert rest == "# Title\n\nBody.\n"

    def test_restamp_replaces_line_one_without_duplicating(self, repo: Path) -> None:
        doc = repo / "doc.md"
        doc.write_text("<!-- slideops-build commit=old date=2020-01-01 repo=old -->\n# Title\n")
        assert cite.stamp(doc, repo) == 0
        text = doc.read_text()
        assert text.count("slideops-build") == 1
        assert "commit=old" not in text
        assert "# Title" in text

    def test_a_fenced_example_stamp_is_left_alone(self, repo: Path) -> None:
        example = "```markdown\n<!-- slideops-build commit=fffffff date=1999-01-01 repo=fake -->\n```\n"
        doc = repo / "doc.md"
        doc.write_text("# Title\n\n" + example)
        assert cite.stamp(doc, repo) == 0
        text = doc.read_text()
        assert text.startswith("<!-- slideops-build commit=")
        assert "commit=fffffff" in text
        assert text.count("slideops-build") == 2


class TestStamp:
    def test_inserts_into_a_deck_with_no_meta(self, repo: Path) -> None:
        deck = repo / "deck.html"
        deck.write_text("<html><head>\n<title>x</title>\n</head><body></body></html>\n")
        assert cite.stamp(deck, repo) == 0
        text = deck.read_text()
        assert '<meta name="slideops-build"' in text
        assert text.index("slideops-build") < text.index("<title>")

    def test_replaces_an_existing_meta_without_duplicating(self, repo: Path) -> None:
        deck = repo / "deck.html"
        deck.write_text(
            '<html><head>\n<meta name="slideops-build" content="commit=old date=2020-01-01 repo=old">\n'
            "</head><body></body></html>\n"
        )
        assert cite.stamp(deck, repo) == 0
        text = deck.read_text()
        assert text.count("slideops-build") == 1
        assert "commit=old" not in text

    def test_records_the_real_head_commit(self, repo: Path) -> None:
        deck = repo / "deck.html"
        deck.write_text("<html><head></head><body></body></html>\n")
        cite.stamp(deck, repo)
        head = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert f"commit={head}" in deck.read_text()

    def test_missing_deck_is_an_error(self, repo: Path) -> None:
        assert cite.stamp(repo / "nope.html", repo) == 2

    def test_deck_without_a_head_element_is_reported(self, repo: Path) -> None:
        deck = repo / "fragment.html"
        deck.write_text("<div>no head here</div>\n")
        assert cite.stamp(deck, repo) == 1
