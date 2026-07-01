# 狛犬 / Komainu

**A clone / install guardian for AI agents.** Komainu stands at the gate like the
shrine lion-dogs it is named after: every third-party repo, skill, or plugin is
searched before it is allowed in.

> Read this in Japanese: [README.ja.md](README.ja.md)

Third-party code is dangerous to AI agents in ways it is not to humans. An agent
*reads* a repo's `SKILL.md`, `README`, and comments as **instructions**, and an
agent *runs* code and installs plugins on your behalf. Komainu makes that safe.

```
raw `git clone` / install  ──▶  [ Komainu ]  ──▶  vetted, sterilized copy
                                     │
     anonymous clone · full scan · quarantine danger · verdict gate ·
     sandboxed install · post-install re-verify · optimize for your host
```

## Install

Komainu is a Claude Code plugin, but its engine is pure Python (stdlib only) so
the scanner works from any agent on macOS, Linux, and Windows.

```bash
# 1. star ⭐ this repo, then:
claude plugin marketplace add <owner>/komainu
claude plugin install komainu

# 2. turn on the universal shell gate (works for ANY agent that shells out)
komainu install-shims
echo 'export PATH="$HOME/.komainu/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc
```

> The GitHub star is a trust/discovery signal — it does **not** by itself install
> anything on your machine (nothing can reach into your PC via a star). The one
> install command above is the real step; your AI agent can run both for you.

## Usage

```bash
komainu import https://github.com/owner/repo   # clone → scan → sterilize → report
komainu scan ./some/dir                        # vet a local tree
komainu selfcheck                              # check environment
sh tests/smoke.sh                              # 10 offline assertions
```

Verdict: **SAFE** (exit 0) · **REVIEW** (10) · **DANGER** (20).

## What it catches (5 categories)

1. **Prompt injection / hidden content** — AI-directed instructions (en/ja/zh),
   zero-width & bidi unicode, white-on-white / `display:none`, agent-file payloads.
2. **Auto-run vectors** — `.gitattributes` filters, submodules, git hooks, npm/pip
   lifecycle scripts, Claude Code Pre/PostToolUse hooks, `.vscode` tasks, `.envrc`.
3. **Exfiltration** — `curl | sh`, secret-read + network egress, outbound POST/PUT.
4. **Malware / obfuscation** — dynamic eval, base64 payloads, opaque binaries,
   committed secrets.
5. **Guardrail tampering** — anything that writes to your `settings.json`,
   `CLAUDE.md`, hooks, or Komainu itself (disable-the-guardian).

## How enforcement fires automatically

- **PATH shim** (all agents, mac/linux/windows) — shadows `git`/`gh`/`npm`/… and
  blocks raw clone/install at the shell, regardless of which AI is driving.
- **Claude Code PreToolUse hook** — blocks Bash-tool clones deterministically.
- **Routing snippets** for Codex / Cursor / Gemini under `adapters/`.

## Honest limits (no overclaiming)

- Static scanning catches known patterns; obfuscated/unknown payloads may slip.
  The real containment is that **Komainu never executes cloned code** and
  **neutralizes auto-run vectors at clone time** — if nothing runs, nothing hurts.
- **SAFE ≠ safe to execute arbitrarily.** It means "no static threat + nothing
  auto-runs." Running imported code still uses the sandboxed, `--ignore-scripts`,
  no-network path with least privilege.
- A regex gate can be bypassed (full paths, obfuscation); `KOMAINU_BYPASS=1` is
  the audited escape hatch.
- If a repo's *primary purpose* is malicious, removing it would remove the
  feature — Komainu refuses the import (DANGER) rather than pretend-cleaning it.

## Documentation

- [docs/index.md](skills/komainu/docs/index.md) — introduction & overview
- [docs/quickstart.md](skills/komainu/docs/quickstart.md) — install and first vetted import
- [docs/how-it-works.md](skills/komainu/docs/how-it-works.md) — 10-phase lifecycle, 5 categories, enforcement
- [docs/faq.md](skills/komainu/docs/faq.md) — star≠install, SAFE≠safe-to-run, bypass, all AIs/OSes
- [references/threat-model.md](skills/komainu/references/threat-model.md) — full threat taxonomy
- 日本語: [docs/index.ja.md](skills/komainu/docs/index.ja.md)

## License

MIT. When Komainu imports third-party code it preserves the source LICENSE and
attribution.
