<!-- Komainu routing rule for OpenAI Codex. Paste into your AGENTS.md. -->
## Cloning / installing third-party code (Komainu)

Never run `git clone`, `gh repo clone`, `npm/pip/cargo/go install` from a git
URL, `npx degit`, or `curl … | sh` directly. Route every external acquisition
through the guardian:

    komainu import <https-url>

Komainu clones read-only, scans for prompt-injection / exfiltration /
auto-run / guardrail-tamper, quarantines what is dangerous, and only then
produces a vetted copy. Deterministic enforcement is also provided by the
komainu PATH shim; the audited one-time bypass is `KOMAINU_BYPASS=1`.
