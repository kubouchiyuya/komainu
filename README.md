<div align="center">

# 🛡️ 狛犬 / Komainu

**The gate every repo, skill, and plugin passes through before your AI touches it.**

Clone or install → deep scan → neutralize the danger → a clean copy handed back.
It *never runs the code it is checking.*

[![CI](https://github.com/kubouchiyuya/komainu/actions/workflows/ci.yml/badge.svg)](https://github.com/kubouchiyuya/komainu/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Pure Python](https://img.shields.io/badge/deps-zero%20(python%20stdlib)-black.svg)](#-quick-start)
[![Platforms](https://img.shields.io/badge/mac%20%7C%20linux%20%7C%20windows-black.svg)](#-for-every-ai-every-os)
[![Agents](https://img.shields.io/badge/Claude%20%7C%20OpenAI%20%7C%20Grok%20%7C%20Gemini%20%7C%20Cursor-black.svg)](#-for-every-ai-every-os)

[日本語](README.ja.md) · [Docs](skills/komainu/docs/index.md) · [Threat model](skills/komainu/references/threat-model.md)

</div>

---

Your AI installs code from strangers all day — a skill, a plugin, a repo, a
package. It **reads** their files as instructions and **runs** their scripts on
your behalf, at machine speed, usually while you're not watching. One poisoned
file turns your helpful agent into someone else's tool, and you may never find
out.

**狛犬 is the missing permission gate.** Named after the shrine lion-dogs that
turn evil away at the gate — it clones anonymously, reads every file for the
ways third-party code attacks an *agent*, quarantines what's dangerous (never
deletes), and hands back a clean copy — or refuses it. **Nothing is ever
executed to do this.**

```bash
komainu import https://github.com/owner/repo
#   → SAFE      you may use it
#   → REVIEW    a human should look first
#   → DANGER    refused
```

## ✨ Key capabilities

- **Reads code the way an attacker weaponizes it** — 5 categories: hidden AI
  instructions (prompt injection), auto-run traps, secret exfiltration, disguised
  malware, and the AI-era killer move: **rewriting your guardrails to disable the
  guard itself.**
- **Never executes what it inspects.** Read-only static analysis. A trap that
  never springs can't hurt you — that's the whole guarantee.
- **Quarantines, never deletes.** Everything dangerous is moved to
  `_QUARANTINE/` with a manifest. Inspect it, restore it, or don't.
- **Fires automatically, for every agent.** A PATH shim intercepts raw
  clone/install for *anything* that shells out — Claude Code, OpenAI Codex, Grok,
  Cursor, Aider, Gemini CLI — plus a deterministic Claude Code hook.
- **Zero dependencies.** Pure Python stdlib. Identical verdicts on mac, Linux,
  and Windows.
- **Honest by design.** `SAFE` means "no static threat + nothing auto-runs," not
  "safe to run anything." The docs never overclaim.

## 🚀 Quick start

```bash
# as a Claude Code plugin
claude plugin marketplace add kubouchiyuya/komainu
claude plugin install komainu

# turn on the universal shell gate (any agent that shells out)
komainu install-shims
echo 'export PATH="$HOME/.komainu/bin:$PATH"' >> ~/.zshrc
```

Then vet anything:

```bash
komainu import https://github.com/owner/repo   # clone → scan → sterilize → report
komainu scan ./local/dir                       # vet something you already have
komainu selfcheck                              # check your environment
sh skills/komainu/tests/smoke.sh               # 10 offline assertions
```

> **Tip:** the star on this repo does *not* install anything — a star can't reach
> your machine. The one install command does the real work; your AI can run both.

## 🚪 The 5 dangers it stops

| Danger | In plain words | Komainu |
|---|---|---|
| 🩹 **Prompt injection** | a hidden README line orders your AI to leak your keys | detects AI-directed text (en/ja/zh) + invisible/bidi/tag unicode; quarantines, strips hidden chars |
| ⚡ **Auto-run** | it runs the moment you clone/open/`npm install` | disarms git hooks, `.gitattributes` filters, submodules, lifecycle scripts, `.vscode`/`.envrc`/`.pth`/`conftest.py`/`build.rs` at clone time |
| 📤 **Exfiltration** | reads `~/.ssh`/`.env` and `curl`s it out | flags secret-read + network, `curl \| sh`, outbound POST — quarantine on sight |
| 🧬 **Disguised malware** | base64 blobs, opaque binaries | flags dynamic code eval, encoded payloads, opaque binaries, committed secrets |
| 🔓 **Guardrail tampering** | rewrites your `settings.json`/`CLAUDE.md`/hooks to switch off the guard | watched specifically → **refused** |

Full taxonomy & residual-risk analysis → [threat-model.md](skills/komainu/references/threat-model.md).

## 🧭 How it works

10 phases; phases 2–5 touch **no** running code. Intercept → minimal anonymous
clone (SHA-pinned, `.git` dropped, filters/hooks off) → scan → sterilize →
verdict → sandboxed install (`--ignore-scripts`, no-net) → re-verify → optimize
→ activate → audit. Deep dive → [how-it-works](skills/komainu/docs/how-it-works.md).

## 🧪 Testing / CI

| Command | Purpose |
|---|---|
| `sh skills/komainu/tests/smoke.sh` | 10 offline assertions: every category detects, sterilizes, clean repo passes, shim blocks |
| GitHub Actions (`ci.yml`) | runs the smoke suite on every push — the badge above is the proof |

## 🌐 For every AI, every OS

Two enforcement layers, so if one is bypassed the other holds. The scanning
engine is a single pure-Python implementation, so the **verdict is identical**
everywhere — only the enforcement layer differs.

| Layer | Covers | Strength |
|---|---|---|
| **PATH shim** | any shell-driving agent (Claude Code, OpenAI Codex, Grok, Cursor, Aider, Gemini CLI) — mac/Linux, PowerShell on Windows | strong / deterministic |
| **Claude Code hook** | Bash-tool clones inside Claude Code | strong / deterministic |
| **Routing snippets** | Codex / Grok / Cursor / Gemini via their config files | advisory |

## ⚖️ The honest limits

- `SAFE` ≠ safe to run anything — it means no static threat + nothing auto-runs.
- Static scanning can miss novel/obfuscated payloads; the real wall is *nothing
  runs*, not the pattern list.
- A regex gate can be bypassed — `KOMAINU_BYPASS=1` is the audited escape hatch.
- If a repo's whole purpose is malicious, cleaning it removes the feature, so
  Komainu refuses (DANGER) rather than ship a hollow copy.

## 🔗 Related projects

- 🧭 **[羅針盤 / Rashinban](https://github.com/kubouchiyuya/rashinban)** — a compass
  for autonomous agent goals: turn a rough request into a linted, verifiable
  `/goal`. Komainu guards what comes *in*; Rashinban aims where you're *going*.

## 🤝 Contributing & security

- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Found a vulnerability? → [SECURITY.md](SECURITY.md) (please don't open a public issue for it)

## 📜 License

MIT — see [LICENSE](LICENSE). When Komainu imports third-party code, it preserves
the source's LICENSE and attribution.

<div align="center">

Stand a guardian at the gate, so your AI never trusts a stranger blindly.

</div>
