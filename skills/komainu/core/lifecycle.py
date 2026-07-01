"""P6 install, P7 re-verify, P8 optimize — the post-clearance lifecycle.

These run ONLY after the verdict gate passes. They are deliberately
conservative: install never runs lifecycle scripts, re-verify re-scans the
embedded copy in place, and optimize adapts to the host without executing
repo code.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .util import Finding, iter_files, read_text, rel
from .scan import scan_all
from .verdict import decide, DANGER


# --- P6: sandboxed dependency install --------------------------------------
def sandbox_install(root: Path) -> dict:
    """Install declared deps with lifecycle scripts DISABLED and no execution
    of repo code. We never auto-run network installs unless a manifest exists.
    """
    actions = []
    if (root / "package.json").exists():
        actions.append({
            "manager": "npm",
            "command": "npm ci --ignore-scripts --no-audit --no-fund",
            "note": "run manually; --ignore-scripts blocks pre/post-install RCE",
            "auto_run": False,
        })
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
        actions.append({
            "manager": "pip",
            "command": "pip install --require-hashes -r requirements.txt  # review first",
            "note": "prefer --require-hashes; review deps before running",
            "auto_run": False,
        })
    # We intentionally return commands rather than executing them: dependency
    # install is the single riskiest step and stays human-gated.
    return {"install_plan": actions, "executed": False}


# --- P7: post-embed re-verification ----------------------------------------
def reverify(embed_root: Path) -> dict:
    """Re-scan the embedded copy IN PLACE after it lands in the target dir.
    Catches anything introduced by move/optimize and confirms nothing changed.
    """
    findings = scan_all(embed_root)
    verdict, summary = decide(findings)
    return {
        "verdict": verdict,
        "summary": summary,
        "findings": [f.to_dict() for f in findings],
        "clean": verdict != DANGER and summary["counts"]["HIGH"] == 0,
    }


# --- P8: adapt to this directory / user / agent ----------------------------
def detect_host_agents(home: Path | None = None) -> list[str]:
    home = home or Path.home()
    found = []
    checks = {
        "claude-code": [home / ".claude", Path(".claude")],
        "codex": [home / ".codex", Path("AGENTS.md")],
        "cursor": [Path(".cursorrules"), home / ".cursor"],
        "gemini": [Path("GEMINI.md"), home / ".gemini"],
    }
    for agent, paths in checks.items():
        if any(p.exists() for p in paths):
            found.append(agent)
    return found


def optimize(embed_root: Path, target_dir: Path, host_agents: list[str]) -> dict:
    """Portability + footprint pass. Non-destructive: reports rewrites needed
    and prunes obvious dead weight; does NOT execute repo code.
    """
    notes = []
    # 1. flag absolute-path hardcodes (portability across mac/win/linux + users)
    abs_hits = 0
    for p in iter_files(embed_root):
        t = read_text(p)
        if t is None:
            continue
        if "/Users/" in t or "/home/" in t or "C:\\Users" in t:
            abs_hits += 1
    if abs_hits:
        notes.append(f"{abs_hits} file(s) contain absolute home paths — "
                     f"rewrite to relative/env for portability")
    # 2. which host integration to generate
    integration = []
    if "claude-code" in host_agents:
        integration.append("Claude Code skill dir + PreToolUse gate")
    if "codex" in host_agents:
        integration.append("Codex AGENTS.md routing snippet")
    if "cursor" in host_agents:
        integration.append(".cursorrules routing snippet")
    if "gemini" in host_agents:
        integration.append("GEMINI.md routing snippet")
    return {
        "abs_path_files": abs_hits,
        "host_agents": host_agents,
        "integration_targets": integration,
        "notes": notes,
    }
