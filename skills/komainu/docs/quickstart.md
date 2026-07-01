# Quickstart

## 1. Install

Komainu is a Claude Code plugin, but its scanner is pure Python so it works
from any agent on macOS, Linux, and Windows.

```bash
# star ⭐ the repo, then:
claude plugin marketplace add kubouchiyuya/komainu
claude plugin install komainu
```

Or use it directly without the plugin system:

```bash
git clone https://github.com/kubouchiyuya/komainu   # (the one repo you clone by hand)
python3 komainu/skills/komainu/bin/komainu selfcheck
```

## 2. Turn on automatic enforcement (optional but recommended)

The **PATH shim** makes *any* agent that shells out route clone/install
through Komainu — Claude Code, Codex, Cursor, Aider, Gemini CLI, or you.

```bash
komainu install-shims
echo 'export PATH="$HOME/.komainu/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc
```

On Claude Code you can also add the deterministic hook — copy the entry from
`adapters/claude/settings-snippet.json` into your `.claude/settings.json`.
(It takes effect at the next session start.)

## 3. Vet your first repo

```bash
komainu import https://github.com/owner/repo
```

You will get a verdict and a report:

| Verdict | Exit | Meaning |
|---|---|---|
| **SAFE** | 0 | no static threat, nothing auto-runs — you may activate it |
| **REVIEW** | 10 | medium findings — a human should approve before use |
| **DANGER** | 20 | critical findings — import refused unless you override |

The reports land next to the clone: `komainu-report.md` and
`komainu-report.json`. Anything dangerous is moved to `_QUARANTINE/` with a
manifest — nothing is deleted, so you can inspect or restore it.

## 4. Other commands

```bash
komainu scan ./local/dir       # vet a directory you already have
komainu selfcheck              # check git / python / environment
sh tests/smoke.sh              # 10 offline assertions prove detection works
```

> **Important:** `SAFE` means "no static threat + nothing auto-executes." It is
> **not** a promise that running the code is safe. To actually install
> dependencies, use the sandboxed path (`--ignore-scripts`, no network) that
> Komainu prints in the report, and run with least privilege.
