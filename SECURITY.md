# Security Policy

Komainu is a security tool, so we take its own security seriously.

## Reporting a vulnerability

**Please do not open a public issue for a vulnerability.**

Use GitHub's private reporting: **Security → Report a vulnerability** (the
"Report a vulnerability" button on this repo's Security tab). That opens a
private advisory only the maintainer can see.

Please include:

- what the issue is and where (file / line / scanner rule),
- a minimal way to reproduce (a fixture repo or a snippet is ideal),
- the impact you see (false negative that lets a threat through, false positive,
  a bypass of the shim/hook, or a way to make Komainu execute inspected code).

You can expect an acknowledgement within a few days. Fixes for confirmed issues
are prioritized, and you'll be credited unless you prefer otherwise.

## What counts as a security issue here

- A **false negative**: a real attack pattern that Komainu marks SAFE.
- A **guard bypass**: making the PATH shim or Claude hook miss a raw
  clone/install.
- **Execution**: any path that makes Komainu run code from an inspected repo.
- **Guardrail tampering** the scanner should have caught but didn't.

## Supported versions

Komainu is pre-1.0; the latest `main` is the supported version. Pin a tag if you
need reproducibility.
