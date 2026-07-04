"""P1 gate classifier — shared by the PATH shims, the Claude hook, and the CLI.

Given a shell command string, decide whether it is a raw external
clone/install that must be routed through komainu. This is intentionally
conservative and HONEST about its limits:

  - It matches the common idioms (git clone, gh repo clone, tarball fetch,
    degit, npx, pip/cargo/go from git, curl|sh). A determined caller can
    still evade a regex gate (full paths, obfuscation) — the shim layer and
    the "never auto-execute" structure are what actually contain damage.
  - Local/first-party operations are allowed (own remotes, already-vetted
    komainu staging, localhost).
"""
from __future__ import annotations

import os
import re

# raw acquisition of external code
_BLOCK_PATTERNS = [
    r"\bgit\s+(?:-C\s+\S+\s+|--git-dir=\S+\s+)*clone\b",  # also `git -C <path> clone`
    r"\bgh\s+repo\s+clone\b",
    r"\bgit\s+submodule\s+(add|update\s+--init)",
    r"\bnpx\s+degit\b",
    r"\bdegit\b",
    r"\bpip[23]?\s+install\s+.*git\+",
    r"\bpip[23]?\s+install\s+.*https?://",
    r"\bcargo\s+install\s+--git\b",
    r"\bgo\s+install\s+\S+@",
    r"\b(curl|wget)\s+[^\n|]*\|\s*(sudo\s+)?(sh|bash|zsh|python|node|ruby|pwsh)\b",
    r"\b(curl|wget)\s+[^\n]*(github|codeload|raw\.githubusercontent)[^\n]*\|\s*(tar|unzip)",
    r"\bclaude\s+plugin\s+(install|marketplace\s+add)\b",
    r"\bnpm\s+install\s+.*(github:|git\+|https?://)",
]
_BLOCK_RE = re.compile("|".join(_BLOCK_PATTERNS), re.IGNORECASE)

# allow-list: an explicit per-command opt-out, and localhost ONLY as the host
# (matching a bare "komainu"/"localhost" substring anywhere let a hostile URL
# like .../komainu-exploit or .../localhost-repo bypass the gate). Komainu's own
# git calls are allowed via the KOMAINU_BYPASS env, not by string-matching.
_ALLOW_RE = re.compile(
    r"--komainu-ok\b|://(?:localhost|127\.0\.0\.1)[:/]",
    re.IGNORECASE)


# leading `KOMAINU_BYPASS=1` (optionally among other env assignments) — the
# documented one-time escape, honored even via the Claude hook where an inline
# env prefix would not reach os.environ.
_ENV_BYPASS_RE = re.compile(r"^\s*(?:\w+=\S*\s+)*KOMAINU_BYPASS=1(?:\s|$)")


def _blank_quoted(cmd: str) -> str:
    """Blank the CONTENTS of quoted strings so a trigger word that appears only
    inside an argument (a release note, commit message, echo) does not
    false-positive the operator's own shell. A real clone/install keeps its
    command+subcommand outside quotes, so it is still detected."""
    cmd = re.sub(r'"(?:[^"\\]|\\.)*"', '""', cmd)
    cmd = re.sub(r"'[^']*'", "''", cmd)
    return cmd


def classify_command(command: str) -> str:
    """Return 'block' or 'allow'."""
    if not command:
        return "allow"
    if os.environ.get("KOMAINU_BYPASS") == "1" or _ENV_BYPASS_RE.match(command):
        return "allow"  # audited elsewhere
    if _ALLOW_RE.search(command):
        return "allow"
    if _BLOCK_RE.search(_blank_quoted(command)):
        return "block"
    return "allow"


def extract_url(command: str) -> str | None:
    m = re.search(r"https://[^\s'\"]+", command)
    return m.group(0) if m else None
