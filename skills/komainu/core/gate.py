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
    r"\bgit\s+clone\b",
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

# allow-list: our own wrapper, localhost, and explicit bypass
_ALLOW_RE = re.compile(
    r"\bkomainu\b|localhost|127\.0\.0\.1|--komainu-ok\b",
    re.IGNORECASE)


def classify_command(command: str) -> str:
    """Return 'block' or 'allow'."""
    if not command:
        return "allow"
    if os.environ.get("KOMAINU_BYPASS") == "1":
        return "allow"  # audited elsewhere
    if _ALLOW_RE.search(command):
        return "allow"
    if _BLOCK_RE.search(command):
        return "block"
    return "allow"


def extract_url(command: str) -> str | None:
    m = re.search(r"https://[^\s'\"]+", command)
    return m.group(0) if m else None
