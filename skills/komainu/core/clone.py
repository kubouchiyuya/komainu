"""P2 — minimal, anonymous, non-executing clone.

Defenses baked into the clone itself (before any scan runs):
  - HTTPS only, never fork/star/push (read-only fetch).
  - core.hooksPath=/dev/null, no submodule recursion, symlinks off.
  - --no-checkout first, so .gitattributes/.gitmodules are inspected BEFORE
    any content filter can run; then checkout with lfs/filters neutralized.
  - GIT_TERMINAL_PROMPT=0 so a hostile URL can't hang on a credential prompt.
  - .git history dropped from the working copy (context-pollution + remote link).
  - junk (CHANGELOG, CI, images, lockfiles) excluded to cut context footprint.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from .util import JUNK_GLOBS, matches_any, rel, iter_files

_URL_RE = re.compile(r"^(https://[^\s]+?)(?:\.git)?/?$", re.IGNORECASE)


def normalize_url(url: str) -> str:
    """Force HTTPS. Reject ssh/git/file schemes to keep clones anonymous & safe."""
    url = url.strip()
    if url.startswith(("git@", "ssh://", "git://", "file://")):
        raise ValueError(f"refusing non-HTTPS scheme (breaks anonymity/safety): {url}")
    m = _URL_RE.match(url)
    if not m:
        raise ValueError(f"not an https repo url: {url}")
    return m.group(1)


def _git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update({
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LFS_SKIP_SMUDGE": "1",
        # Komainu's own git is the sanctioned path — let it pass the PATH shim.
        "KOMAINU_BYPASS": "1",
    })
    return subprocess.run(
        ["git"] + args, cwd=str(cwd) if cwd else None,
        env=env, capture_output=True, text=True, timeout=300,
    )


def clone(url: str, dest: Path, ref: str | None = None, keep_junk: bool = False) -> dict:
    url = normalize_url(url)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    safe_cfg = [
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.symlinks=false",
        "-c", "core.fsmonitor=false",
        "-c", "protocol.ext.allow=never",
        "-c", "filter.lfs.smudge=",
        "-c", "filter.lfs.process=",
        "-c", "filter.lfs.required=false",
    ]
    # 1. clone without checkout (no submodules, shallow)
    cp = _git(safe_cfg + ["clone", "--no-checkout", "--depth", "1",
                          "--no-recurse-submodules", url, str(dest)])
    if cp.returncode != 0:
        raise RuntimeError(f"git clone failed: {cp.stderr.strip()[:400]}")

    # 2. record the pinned commit (SHA pinning / TOCTOU)
    head = _git(["rev-parse", "HEAD"], cwd=dest)
    sha = head.stdout.strip() if head.returncode == 0 else ""

    # 3. detect .gitattributes filter drivers BEFORE checkout. After --no-checkout
    #    the working tree is empty, so read the blob via `git show` (not the disk).
    #    Undefined filter drivers cannot execute without a matching git config
    #    entry (config is never fetched by clone) and lfs smudge/process are
    #    disabled in safe_cfg; the checked-out .gitattributes is additionally
    #    quarantined by the scanner (scan_exec_vectors 2b).
    ga_had_filters = False
    show = _git(["show", "HEAD:.gitattributes"], cwd=dest)
    if show.returncode == 0 and re.search(r"(filter|clean|smudge|process)\s*=", show.stdout):
        ga_had_filters = True

    # 4. checkout with filters disabled
    co = _git(safe_cfg + ["checkout", "HEAD", "--", "."], cwd=dest)
    if co.returncode != 0:
        # fall back to reset (still no filters)
        _git(safe_cfg + ["reset", "--hard", "HEAD"], cwd=dest)

    # 5. drop .git (removes remote link + history from working copy)
    gitdir = dest / ".git"
    if gitdir.exists():
        shutil.rmtree(gitdir, ignore_errors=True)

    # 6. junk exclusion (minimal import / context footprint)
    dropped = 0
    if not keep_junk:
        for p in list(iter_files(dest)):
            if matches_any(rel(p, dest), JUNK_GLOBS):
                try:
                    p.unlink()
                    dropped += 1
                except OSError:
                    pass

    return {"url": url, "sha": sha, "dest": str(dest),
            "gitattributes_filters_detected": ga_had_filters,
            "junk_dropped": dropped}
