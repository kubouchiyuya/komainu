# How Komainu works

## The 10-phase lifecycle

Every import runs the same pipeline. Phases P2–P5 touch **no** running code;
execution only ever happens in the sandboxed, human-gated install (P6).

| Phase | What happens | Runs code? |
|---|---|---|
| **P1 Intercept** | PATH shim / Claude hook catches a raw clone/install and routes it here | no |
| **P2 Clone** | read-only HTTPS, `--no-checkout` → inspect `.gitattributes`/`.gitmodules` *first* → checkout with filters & hooks disabled → drop `.git` → drop junk → pin the commit SHA | no |
| **P3 Scan** | all 5 threat categories (below) | no |
| **P4 Sterilize** | move dangerous files to `_QUARANTINE/`, strip hidden unicode, report broken references | no |
| **P5 Verdict** | SAFE / REVIEW / DANGER gate | no |
| **P6 Install** | dependencies with `--ignore-scripts`, no network, human-gated | sandboxed |
| **P7 Re-verify** | re-scan the embedded copy *in place* after it lands | verify |
| **P8 Optimize** | rewrite absolute paths, prune footprint, detect host agent, generate integration | verify |
| **P9 Activate** | register the skill/plugin, generate usage | — |
| **P10 Audit** | record SAFE@SHA, remember known-bad hashes | — |

## The 11 threat categories

1. **Prompt injection / hidden content** — AI-directed instructions (English,
   Japanese, Chinese), zero-width & bidi & tag unicode, hidden markup, and
   payloads buried in agent-instruction files.
2. **Auto-run vectors** — `.gitattributes` filter drivers, submodules, git
   hooks, npm/pip lifecycle scripts, Claude Code hooks, `.vscode/tasks.json`,
   `.devcontainer`, `.envrc`, `sitecustomize.py`/`*.pth`, `conftest.py`,
   `build.rs`, shell rc files.
3. **Exfiltration** — `curl … | sh`, files that read secrets *and* have network
   egress, outbound POST/PUT.
4. **Malware / obfuscation** — dynamic code evaluation, base64 payloads, opaque
   binaries, committed secrets.
5. **Guardrail tampering** — writes to your `settings.json`, `CLAUDE.md`,
   `AGENTS.md`, hooks, or Komainu itself (disable-the-guardian).
6. **Supply-chain / dependency risk** — deps from git/URL/file sources,
   registry overrides (dependency-confusion), missing lockfiles.
7. **MCP tool poisoning** — hidden instructions in MCP tool descriptions and
   remote-fetch server commands (OWASP MCP03; rug-pull surface).
8. **Persistence / backdoor** — reverse shells (`/dev/tcp`, `nc -e`),
   `authorized_keys` writes, cron / launchd / systemd, shell-rc appends.
9. **Destructive payloads** — `rm -rf` of broad paths, fork bombs, disk wipes
   (`dd`/`mkfs`), mass delete.
10. **Path traversal / zip-slip** — `extractall` without validation, writes to
    `../` paths.
11. **Privilege escalation** — setuid bits, `setuid()`, `chown root`, `sudo`.

Full taxonomy and residual-risk analysis: [../references/threat-model.md](../references/threat-model.md).

## How enforcement fires — for every AI, every OS

| Layer | Covers | Guarantee |
|---|---|---|
| **PATH shim** (`shims/`) | any agent that shells out — Claude Code, OpenAI Codex, Grok, Cursor, Aider, Gemini CLI, humans — on macOS/Linux (PowerShell on Windows) | strong / deterministic |
| **Claude Code hook** (`adapters/claude/`) | Bash-tool clones inside Claude Code | strong / deterministic |
| **Routing snippets** (`adapters/{codex,grok,cursor,gemini}/`) | agents configured via AGENTS.md / .cursorrules / GEMINI.md | advisory |

The engine is a single pure-Python implementation, so the **verdict is
identical** wherever it runs — the enforcement layer differs per host, the
judgment does not.

## Handling a verdict

| Verdict | What to do |
|---|---|
| **SAFE** | Activate it. Still install dependencies via the sandboxed path (P6, `--ignore-scripts`, no network) and run with least privilege. |
| **REVIEW** | Open `komainu-report.md`, read the medium findings, then re-run with them acknowledged. The clean tree is usable; the flagged files were kept (not quarantined) because removing them could break the skill. |
| **DANGER** | Import is refused. Inspect `_QUARANTINE/MANIFEST.json` for what was pulled and why. Only override with a deliberate, audited `KOMAINU_BYPASS=1` if you fully trust the source. |

**Restoring a quarantined file** — nothing is deleted. Everything under
`_QUARANTINE/` keeps its original path; move a file back if you have reviewed it
and decided it is safe. Sanitized originals are kept under
`_QUARANTINE/originals/` for diffing.

## Configuration (environment variables)

| Variable | Effect |
|---|---|
| `KOMAINU_BYPASS=1` | Skip the gate for one command. **Audited** — every bypass is logged. |
| `KOMAINU_AUDIT=<path>` | Where the block/bypass audit log is written (default `~/.komainu/audit.log`). |
| `KOMAINU_STAGING=<dir>` | Where clones are staged and reports are written (default `workspace/komainu` or `~/.komainu/staging`). |

## Why it can claim "nearly everything" — honestly

Static scanning catches *known* patterns; obfuscated or novel payloads can slip
past any scanner. Komainu's real containment is structural:

1. **It never executes imported code.** A missed pattern that never runs does no
   harm.
2. **It disarms auto-run at clone time** (P2) — git hooks off, no submodule
   recursion, LFS/filters off, and it never runs install/lifecycle scripts
   (those only ever run sandboxed in P6 with `--ignore-scripts`).
3. **It quarantines, not deletes** — recoverable, auditable.

So the near-zero-damage guarantee comes from (1)(2)(3); the scanners are the
early-warning signal on top.

### The honest limits

- **`SAFE` ≠ safe to run.** It means "no static threat + nothing auto-runs."
- A regex gate can be bypassed (absolute paths, obfuscation). `KOMAINU_BYPASS=1`
  is the audited escape hatch.
- The hook only covers **shell-driven** clone/install. App-UI plugin installs
  are out of scope and rely on discipline.
- If a repo's *primary purpose* is malicious, removing the malice removes the
  feature — Komainu **refuses** the import (DANGER) rather than pretend-clean it.
