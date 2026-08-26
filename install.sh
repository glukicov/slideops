#!/bin/sh
# Install the SlideOps skills for any agent that reads SKILL.md.
#
#   ./install.sh              symlink into every skills directory this machine has an agent for
#   ./install.sh --copy       copy instead of symlink (a pinned snapshot)
#   ./install.sh --dry-run    print what would happen, change nothing
#   ./install.sh --dest DIR   install into DIR only
#
# Claude Code users should prefer the plugin install, which is the only one that updates
# itself: /plugin marketplace add glukicov/slideops
#
# Two destinations cover four agents, because ~/.agents/skills is a shared convention:
#
#   ~/.claude/skills    Claude Code, and read by OpenCode too
#   ~/.agents/skills    Codex, Copilot CLI, OpenCode
#
# The skills are markdown plus two standard-library Python scripts, so there is nothing to
# build and no dependency to install. That is deliberate: an agent that can read a file and
# run `python3` can run all of this.
set -eu

SRC=$(CDPATH= cd -- "$(dirname -- "$0")/skills" && pwd)
MODE=symlink
DRY=no
DESTS="$HOME/.claude/skills $HOME/.agents/skills"

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --dry-run) DRY=yes ;;
    --dest) [ $# -ge 2 ] || { echo "--dest needs a directory" >&2; exit 2; }; DESTS="$2"; shift ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

for dest in $DESTS; do
  for skill in slideops slides-to-pdf; do
    target="$dest/$skill"
    if [ "$DRY" = yes ]; then
      echo "would $MODE $SRC/$skill -> $target"
      continue
    fi
    mkdir -p "$dest"
    rm -rf "$target"
    if [ "$MODE" = copy ]; then
      cp -R "$SRC/$skill" "$target"
    else
      ln -s "$SRC/$skill" "$target"
    fi
    echo "$MODE  $target"
  done
done

[ "$DRY" = yes ] || echo "Done. Ask your agent to make slides about a repository."
