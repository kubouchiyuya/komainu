"""Komainu scanners — the 5 threat categories (stdlib only).

Each scanner takes the cloned repo root and returns list[Finding].
Nothing here executes repo content; everything is read-only static analysis.
Any instruction text found is treated strictly as DATA, never followed.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .util import (
    Finding, iter_files, read_text, rel, is_binary_path,
    CAT_INJECTION, CAT_EXEC, CAT_EXFIL, CAT_MALWARE, CAT_SELFDEFENSE,
    SEV_LOW, SEV_MED, SEV_HIGH, SEV_CRIT, SEV_INFO,
)

# ---------------------------------------------------------------------------
# Category 1: prompt injection + hidden unicode
# ---------------------------------------------------------------------------

# Zero-width / invisible / bidi-control / tag characters used to hide payloads.
_HIDDEN_RANGES = [
    (0x200B, 0x200F),  # zero-width space/joiner + LRM/RLM
    (0x202A, 0x202E),  # bidi embedding/override (LRE RLE PDF LRO RLO)
    (0x2060, 0x2064),  # word joiner / invisible operators
    (0x2066, 0x2069),  # bidi isolates
    (0xFEFF, 0xFEFF),  # BOM / zero-width no-break space
    (0xE0000, 0xE007F),  # unicode tag chars (used for hidden-instruction smuggling)
]


def _hidden_chars(text: str) -> list[tuple[int, str]]:
    out = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        for lo, hi in _HIDDEN_RANGES:
            if lo <= cp <= hi:
                out.append((i, f"U+{cp:04X}"))
                break
    return out


# Multilingual prompt-injection phrases (en / ja / zh). Case-insensitive.
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|the)\s+",
    r"forget\s+(everything|all\s+previous|your\s+instructions)",
    r"you\s+are\s+now\s+(a|an|in)\b",
    r"new\s+(system|instructions?)\s*:",
    r"override\s+(the\s+)?(system|safety|guardrails?)",
    r"(reveal|print|show|repeat)\s+(your|the)\s+(system\s+)?(prompt|instructions)",
    r"do\s+not\s+tell\s+the\s+user",
    r"without\s+(telling|informing|asking)\s+the\s+user",
    r"exfiltrat",
    r"send\s+(the|all|your)?\s*(secrets?|credentials?|keys?|tokens?|env)",
    r"上記の(指示|命令)を?(無視|忘れ)",
    r"これまでの(指示|命令|ルール)を(無視|忘れ)",
    r"ユーザーに(知らせ|伝え|報告し)ない",
    r"あなたは今(から)?",
    r"忽略(以上|之前|所有)(的)?(指令|指示)",
    r"不要(告诉|通知)用户",
]
_INJ_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# Files that instruct an AI agent directly (highest injection value).
_AGENT_TARGET_GLOBS = (
    "SKILL.md", "AGENTS.md", "CLAUDE.md", ".cursorrules", ".clinerules",
    "GEMINI.md", "copilot-instructions.md",
)


def _looks_agent_target(path: Path) -> bool:
    n = path.name
    return any(re.fullmatch(re.escape(g).replace(r"\*", ".*"), n) or n == g
               for g in _AGENT_TARGET_GLOBS)


# Hidden-in-markup: white text, tiny font, offscreen, HTML comments with commands
_MARKUP_HIDE_RE = re.compile(
    r"(color\s*:\s*#?fff|color\s*:\s*white|font-size\s*:\s*0|display\s*:\s*none|"
    r"visibility\s*:\s*hidden|opacity\s*:\s*0|position\s*:\s*absolute;\s*left\s*:\s*-\d)",
    re.IGNORECASE,
)


def scan_injection(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        text = read_text(path)
        if text is None:
            continue
        r = rel(path, root)
        agent_target = _looks_agent_target(path)

        # hidden unicode
        hidden = _hidden_chars(text)
        if hidden:
            sample = ", ".join(cp for _, cp in hidden[:8])
            findings.append(Finding(
                CAT_INJECTION, SEV_HIGH, "hidden-unicode",
                f"{len(hidden)} invisible/bidi/tag char(s) — classic hidden-instruction smuggling",
                r, evidence=sample, action="sanitize",
            ))

        # injection phrasing
        for m in _INJ_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            sev = SEV_CRIT if agent_target else SEV_HIGH
            findings.append(Finding(
                CAT_INJECTION, sev, "prompt-injection",
                "AI-directed instruction phrasing"
                + (" inside an agent-instruction file" if agent_target else ""),
                r, line=line, evidence=m.group(0)[:120],
                action="quarantine" if agent_target else "flag",
            ))

        # markup-hidden content
        if path.suffix.lower() in (".md", ".html", ".htm", ".mdx"):
            for m in _MARKUP_HIDE_RE.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                findings.append(Finding(
                    CAT_INJECTION, SEV_MED, "hidden-markup",
                    "content hidden from humans but readable by an agent",
                    r, line=line, evidence=m.group(0)[:80], action="flag",
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 2: auto-run / execution vectors (clone / install / editor-open)
# ---------------------------------------------------------------------------

def _scan_file_patterns(root: Path, spec: list[tuple[str, str, str, str]],
                        category: str, path_filter: Callable[[Path], bool] | None = None
                        ) -> list[Finding]:
    """spec: list of (regex, severity, rule, message)."""
    compiled = [(re.compile(rx, re.IGNORECASE | re.MULTILINE), sev, rule, msg)
                for rx, sev, rule, msg in spec]
    out: list[Finding] = []
    for path in iter_files(root):
        if path_filter and not path_filter(path):
            continue
        text = read_text(path)
        if text is None:
            continue
        r = rel(path, root)
        for rx, sev, rule, msg in compiled:
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                out.append(Finding(category, sev, rule, msg, r, line=line,
                                   evidence=m.group(0)[:120], action="flag"))
    return out


def scan_exec_vectors(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    # 2a. presence-based vectors (existence of the file/dir is the signal)
    presence = [
        (".git/hooks", SEV_HIGH, "git-hooks", "git hooks present (run on git operations)"),
        (".githooks", SEV_HIGH, "githooks-dir", "custom hooks dir (core.hooksPath candidate)"),
        (".gitmodules", SEV_MED, "gitmodules", "submodules — fetch external code on --recurse"),
        (".vscode/tasks.json", SEV_HIGH, "vscode-tasks", "editor tasks (runOn folderOpen can auto-execute)"),
        (".vscode/settings.json", SEV_LOW, "vscode-settings", "editor settings (may enable auto-run extensions)"),
        (".devcontainer", SEV_MED, "devcontainer", "devcontainer (postCreate/postStart commands)"),
        (".envrc", SEV_HIGH, "direnv", "direnv .envrc auto-executes on cd"),
    ]
    for relp, sev, rule, msg in presence:
        p = root / relp
        if p.exists():
            findings.append(Finding(CAT_EXEC, sev, rule, msg, relp, action="quarantine"))

    # 2b. .gitattributes filter/clean/smudge/process drivers (checkout-time RCE)
    ga = root / ".gitattributes"
    if ga.exists():
        t = read_text(ga) or ""
        for m in re.finditer(r"(filter|clean|smudge|process)\s*=\s*(\S+)", t):
            findings.append(Finding(
                CAT_EXEC, SEV_HIGH, "gitattributes-filter",
                "content filter driver runs a command at checkout",
                ".gitattributes", evidence=m.group(0)[:120], action="quarantine"))

    # 2c. package-manager lifecycle scripts (run on install)
    # iter_files (not rglob) so _QUARANTINE / node_modules / .git stay excluded.
    for pkg in iter_files(root):
        if pkg.name != "package.json":
            continue
        t = read_text(pkg) or ""
        for m in re.finditer(r'"(preinstall|install|postinstall|prepare|prepublish|prepublishOnly)"\s*:', t):
            line = t.count("\n", 0, m.start()) + 1
            findings.append(Finding(
                CAT_EXEC, SEV_HIGH, "npm-lifecycle",
                "npm lifecycle script executes on install",
                rel(pkg, root), line=line, evidence=m.group(1), action="flag"))

    # 2d. python / make build-time execution
    findings += _scan_file_patterns(root, [
        (r"cmdclass|setup\(\s", SEV_MED, "setup-py", "setup.py may run code on install"),
    ], CAT_EXEC, path_filter=lambda p: p.name in ("setup.py",))

    # 2e. Claude Code plugin auto-run wiring (Pre/PostToolUse hooks, settings hooks)
    findings += _scan_file_patterns(root, [
        (r'"(PreToolUse|PostToolUse|Stop|SubagentStop|UserPromptSubmit)"', SEV_HIGH,
         "cc-hook", "Claude Code hook wiring — auto-fires on agent tool use"),
        (r'"command"\s*:\s*"[^"]*(curl|wget|bash\s+-c|sh\s+-c|python\s+-c)', SEV_CRIT,
         "cc-hook-shell", "Claude Code hook runs a shell command automatically"),
    ], CAT_EXEC, path_filter=lambda p: p.name in ("hooks.json", "settings.json", "settings.local.json"))

    # 2f. name-based auto-run files anywhere in the tree
    name_vectors = {
        "sitecustomize.py": (SEV_HIGH, "python sitecustomize auto-imports on interpreter start"),
        "usercustomize.py": (SEV_HIGH, "python usercustomize auto-imports on interpreter start"),
        "conftest.py": (SEV_MED, "pytest auto-loads conftest.py when tests run"),
        "build.rs": (SEV_HIGH, "cargo build script executes on `cargo build`"),
        ".bashrc": (SEV_MED, "shell rc shipped in repo (auto-sourced if placed in $HOME)"),
        ".zshrc": (SEV_MED, "shell rc shipped in repo (auto-sourced if placed in $HOME)"),
        ".bash_profile": (SEV_MED, "shell profile shipped in repo"),
        ".zprofile": (SEV_MED, "shell profile shipped in repo"),
        ".profile": (SEV_MED, "shell profile shipped in repo"),
    }
    for p in iter_files(root):
        meta = name_vectors.get(p.name)
        if meta:
            findings.append(Finding(CAT_EXEC, meta[0], "auto-run-file", meta[1],
                                    rel(p, root), action="flag"))
        elif p.suffix == ".pth":
            findings.append(Finding(
                CAT_EXEC, SEV_MED, "python-pth",
                "python .pth file auto-executes 'import' lines when on sys.path",
                rel(p, root), action="flag"))

    return findings


# ---------------------------------------------------------------------------
# Category 3: exfiltration / outbound data flow (guardrail check)
# ---------------------------------------------------------------------------

_SECRET_SOURCES = (
    r"\.ssh/|id_rsa|id_ed25519|\.aws/|\.config/gcloud|\.npmrc|\.git-credentials|"
    r"\.env(\.|\b)|process\.env|os\.environ|keychain|security\s+find-generic-password|"
    r"AWS_SECRET|GITHUB_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY"
)
_NET_SINKS = (
    r"curl|wget|nc\b|ncat|/dev/tcp/|Invoke-WebRequest|Invoke-RestMethod|"
    r"requests\.(get|post|put)|urllib|http\.client|fetch\(|axios|net\.connect|"
    r"socket\.(socket|connect)|nslookup|dig\s"
)


def scan_exfil(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    curl_pipe = re.compile(r"(curl|wget)\s+[^\n|]*\|\s*(sudo\s+)?(sh|bash|zsh|python|node|ruby|pwsh)",
                           re.IGNORECASE)
    net_re = re.compile(_NET_SINKS, re.IGNORECASE)
    sec_re = re.compile(_SECRET_SOURCES, re.IGNORECASE)
    post_re = re.compile(r"(curl[^\n]*(-X\s*POST|-X\s*PUT|--data|-d\s)|requests\.(post|put)|-Method\s+Post)",
                         re.IGNORECASE)

    for path in iter_files(root):
        text = read_text(path)
        if text is None:
            continue
        r = rel(path, root)
        for m in curl_pipe.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding(
                CAT_EXFIL, SEV_CRIT, "curl-pipe-shell",
                "downloads remote code and pipes straight into a shell",
                r, line=line, evidence=m.group(0)[:120], action="quarantine"))

        has_secret = sec_re.search(text)
        has_net = net_re.search(text)
        if has_secret and has_net:
            line = text.count("\n", 0, has_secret.start()) + 1
            findings.append(Finding(
                CAT_EXFIL, SEV_CRIT, "secret-plus-network",
                "reads secrets/credentials AND has network egress in the same file",
                r, line=line, evidence=(has_secret.group(0) + " + " + has_net.group(0))[:120],
                action="quarantine"))
        elif has_net:
            for m in post_re.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                findings.append(Finding(
                    CAT_EXFIL, SEV_MED, "outbound-post",
                    "outbound POST/PUT — verify destination and payload",
                    r, line=line, evidence=m.group(0)[:100], action="flag"))
    return findings


# ---------------------------------------------------------------------------
# Category 4: malware-like obfuscation + committed secrets
# ---------------------------------------------------------------------------

_SECRET_LITERALS = [
    (r"AKIA[0-9A-Z]{16}", "aws-access-key"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "github-token"),
    (r"sk-ant-[A-Za-z0-9\-_]{20,}", "anthropic-key"),
    (r"sk-[A-Za-z0-9]{32,}", "openai-key"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "slack-token"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "private-key"),
]
_SECRET_RES = [(re.compile(rx), name) for rx, name in _SECRET_LITERALS]


def scan_malware(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    obf = re.compile(
        r"(eval\s*\(|\bexec\s*\(|base64\s+-d|b64decode|atob\s*\(|"
        r"FromBase64String|python\s+-c\s+['\"]|node\s+-e\s+['\"]|"
        r"\$\(echo\s+[A-Za-z0-9+/=]{40,}|\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2})",
        re.IGNORECASE)
    for path in iter_files(root):
        # opaque binaries / unexpected executables
        if is_binary_path(path) and path.suffix.lower() in (
                ".exe", ".dll", ".so", ".dylib", ".bin", ".wasm", ".class", ".jar", ".o"):
            findings.append(Finding(
                CAT_MALWARE, SEV_HIGH, "opaque-binary",
                "compiled/opaque binary — cannot be statically vetted",
                rel(path, root), action="quarantine"))
            continue
        text = read_text(path)
        if text is None:
            continue
        r = rel(path, root)
        for m in obf.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(Finding(
                CAT_MALWARE, SEV_HIGH, "obfuscation",
                "dynamic-eval / encoded payload — common malware disguise",
                r, line=line, evidence=m.group(0)[:100], action="flag"))
        for rx, name in _SECRET_RES:
            mm = rx.search(text)
            if mm:
                line = text.count("\n", 0, mm.start()) + 1
                findings.append(Finding(
                    CAT_MALWARE, SEV_MED, "committed-secret",
                    f"committed secret ({name})",
                    r, line=line, evidence="<redacted>", action="flag"))
    return findings


# ---------------------------------------------------------------------------
# Category 5: guardrail self-defense — repo trying to disable the guardian
# ---------------------------------------------------------------------------

# Paths whose modification means "escalate privilege / disable guardrails".
_GUARD_TARGETS = re.compile(
    r"(\.claude/settings(\.local)?\.json|CLAUDE\.md|AGENTS\.md|"
    r"\.claude/hooks/|\.claude/skills/komainu|permissions\.(deny|allow)|"
    r"settings-ssot|hitl-gate|miyabi-blockade|komainu-gate|core\.hooksPath)",
    re.IGNORECASE)
_WRITE_VERBS = re.compile(
    r"(>|>>|tee\b|sed\s+-i|cp\s|mv\s|rm\s|cat\s*>|writeFile|fs\.write|"
    r"Set-Content|Add-Content|Out-File|open\([^)]*['\"]w)",
    re.IGNORECASE)


def scan_guardrail_tamper(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        text = read_text(path)
        if text is None:
            continue
        r = rel(path, root)
        for m in _GUARD_TARGETS.finditer(text):
            # a line that references a guardrail target AND a write verb is high signal
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            line_text = text[line_start: line_end if line_end != -1 else len(text)]
            if _WRITE_VERBS.search(line_text):
                line = text.count("\n", 0, m.start()) + 1
                findings.append(Finding(
                    CAT_SELFDEFENSE, SEV_CRIT, "guardrail-tamper",
                    "attempts to WRITE to a guardrail / settings / komainu file "
                    "(disable-the-guardian / privilege escalation)",
                    r, line=line, evidence=line_text.strip()[:120], action="reject"))
    return findings


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------

ALL_SCANNERS = [
    scan_injection,
    scan_exec_vectors,
    scan_exfil,
    scan_malware,
    scan_guardrail_tamper,
]


def scan_all(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for fn in ALL_SCANNERS:
        try:
            findings += fn(root)
        except Exception as e:  # a broken scanner must not blind the others
            findings.append(Finding(
                "engine", SEV_INFO, "scanner-error",
                f"{fn.__name__} raised {type(e).__name__}: {e}", action="flag"))
    return findings
