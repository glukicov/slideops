#!/usr/bin/env python3
"""Validate the SlideOps skills, plugin manifests and template.

`skills-ref validate ./slideops` covers the frontmatter spec more thoroughly; this adds
the checks specific to this repository. Development tooling, not part of either skill.
Run `--help` for the arguments.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Annotated

import typer
import yaml

SKILLS_DIR = "skills"
SKILL_NAMES = ("slideops", "slides-to-pdf")
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_NAME = 64
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
COLOUR_RE = re.compile(r"rgba?\(|hsla?\(|oklch\(|hwb\(|#[0-9a-fA-F]{3,8}\b")

problems: list[str] = []


def fail(where: Path | str, message: str) -> None:
    problems.append(f"{where}: {message}")


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text()
    if not text.startswith("---\n"):
        fail(skill_md, "missing YAML frontmatter")
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        fail(skill_md, "frontmatter is never closed")
        return {}
    # Claude Code's loader is lenient, but ecosystem tools (npx skills, strict YAML
    # parsers) silently drop a skill whose frontmatter does not parse. Fail here instead.
    try:
        parsed = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        fail(skill_md, f"frontmatter is not strict YAML (ecosystem tools will drop this skill): {exc}")
        return {}
    if not isinstance(parsed, dict):
        fail(skill_md, "frontmatter is not a YAML mapping")
        return {}
    return {key: value if isinstance(value, str) else "" for key, value in parsed.items()}


def check_skill(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        fail(skill_dir, "no SKILL.md")
        return

    fields = parse_frontmatter(skill_md)
    name = fields.get("name", "")
    if not name:
        fail(skill_md, "frontmatter has no name")
    else:
        if len(name) > MAX_NAME or not NAME_RE.match(name):
            fail(skill_md, f"name {name!r} must be lowercase alphanumeric with single hyphens")
        if name != skill_dir.name:
            fail(skill_md, f"name {name!r} must match the directory name {skill_dir.name!r}")

    description = fields.get("description", "")
    if not description:
        fail(skill_md, "frontmatter has no description")
    elif len(description) > MAX_DESCRIPTION:
        fail(skill_md, f"description is {len(description)} chars, max {MAX_DESCRIPTION}")

    compatibility = fields.get("compatibility", "")
    if len(compatibility) > MAX_COMPATIBILITY:
        fail(skill_md, f"compatibility is {len(compatibility)} chars, max {MAX_COMPATIBILITY}")

    unknown = set(fields) - {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
    if unknown:
        fail(skill_md, f"frontmatter fields not in the spec: {sorted(unknown)}")
    if "allowed-tools" in fields:
        fail(skill_md, "allowed-tools pre-approves shell access; keep it out of the portable skill")

    for link in re.findall(r"\]\((?!https?:)([^)#]+)\)", skill_md.read_text()):
        if not (skill_dir / link).exists():
            fail(skill_md, f"broken relative link: {link}")


def check_html(path: Path, *, is_template: bool) -> None:
    html = path.read_text()

    opens = len(re.findall(r"<section class=\"slide", html))
    closes = len(re.findall(r"</section>", html))
    if opens != closes:
        fail(path, f"{opens} slide sections but {closes} </section>")
    if opens == 0:
        fail(path, "no slides found")

    divs, div_closes = len(re.findall(r"<div", html)), len(re.findall(r"</div>", html))
    if divs != div_closes:
        fail(path, f"unbalanced divs: {divs} open, {div_closes} close")

    for marker in ("<!-- SLIDES START", "<!-- SLIDES END -->"):
        if marker not in html:
            fail(path, f"missing splice marker {marker}")

    root = re.search(r"  :root\{.*?\n  \}", html, re.S)
    if not root:
        fail(path, "no :root theme block")
    else:
        body = html[: root.start()] + html[root.end() :]
        body = re.sub(r"<pre\b.*?</pre>", "", body, flags=re.S)
        body = re.sub(r"<svg\b.*?</svg>", "", body, flags=re.S)
        for line_no, line in enumerate(body.split("\n"), start=1):
            if COLOUR_RE.search(line) and "data:image" not in line:
                fail(path, f"colour literal outside the theme block (line ~{line_no}): {line.strip()[:70]}")

    if is_template:
        if "[DECK TITLE]" not in html:
            fail(path, "template lost its [DECK TITLE] placeholder")
    else:
        for placeholder in ("[DECK TITLE]", "[Slide title]", "[Section name]"):
            if placeholder in html:
                fail(path, f"unfilled placeholder {placeholder}")
        if 'class="img-placeholder"' in html:
            fail(path, "empty image slot: replace .img-placeholder with the real <img>")
        if "—" in re.sub(r"<pre.*?</pre>", "", html, flags=re.S):
            fail(path, "em dash in prose (allowed only inside verbatim snippets)")


def check_plugin_manifests(root: Path) -> None:
    """The plugin manifest is what delivers updates: users only get a new version when
    `version` changes, so a stale or malformed manifest silently strands everyone."""
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        fail(root, "missing .claude-plugin/plugin.json (needed for /plugin install)")
        return
    try:
        plugin = json.loads(manifest.read_text())
    except json.JSONDecodeError as exc:
        fail(manifest, f"invalid JSON: {exc}")
        return

    for field in ("name", "description", "version"):
        if not plugin.get(field):
            fail(manifest, f"missing required field: {field}")
    name = plugin.get("name", "")
    if name and not NAME_RE.match(name):
        fail(manifest, f"name {name!r} must be lowercase alphanumeric with single hyphens")

    version = plugin.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", str(version)):
        fail(manifest, f"version {version!r} must be semver, e.g. 1.2.0")

    skill_md = root / SKILLS_DIR / "slideops" / "SKILL.md"
    if skill_md.is_file() and version:
        match = re.search(r"^\s+version:\s*(\S+)\s*$", skill_md.read_text(), re.M)
        if match and match.group(1) != version:
            fail(manifest, f"version {version} does not match SKILL.md metadata.version {match.group(1)}")

    market = root / ".claude-plugin" / "marketplace.json"
    if not market.is_file():
        fail(root, "missing .claude-plugin/marketplace.json (needed for /plugin marketplace add)")
        return
    try:
        marketplace = json.loads(market.read_text())
    except json.JSONDecodeError as exc:
        fail(market, f"invalid JSON: {exc}")
        return
    if not marketplace.get("name"):
        fail(market, "missing required field: name")
    if not isinstance(marketplace.get("owner"), dict) or not marketplace["owner"].get("name"):
        fail(market, "owner must be an object with a name")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or not entries:
        fail(market, "plugins must be a non-empty array")
        return
    for entry in entries:
        if not entry.get("name") or not entry.get("source"):
            fail(market, f"plugin entry needs name and source: {entry}")
        source = str(entry.get("source", ""))
        if source.startswith("./") and not (root / source).is_dir():
            fail(market, f"plugin source does not exist: {source}")
        if entry.get("name") and name and entry["name"] != name:
            fail(market, f"entry name {entry['name']!r} does not match plugin.json name {name!r}")


app = typer.Typer(rich_markup_mode="markdown", add_completion=False)


@app.command()
def main(
    repo_root: Annotated[
        Path | None,
        typer.Argument(help="Repository to validate. Defaults to the one this script lives in."),
    ] = None,
) -> None:
    """Check the skills, the plugin manifests and the template, one line per problem.

    Covers the Agent Skills frontmatter contract, the plugin and marketplace manifests
    that carry updates to installed users, the template's structural invariants, and the
    theming invariant that every colour lives in the :root block.

    Exits non-zero if anything fails, so it can gate a commit or a release.
    """
    root = repo_root.resolve() if repo_root is not None else Path(__file__).resolve().parent.parent

    check_plugin_manifests(root)

    for skill in SKILL_NAMES:
        skill_dir = root / SKILLS_DIR / skill
        if skill_dir.is_dir():
            check_skill(skill_dir)
        else:
            fail(root, f"missing skill directory: {SKILLS_DIR}/{skill}")

    template = root / SKILLS_DIR / "slideops" / "assets" / "template.html"
    if template.is_file():
        check_html(template, is_template=True)
    else:
        fail(root, f"missing {SKILLS_DIR}/slideops/assets/template.html")

    for deck in sorted((root / SKILLS_DIR / "slideops" / "examples").glob("*.html")):
        check_html(deck, is_template=False)

    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        raise typer.Exit(1)

    print("OK: skills, plugin manifests, template, and example decks pass")


if __name__ == "__main__":
    app()
