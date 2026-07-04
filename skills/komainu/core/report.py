"""Report rendering — machine-readable JSON + human Markdown."""
from __future__ import annotations

import json
from pathlib import Path

from .util import Finding, sev_rank


def to_json(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_markdown(payload: dict) -> str:
    v = payload.get("verdict", "?")
    s = payload.get("summary", {})
    c = s.get("counts", {})
    lines = [
        f"# Komainu report — {payload.get('source', '')}",
        "",
        f"- verdict: **{v}**",
        f"- sha: `{payload.get('sha', '')}`",
        f"- ruleset: `{payload.get('ruleset_version', '')}`",
        f"- counts: crit={c.get('CRITICAL',0)} high={c.get('HIGH',0)} "
        f"med={c.get('MEDIUM',0)} low={c.get('LOW',0)}",
    ]
    if payload.get("initial_verdict"):
        ic = payload.get("initial_summary", {}).get("counts", {})
        lines.append(f"- **Before -> After**: {payload['initial_verdict']} "
                     f"(crit={ic.get('CRITICAL',0)} high={ic.get('HIGH',0)}) "
                     f"-> {v}")
    ster = payload.get("sterilize") or {}
    if ster:
        lines.append(f"- quarantined: {ster.get('quarantined',0)}  "
                     f"sanitized: {ster.get('sanitized',0)}")
        if ster.get("broken_references"):
            lines.append(f"- **broken references after sterilize**: "
                         f"{', '.join(ster['broken_references'])}")
    lines += ["", "## Findings (most severe first)", ""]
    findings = payload.get("findings", [])
    findings = sorted(findings, key=lambda f: -sev_rank(f["severity"]))
    if not findings:
        lines.append("_none_")
    for f in findings:
        loc = f["path"] + (f":{f['line']}" if f.get("line") else "")
        lines.append(f"- `{f['severity']}` **{f['category']}/{f['rule']}** "
                     f"{f['message']} — {loc}"
                     + (f"  · `{f['evidence']}`" if f.get("evidence") else "")
                     + (f"  → _{f['action']}_" if f.get("action") else ""))
    return "\n".join(lines) + "\n"


def write_reports(out_dir: Path, payload: dict) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    jp = out_dir / "komainu-report.json"
    mp = out_dir / "komainu-report.md"
    jp.write_text(to_json(payload), "utf-8")
    mp.write_text(to_markdown(payload), "utf-8")
    return jp, mp
