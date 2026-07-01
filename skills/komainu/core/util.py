"""Komainu core utilities — stdlib only, cross-platform (mac/win/linux).

Shared helpers: platform info, hashing, file walking, text detection,
severity model, and the Finding record used across every scanner.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import platform
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Iterator

# --- severity model ---------------------------------------------------------
# Ordered low -> high. Verdict aggregation depends on this ordering.
SEV_INFO = "INFO"
SEV_LOW = "LOW"
SEV_MED = "MEDIUM"
SEV_HIGH = "HIGH"
SEV_CRIT = "CRITICAL"
SEV_ORDER = [SEV_INFO, SEV_LOW, SEV_MED, SEV_HIGH, SEV_CRIT]


def sev_rank(sev: str) -> int:
    return SEV_ORDER.index(sev) if sev in SEV_ORDER else 0


# Category ids (map to threat-model.md sections).
CAT_INJECTION = "injection"          # prompt-injection / hidden unicode
CAT_EXEC = "exec_vector"             # auto-run on clone/install/open
CAT_EXFIL = "exfil"                  # outbound data flow
CAT_MALWARE = "malware_obfuscation"  # virus-like / obfuscation / secrets
CAT_SELFDEFENSE = "guardrail_tamper" # edits to guardrails / komainu itself


@dataclass
class Finding:
    category: str
    severity: str
    rule: str
    message: str
    path: str = ""
    line: int = 0
    evidence: str = ""
    action: str = ""  # what sterilize did / should do: quarantine|sanitize|flag|reject

    def to_dict(self) -> dict:
        return asdict(self)


# --- platform ---------------------------------------------------------------
def platform_info() -> dict:
    return {
        "system": platform.system(),          # Darwin | Linux | Windows
        "release": platform.release(),
        "python": sys.version.split()[0],
        "is_windows": os.name == "nt",
    }


def which(name: str) -> str | None:
    from shutil import which as _which
    return _which(name)


# --- hashing ----------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


# --- file walking -----------------------------------------------------------
# Directories never worth scanning for threats (but .git IS inspected separately).
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
             "_QUARANTINE"}

# Extensions treated as binary (opaque -> flagged, not text-scanned).
BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
               ".zip", ".gz", ".tar", ".tgz", ".bz2", ".xz", ".7z", ".rar",
               ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp3", ".mp4",
               ".mov", ".avi", ".wasm", ".so", ".dylib", ".dll", ".exe",
               ".bin", ".o", ".a", ".class", ".jar", ".pyc"}

MAX_TEXT_BYTES = 4 * 1024 * 1024  # skip reading files larger than 4 MB as text


def iter_files(root: Path, include_git: bool = False) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # prune skip dirs (keep .git only if asked)
        pruned = []
        for name in list(dirnames):
            if name == ".git" and include_git:
                continue
            if name in SKIP_DIRS:
                pruned.append(name)
        for name in pruned:
            dirnames.remove(name)
        for fn in filenames:
            yield d / fn


def is_binary_path(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTS:
        return True
    return False


def read_text(path: Path) -> str | None:
    """Read a file as text, or None if binary/too big/unreadable."""
    try:
        if path.is_symlink():
            return None
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
    except OSError:
        return None
    if is_binary_path(path):
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    # NUL byte -> binary
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1")
        except Exception:
            return None


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# --- junk / minimal-import policy ------------------------------------------
# Patterns dropped at clone time to cut context-pollution footprint.
JUNK_GLOBS = [
    ".git", ".github/workflows/*", "CHANGELOG*", "*.png", "*.jpg", "*.jpeg",
    "*.gif", "*.webp", "*.pdf", "*.mp4", "*.mov", "docs/**/*.png",
    ".DS_Store", "*.lock",
]


def matches_any(relpath: str, globs: Iterable[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(relpath, g) or fnmatch.fnmatch(os.path.basename(relpath), g):
            return True
    return False
