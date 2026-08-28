# Security policy

## Reporting a vulnerability

Use GitHub's private reporting form:
**[Report a vulnerability](https://github.com/glukicov/slideops/security/advisories/new)**.
It opens a private advisory that only you and I can see, so please use it rather than a
public issue.

This is a solo project. Expect a first response in days rather than hours.

## Supported versions

The latest release. There are no maintenance branches, so a fix ships as a new version
rather than as a backport.

## What is in scope

The two shipped scripts, `skills/slideops/scripts/check.py` and `cite.py`, and the
instructions in `SKILL.md` and `references/` that tell an agent which shell commands to
run. Anything that would make a generated deck leak repository content it was told not to,
or make the build pass a path or an argument it should not, is in scope.

## Worth knowing before you report

Three properties are deliberate, and they are the ones most likely to look like findings:

- **The skills declare no `allowed-tools`.** Each agent applies its own confirmation rules
  to the shell commands the skill asks for. That is the intended behaviour, not an
  oversight.
- **Chrome keeps its sandbox.** Nothing in the skills passes `--no-sandbox`. If you find a
  path that does, that is a bug worth reporting.
- **A deck is treated as public.** The skill will not read secrets, credentials files or
  production data for slide content, redacts what it does quote, and ends the verification
  pass with a redaction scan over the HTML, the PDF, the notes and every embedded image. A
  case where content reaches a slide despite that is exactly what this form is for.
