# Komainu rule for Cursor / Windsurf / Cline. Append to .cursorrules (or .clinerules).

When asked to clone a repository or install a plugin/skill/package from an
external source, DO NOT run git clone / gh repo clone / npm|pip|cargo|go
install-from-git / npx degit / curl|sh directly. Always route through:

    komainu import <https-url>

Komainu is the security guardian: read-only clone, full scan (injection /
exfiltration / auto-run vectors / guardrail tampering), quarantine of dangerous
files, then a vetted copy. The komainu PATH shim enforces this at the shell.
