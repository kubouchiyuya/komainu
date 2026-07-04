# Changelog — 狛犬 / Komainu

Ruleset versions track the detection rules (`core/util.py: RULESET_VERSION`) so
reports and audits are pinnable and new incidents are traceable to a version.

## 0.2.0 — ruleset 2026.07.03

- **Expanded from 5 to 11 threat categories.** Added, grounded in 2025-26
  incidents:
  - Supply-chain / dependency risk (git/URL deps, registry override /
    dependency-confusion, missing lockfiles) — npm Shai-Hulud era
  - MCP tool poisoning / rug-pull (hidden instructions in tool descriptions,
    remote-fetch server commands) — OWASP MCP03:2025
  - Persistence / backdoor / reverse shell (`/dev/tcp`, `nc -e`,
    `authorized_keys`, cron / launchd / systemd)
  - Destructive payloads (`rm -rf`, fork bomb, `dd`/`mkfs`, mass delete)
  - Path traversal / zip-slip (`extractall`, `../` writes)
  - Privilege escalation (setuid, `chown root`, `sudo`)
- Reports now record `ruleset_version`.
- **Security fixes:** two guardian bypasses closed — the allowlist matched
  `komainu`/`localhost` as a substring (a hostile `…/komainu-exploit` URL slipped
  through), and `git -C <path> clone` / `--git-dir=… clone` evaded the gate.
- Docs use read-only framing; removed the source-star option.
- Test suite: 16 offline assertions (all 11 categories + gate/shim).

## 0.1.0

- Initial release: 5 categories, PATH shim + Claude Code hook, 10-phase
  lifecycle, sandboxed install, quarantine-not-delete.
