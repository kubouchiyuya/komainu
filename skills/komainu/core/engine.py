"""Komainu engine — orchestrates the 10-phase lifecycle.

P1 intercept happens at the shim/hook layer (outside this process). This engine
runs P2..P10 for a given URL or a local path:

  P2 clone (minimal/anonymous)  -> P3 scan (5 categories) -> P4 sterilize
  -> P5 verdict gate -> [P6 install plan] -> [P7 re-verify] -> [P8 optimize]
  -> P9 activation notes -> P10 report/audit

Nothing in this module executes cloned repo content.
"""
from __future__ import annotations

import time
from pathlib import Path

from . import clone as clone_mod
from . import lifecycle
from .scan import scan_all
from .sterilize import sterilize
from .verdict import decide, one_line, DANGER, REVIEW, SAFE
from .report import write_reports
from .util import platform_info, RULESET_VERSION


def vet_path(root: Path, do_sterilize: bool = True, source: str = "") -> dict:
    """Scan (+optionally sterilize) an existing local tree."""
    findings = scan_all(root)
    verdict, summary = decide(findings)
    payload = {
        "source": source or str(root),
        "root": str(root),
        "platform": platform_info(),
        "ruleset_version": RULESET_VERSION,
        "findings": [f.to_dict() for f in findings],
        "verdict": verdict,
        "summary": summary,
    }
    if do_sterilize and (verdict != SAFE):
        ster = sterilize(root, findings)
        # re-scan after sterilize to reflect residual risk (excludes _QUARANTINE)
        findings2 = scan_all(root)
        verdict2, summary2 = decide(findings2)
        payload.update({
            "initial_verdict": verdict,       # Before
            "initial_summary": summary,       # Before
            "sterilize": ster,
            "post_sterilize_verdict": verdict2,   # After
            "post_sterilize_summary": summary2,
            "findings": [f.to_dict() for f in findings2],
            "verdict": verdict2,
            "summary": summary2,
        })
    return payload


def import_url(url: str, staging: Path, ref: str | None = None,
               keep_junk: bool = False, target_dir: Path | None = None) -> dict:
    """Full P2..P10 for a remote repo. Returns the report payload.

    Does NOT move anything into target_dir unless verdict is SAFE (or the caller
    later approves). Activation past a non-SAFE verdict is a human decision.
    """
    t0 = time.time()
    dest = staging / _slug(url)
    clone_info = clone_mod.clone(url, dest, ref=ref, keep_junk=keep_junk)

    payload = vet_path(dest, do_sterilize=True, source=url)
    payload["sha"] = clone_info.get("sha", "")
    payload["clone"] = clone_info

    verdict = payload["verdict"]
    # P6 install plan (never auto-executed)
    payload["install"] = lifecycle.sandbox_install(dest)
    # P8 optimize preview (host detection + portability)
    host_agents = lifecycle.detect_host_agents()
    payload["optimize"] = lifecycle.optimize(dest, target_dir or dest, host_agents)

    payload["activation"] = {
        "allowed": verdict == SAFE,
        "gate": verdict,
        "reason": {
            SAFE: "no static threat + nothing auto-executes; may activate "
                  "(runtime still least-privilege via sandbox install)",
            REVIEW: "medium findings — MASA approval required before activation",
            DANGER: "critical findings — import refused unless explicitly overridden",
        }[verdict],
        "note_safe_means": "SAFE != safe to run arbitrarily; use sandbox install path",
    }
    payload["elapsed_sec"] = round(time.time() - t0, 2)

    jp, mp = write_reports(dest.parent, payload)
    payload["report_json"] = str(jp)
    payload["report_md"] = str(mp)
    return payload


def _slug(url: str) -> str:
    s = url.rstrip("/").split("/")[-1]
    s = s[:-4] if s.endswith(".git") else s
    return "".join(c if (c.isalnum() or c in "-_.") else "-" for c in s) or "repo"
