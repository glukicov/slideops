#!/usr/bin/env python3
"""slideops cite: produce the citation attributes for a snippet, and stamp the build commit.

The companion to check.py. `check` tells you what drifted; `cite` is what you use while
building or repairing a slide, so the two attributes that make a snippet checkable are
never typed by hand:

    python3 cite.py app/main.py:40-58 [more...] [--repo PATH] [--snippet] [--md]
    python3 cite.py --stamp docs/slides/deck.html [--repo PATH]

With --md the citation prints as the comment form used in Markdown docs, --snippet prints
a fenced block instead of escaped HTML, and --stamp on a .md file writes the comment stamp
onto line 1.

A hand-computed hash is worse than no hash: it reports UNVERIFIED or CHANGED months later
and nobody can tell whether the code moved or the build was sloppy. Same for the build
date, which an agent will otherwise cheerfully invent.

Exit codes: 0 fine, 1 a reference could not be resolved, 2 the repo or deck is unreadable.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import re
import subprocess
import sys
from pathlib import Path

HASH_LENGTH = 12
BUILD_META_RE = re.compile(r'<meta name="slideops-build" content="[^"]*">', re.I)
MD_BUILD_META_RE = re.compile(r"\A<!--\s*slideops-build[^>]*-->[ \t]*\n?", re.I)
HEAD_RE = re.compile(r"<head[^>]*>", re.I)
HALF_WIDTH, FULL_WIDTH = 65, 95
MD_SUFFIXES = {".md", ".markdown"}
FENCE_LANGS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".sh": "bash",
    ".bash": "bash",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".md": "markdown",
    ".markdown": "markdown",
}


def git(repo: Path, *args: str) -> str | None:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)
    return result.stdout.strip() if result.returncode == 0 else None


def parse_ref(ref: str) -> tuple[str, int | None, int | None]:
    """'app/main.py:40-58' -> ('app/main.py', 40, 58). Range is optional."""
    match = re.match(r"^(?P<path>.+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$", ref.strip())
    if not match:
        return ref.strip(), None, None
    start = int(match.group("start")) if match.group("start") else None
    end = int(match.group("end")) if match.group("end") else start
    return match.group("path"), start, end


def fence_for(lines: list[str]) -> str:
    """A backtick fence one longer than any backtick run in the content, minimum three."""
    longest_run = max((len(m) for line in lines for m in re.findall(r"`+", line)), default=0)
    return "`" * max(3, longest_run + 1)


def cite_one(ref: str, repo: Path, show_snippet: bool, markdown: bool = False) -> bool:
    path, start, end = parse_ref(ref)
    file_path = repo / path
    if not file_path.is_file():
        print(f"{ref}: no such file under {repo}", file=sys.stderr)
        return False

    lines = file_path.read_text(errors="replace").splitlines()
    if start is None:
        selected, src = lines, path
    else:
        if end is None or start < 1 or end > len(lines) or start > end:
            print(f"{ref}: file has {len(lines)} lines; that range does not exist", file=sys.stderr)
            return False
        selected, src = lines[start - 1 : end], f"{path}:{start}-{end}"

    digest = hashlib.sha256("\n".join(selected).encode("utf-8")).hexdigest()[:HASH_LENGTH]
    attributes = f'data-src="{src}" data-sha256="{digest}"'
    print(f"<!-- slideops {attributes} -->" if markdown else attributes)

    if not markdown:
        # The width budgets are slide-pattern constraints; fenced Markdown scrolls instead.
        longest = max((len(line) for line in selected), default=0)
        if longest > FULL_WIDTH:
            print(
                f"  warning: longest line is {longest} chars; over the ~{FULL_WIDTH} full-width budget",
                file=sys.stderr,
            )
        elif longest > HALF_WIDTH:
            print(f"  note: longest line is {longest} chars; needs a full-width pre (~{FULL_WIDTH})", file=sys.stderr)

    if show_snippet:
        if markdown:
            fence = fence_for(selected)
            print(fence + FENCE_LANGS.get(file_path.suffix.lower(), ""))
            for line in selected:
                print(line)
            print(fence)
        else:
            print()
            for line in selected:
                print(html.escape(line))
    return True


def stamp(deck: Path, repo: Path) -> int:
    """Write the build provenance meta, which is what lets check.py diff against the past."""
    if not deck.is_file():
        print(f"Deck not found: {deck}", file=sys.stderr)
        return 2

    commit = git(repo, "rev-parse", "--short", "HEAD")
    if not commit:
        print(f"Not a git repository (or no commits): {repo}", file=sys.stderr)
        return 2
    if git(repo, "status", "--porcelain"):
        print("  note: the repo has uncommitted changes; check.py can only diff against the commit", file=sys.stderr)

    name = (git(repo, "rev-parse", "--show-toplevel") or str(repo)).rsplit("/", 1)[-1]
    today = datetime.date.today().isoformat()
    payload = f"commit={commit} date={today} repo={name}"

    text = deck.read_text()
    if deck.suffix.lower() in MD_SUFFIXES:
        # The stamp owns line 1 of a Markdown doc; a stamp-shaped example deeper in the
        # file (say, inside a code fence) is content and must never be rewritten.
        meta = f"<!-- slideops-build {payload} -->"
        if MD_BUILD_META_RE.match(text):
            text, action = MD_BUILD_META_RE.sub(meta + "\n", text, count=1), "updated"
        else:
            text, action = meta + "\n" + text, "inserted"
        deck.write_text(text)
        print(f"{action}: {meta}")
        return 0

    meta = f'<meta name="slideops-build" content="{payload}">'
    if BUILD_META_RE.search(text):
        text = BUILD_META_RE.sub(meta, text, count=1)
        action = "updated"
    else:
        head = HEAD_RE.search(text)
        if not head:
            print(f"{deck}: no <head> to insert the build meta into", file=sys.stderr)
            return 1
        text = text[: head.end()] + "\n" + meta + text[head.end() :]
        action = "inserted"

    deck.write_text(text)
    print(f"{action}: {meta}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Print citation attributes, or stamp a deck's build commit.")
    parser.add_argument("refs", nargs="*", help="path:start-end references to cite")
    parser.add_argument("--repo", type=Path, default=Path(), help="repository the deck cites (default: cwd)")
    parser.add_argument("--snippet", action="store_true", help="also print the HTML-escaped source, ready to paste")
    parser.add_argument("--md", action="store_true", help="print Markdown citation comments (and fenced snippets)")
    parser.add_argument("--stamp", type=Path, metavar="DECK", help="write the build commit meta into this deck")
    args = parser.parse_args(argv[1:])

    repo: Path = args.repo.resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}", file=sys.stderr)
        return 2

    if args.stamp:
        code = stamp(args.stamp, repo)
        if code or not args.refs:
            return code

    if not args.refs:
        parser.print_usage(sys.stderr)
        print("Give at least one path:start-end reference, or --stamp DECK.", file=sys.stderr)
        return 2

    return 0 if all([cite_one(ref, repo, args.snippet, markdown=args.md) for ref in args.refs]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
