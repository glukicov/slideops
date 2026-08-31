"""End-to-end tests: does the tooling detect the drift a real repository produces?

Each test builds a throwaway git repository, cites a snippet the way the skill does, then
makes one kind of change a real codebase makes (shift the lines, edit the logic, delete the
file) and asserts the status reported. The claim these skills make is that a document can
prove whether it still matches the code, so the prover needs its own test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

CHECK = Path(__file__).resolve().parent.parent / "skills" / "slideops" / "scripts" / "check.py"
CITE = Path(__file__).resolve().parent.parent / "skills" / "slideops" / "scripts" / "cite.py"

SOURCE = """def helper():
    return 1


def rate_limit(requests, window):
    allowance = requests / window
    return allowance > 1


def unused():
    pass
"""


@dataclass
class DeckRepo:
    """A repository with one document citing lines 5-7 of app.py, built at HEAD.

    The document is either an HTML deck or a Markdown doc: the two citation carriers
    share the whole freshness lifecycle, so every drift scenario runs against both.
    """

    root: Path
    deck: Path
    citation: str
    kind: str = "html"
    expected_location: str = "5"

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def rewrite_source(self, text: str, message: str) -> None:
        (self.root / "app.py").write_text(text)
        self.git("commit", "-qam", message)

    def source(self) -> str:
        return (self.root / "app.py").read_text()

    def run_check(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECK), str(self.deck), "--repo", str(self.root), *extra],
            capture_output=True,
            text=True,
        )

    def citations(self, *extra: str) -> list[dict[str, Any]]:
        result = self.run_check("--json", *extra)
        payload = json.loads(result.stdout)
        return [c for deck in payload["decks"] for c in deck["citations"]]

    def only(self, *extra: str) -> dict[str, Any]:
        found = self.citations(*extra)
        assert len(found) == 1
        return found[0]

    def set_citation(self, attributes: str) -> None:
        carrier = f"<!-- slideops {attributes} -->" if self.kind == "md" else attributes
        self.deck.write_text(self.deck.read_text().replace(self.citation, carrier))
        self.citation = carrier

    def restamp(self) -> None:
        subprocess.run(
            [sys.executable, str(CITE), "--stamp", str(self.deck), "--repo", str(self.root)],
            check=True,
            capture_output=True,
        )


@pytest.fixture(params=["html", "md"])
def deck_repo(request: pytest.FixtureRequest, tmp_path: Path) -> DeckRepo:
    kind: str = request.param
    root = tmp_path / "repo"
    root.mkdir()
    (root / "app.py").write_text(SOURCE)
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "test@example.com"),
        ("config", "user.name", "Test"),
        ("add", "-A"),
        ("commit", "-qm", "initial"),
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

    cite_args = ["app.py:5-7", "--repo", str(root)] + (["--md"] if kind == "md" else [])
    cited = subprocess.run(
        [sys.executable, str(CITE), *cite_args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    if kind == "md":
        deck = root / "docs" / "slides" / "doc.md"
        deck.parent.mkdir(parents=True)
        deck.write_text(f"# Guide\n\n## RATE-LIMIT\n\n{cited}\n```python\nsnippet\n```\n")
        # Headings are the anchors: "# Guide" is 0, "## RATE-LIMIT" is 1, displayed as 2.
        repo = DeckRepo(root=root, deck=deck, citation=cited, kind="md", expected_location="2")
    else:
        deck = root / "docs" / "slides" / "deck.html"
        deck.parent.mkdir(parents=True)
        deck.write_text(
            f"<html><head>\n</head><body>\n<!-- 4: RATE-LIMIT -->\n<pre {cited}>snippet</pre>\n</body></html>\n"
        )
        repo = DeckRepo(root=root, deck=deck, citation=cited)
    repo.restamp()
    return repo


def test_a_freshly_built_deck_is_current(deck_repo: DeckRepo) -> None:
    citation = deck_repo.only()
    assert citation["status"] == "CURRENT"
    assert deck_repo.run_check().returncode == 0


def test_slide_attribution_survives_a_hyphenated_label(deck_repo: DeckRepo) -> None:
    citation = deck_repo.only()
    assert citation["slide"] == deck_repo.expected_location
    assert citation["label"] == "RATE-LIMIT"


def test_a_directory_sweep_finds_the_deck(deck_repo: DeckRepo) -> None:
    (deck_repo.deck.parent / "README.md").write_text("# Companion readme\n\nNo citations, must be skipped.\n")
    result = subprocess.run(
        [sys.executable, str(CHECK), "docs/slides", "--repo", str(deck_repo.root), "--json"],
        cwd=deck_repo.root,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["checked"] == 1
    assert payload["stale"] == 0
    assert payload["decks"][0]["kind"] == ("doc" if deck_repo.kind == "md" else "deck")


def test_shifted_lines_report_moved_with_the_new_range(deck_repo: DeckRepo) -> None:
    deck_repo.rewrite_source("import os\nimport sys\n\n\n" + SOURCE, "add imports")
    citation = deck_repo.only()
    assert citation["status"] == "MOVED"
    assert citation["new_range"] == [9, 11]
    assert deck_repo.run_check().returncode == 1


def test_exit_zero_keeps_a_report_only_job_green(deck_repo: DeckRepo) -> None:
    deck_repo.rewrite_source("import os\nimport sys\n\n\n" + SOURCE, "add imports")
    assert deck_repo.run_check("--exit-zero").returncode == 0


def test_quiet_is_silent_while_everything_is_current(deck_repo: DeckRepo) -> None:
    assert deck_repo.run_check("--quiet").stdout.strip() == ""


def test_applying_the_suggested_fix_makes_the_deck_current(deck_repo: DeckRepo) -> None:
    deck_repo.rewrite_source("import os\nimport sys\n\n\n" + SOURCE, "add imports")
    moved = deck_repo.only()
    deck_repo.set_citation(f'data-src="{moved["suggested_src"]}" data-sha256="{moved["suggested_sha256"]}"')
    deck_repo.restamp()
    assert deck_repo.only()["status"] == "CURRENT"
    assert deck_repo.run_check().returncode == 0


def test_edited_logic_reports_changed_with_a_diff_and_the_commit(deck_repo: DeckRepo) -> None:
    deck_repo.rewrite_source(deck_repo.source().replace("allowance > 1", "allowance > 2"), "raise the threshold")
    citation = deck_repo.only()
    assert citation["status"] == "CHANGED"
    assert any("raise the threshold" in commit for commit in citation["commits"])
    assert any(line.startswith("+") and "allowance > 2" in line for line in citation["diff"])


def test_a_deleted_file_reports_missing(deck_repo: DeckRepo) -> None:
    (deck_repo.root / "app.py").unlink()
    deck_repo.git("commit", "-qam", "delete app.py")
    assert deck_repo.only()["status"] == "MISSING"


def test_a_snippet_without_a_hash_is_unverified(deck_repo: DeckRepo) -> None:
    deck_repo.set_citation('data-src="app.py:5-7"')
    citation = deck_repo.only()
    assert citation["status"] == "UNVERIFIED"
    assert deck_repo.run_check().returncode == 0


@pytest.mark.parametrize("example", ["skill-demo.html", "skill-demo.md"])
def test_the_examples_still_match_this_repository(example: str) -> None:
    """The demo deck and doc are built by the skill, so their citations are a live regression test."""
    root = Path(__file__).resolve().parent.parent
    target = root / "skills" / "slideops" / "examples" / example
    result = subprocess.run(
        [sys.executable, str(CHECK), str(target), "--repo", str(root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
