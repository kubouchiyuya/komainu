<!-- Komainu routing rule for Gemini CLI. Paste into GEMINI.md. -->
## Third-party clone/install policy (Komainu)

All external code acquisition (`git clone`, `gh repo clone`, install-from-git,
`npx degit`, `curl … | sh`) must go through the guardian:

    komainu import <https-url>

It clones read-only, scans (prompt-injection / exfiltration / auto-run /
guardrail-tamper), quarantines danger, and yields a vetted copy. The komainu
PATH shim enforces this for any shelled command; audited bypass: `KOMAINU_BYPASS=1`.
