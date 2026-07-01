"""Verdict aggregation: findings -> SAFE / REVIEW / DANGER.

SAFE  = no known-bad static patterns AND no auto-run wiring survived.
        NOTE: SAFE means "no static threat + nothing auto-executes", NOT
        "safe to run arbitrarily". Executing imported code still needs
        least-privilege + the sandboxed install path.
REVIEW = medium-severity findings a human should approve.
DANGER = critical findings (exfil, guardrail-tamper, curl|pipe|sh, agent-file
         injection). Import is refused unless MASA explicitly overrides.
"""
from __future__ import annotations

from .util import Finding, sev_rank, SEV_CRIT, SEV_HIGH, SEV_MED

SAFE = "SAFE"
REVIEW = "REVIEW"
DANGER = "DANGER"


def decide(findings: list[Finding]) -> tuple[str, dict]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    reject = [f for f in findings if f.action == "reject"]
    if counts["CRITICAL"] > 0 or reject:
        verdict = DANGER
    elif counts["HIGH"] > 0 or counts["MEDIUM"] > 0:
        verdict = REVIEW
    else:
        verdict = SAFE

    summary = {
        "verdict": verdict,
        "counts": counts,
        "reject_count": len(reject),
        "total": len(findings),
    }
    return verdict, summary


def one_line(summary: dict) -> str:
    c = summary["counts"]
    return (f"{summary['verdict']} — crit={c['CRITICAL']} high={c['HIGH']} "
            f"med={c['MEDIUM']} low={c['LOW']} (total {summary['total']})")
