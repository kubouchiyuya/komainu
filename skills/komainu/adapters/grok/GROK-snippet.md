<!-- Komainu routing rule for Grok (xAI). Paste into your Grok agent's system
     prompt / rules file (e.g. GROK.md or the equivalent config). -->
## Third-party clone/install policy (Komainu)

Never run `git clone`, `gh repo clone`, `npm/pip/cargo/go install` from a git
URL, `npx degit`, or `curl … | sh` directly. Route every external acquisition
through the guardian:

    komainu import <https-url>

Komainu clones anonymously, scans for prompt-injection / exfiltration /
auto-run / guardrail-tamper, quarantines what is dangerous, and only then
produces a vetted copy. Deterministic enforcement is also provided by the
komainu PATH shim (it intercepts any shelled clone/install regardless of which
agent runs it); the audited one-time bypass is `KOMAINU_BYPASS=1`.
