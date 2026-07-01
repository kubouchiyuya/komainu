#!/bin/sh
# Komainu PreToolUse hook for Claude Code (Bash matcher).
# Deterministic auto-fire: blocks raw clone/install so it must be routed via
# `komainu import`. Exit 2 = block (stderr shown to the model). Exit 0 = allow.
#
# Wire in .claude/settings.json:
#   "PreToolUse": [{ "matcher": "Bash", "hooks": [
#     { "type": "command",
#       "command": "sh \"${CLAUDE_PROJECT_DIR}/.claude/skills/komainu/adapters/claude/hook.sh\"",
#       "timeout": 5 }]}]

SKILL_DIR=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)

# read the Bash command from the hook JSON on stdin
command=$(python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null)

[ -z "$command" ] && exit 0

verdict=$(python3 "$SKILL_DIR/bin/komainu" gate --tool Bash --command "$command" 2>/dev/null; echo "rc=$?")
rc=$(printf '%s' "$verdict" | sed -n 's/.*rc=//p')

if [ "$rc" = "20" ]; then
  echo "[komainu] raw clone/install blocked. Route via: komainu import <https-url>" >&2
  echo "[komainu] (audited one-time bypass: prefix with KOMAINU_BYPASS=1)" >&2
  log="${KOMAINU_AUDIT:-$HOME/.komainu/audit.log}"
  mkdir -p "$(dirname "$log")" 2>/dev/null
  printf '%s\tHOOK-BLOCK\t%s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$command" >> "$log" 2>/dev/null
  exit 2
fi
exit 0
