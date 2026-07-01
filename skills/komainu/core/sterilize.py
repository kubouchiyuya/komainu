"""Sterilize: neutralize threats while preserving skill structure.

Policy (aligned with AKATSUKI rules: quarantine, never destroy; backup first):
  - Dangerous files (action=quarantine|reject) are MOVED to _QUARANTINE/,
    never deleted. A manifest records origin + reason so they can be restored.
  - Hidden unicode (action=sanitize) is stripped in place in the clean tree;
    the original stays under _QUARANTINE/originals/ for diffing.
  - Everything else is left intact.
  - After sterilizing, referenced-but-missing entrypoints are reported so a
    human sees if stripping broke the skill ("補完" = repair signal, not silent).
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .util import Finding
from .scan import _HIDDEN_RANGES


def _strip_hidden(text: str) -> tuple[str, int]:
    out = []
    removed = 0
    for ch in text:
        cp = ord(ch)
        hit = False
        for lo, hi in _HIDDEN_RANGES:
            if lo <= cp <= hi:
                hit = True
                break
        if hit:
            removed += 1
        else:
            out.append(ch)
    return "".join(out), removed


def sterilize(root: Path, findings: list[Finding]) -> dict:
    quarantine = root / "_QUARANTINE"
    originals = quarantine / "originals"
    manifest: list[dict] = []

    # de-dup targets by path+action
    move_targets: dict[str, str] = {}   # relpath -> reason
    sanitize_targets: set[str] = set()
    for f in findings:
        if not f.path:
            continue
        if f.action in ("quarantine", "reject"):
            move_targets.setdefault(f.path, f"{f.rule}: {f.message}")
        elif f.action == "sanitize":
            sanitize_targets.add(f.path)

    # 1. quarantine dangerous files (move, keep tree layout under _QUARANTINE)
    for relp, reason in sorted(move_targets.items()):
        src = root / relp
        if not src.exists():
            continue
        dst = quarantine / relp
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        manifest.append({"path": relp, "action": "quarantined", "reason": reason})

    # 2. sanitize hidden unicode in place (backup original)
    for relp in sorted(sanitize_targets):
        src = root / relp
        if not src.exists():
            continue
        try:
            text = src.read_text("utf-8")
        except Exception:
            continue
        cleaned, removed = _strip_hidden(text)
        if removed:
            bak = originals / relp
            bak.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(bak))
            src.write_text(cleaned, "utf-8")
            manifest.append({"path": relp, "action": "sanitized",
                             "reason": f"stripped {removed} hidden char(s)"})

    # 3. repair signal: SKILL.md references to files that no longer exist
    broken: list[str] = []
    skill_md = root / "SKILL.md"
    if skill_md.exists():
        t = skill_md.read_text("utf-8", "replace")
        for m in re.finditer(r"(scripts?/[\w\-./]+|core/[\w\-./]+|bin/[\w\-./]+)", t):
            ref = m.group(1).rstrip(".,)")
            if not (root / ref).exists() and not (quarantine / ref).exists():
                continue
            if (quarantine / ref).exists() and not (root / ref).exists():
                broken.append(ref)

    if manifest or broken:
        quarantine.mkdir(parents=True, exist_ok=True)
        (quarantine / "MANIFEST.json").write_text(
            json.dumps({"quarantined": manifest, "broken_references": sorted(set(broken))},
                       indent=2, ensure_ascii=False), "utf-8")

    return {
        "quarantined": len([m for m in manifest if m["action"] == "quarantined"]),
        "sanitized": len([m for m in manifest if m["action"] == "sanitized"]),
        "broken_references": sorted(set(broken)),
        "manifest": manifest,
    }
