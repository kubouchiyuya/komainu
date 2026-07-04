# FAQ

### Does starring the repo install it? / star したら入る?

No. A GitHub star is a bookmark and trust signal — nothing runs on your machine
when you star, because GitHub cannot reach into your computer. The real install
is the one command in the [quickstart](quickstart.md); your AI agent can run
both the star and the install for you.

### What does "SAFE" actually mean? / SAFE の意味は?

"No static threat was found **and** nothing auto-executes on clone/install." It
is **not** a guarantee that running the code is safe. Komainu never runs the
imported code, so it cannot vouch for runtime behavior. Install dependencies via
the sandboxed path (`--ignore-scripts`, no network) and run with least privilege.

### Can a malicious repo just bypass the shim? / shim は回避できる?

A regex gate can be evaded (calling `/usr/bin/git` directly, obfuscation). The
shim raises the cost of a raw pull; the real containment is that Komainu
**never auto-executes** imported code and **disarms auto-run vectors at clone
time**. `KOMAINU_BYPASS=1` is the documented, **audited** escape hatch.

### Does it work with agents other than Claude Code? / 他のAIでも動く?

Yes. The scanner is pure Python and the **PATH shim** intercepts clone/install
for any agent that shells out — Codex, Cursor, Aider, Gemini CLI, or a human.
Claude Code gets an extra deterministic hook. Codex/Cursor/Gemini also have
routing snippets under `adapters/`.

### Windows? / Windows は?

Yes — the engine is cross-platform, and `shims/windows/komainu-shim.ps1`
provides PowerShell function shims. Dot-source it from your `$PROFILE`.

### Does Komainu modify the source repository? / 取得は破壊的ですか?

No. It fetches **read-only over HTTPS** and works on a local copy — it drops the
`.git` remote and does not push or change the source in any way. Everything
happens on your machine.

### What happens to dangerous files — are they deleted? / 危険物は削除される?

No. They are **moved** to `_QUARANTINE/` with a manifest recording origin and
reason, so you can inspect or restore them. Hidden-unicode is stripped in the
clean copy while the original is kept for diffing.

### Does it break the imported skill by removing things? / 機能が壊れない?

Komainu quarantines *ancillary* threats (injection files, auto-run wiring, junk)
and repairs/report broken references. If the malice **is** the skill's core
function, cleaning it would break the feature — so Komainu refuses the import
(DANGER) rather than ship a hollowed-out copy.

### Where do the reports go? / レポートはどこ?

Next to the staged clone: `komainu-report.md` (human) and
`komainu-report.json` (machine-readable, for pipelines).
