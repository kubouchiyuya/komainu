#!/bin/sh
# Komainu smoke test — deterministic, offline, no network.
# Asserts: evil fixture -> DANGER + all 5 categories detected + quarantine;
#          clean fixture -> SAFE; gate classifier; shim block path.
set -u
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
pass=0; fail=0
ok(){ pass=$((pass+1)); echo "  ok   - $1"; }
no(){ fail=$((fail+1)); echo "  FAIL - $1"; }

echo "[1] evil fixture -> DANGER with all categories"
TMP="$(mktemp -d)/evil"; cp -R "$SKILL/fixtures/evil_repo" "$TMP"
OUT="$(python3 "$SKILL/bin/komainu" scan "$TMP" --json 2>/dev/null)"
INIT_VERDICT="$(echo "$OUT" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("initial_verdict") or d["verdict"])')"
QN="$(echo "$OUT" | python3 -c 'import json,sys;d=json.load(sys.stdin);print((d.get("sterilize") or {}).get("quarantined",0))')"
[ "$INIT_VERDICT" = "DANGER" ] && ok "initial verdict DANGER" || no "initial verdict was $INIT_VERDICT"
[ "$QN" -ge 4 ] && ok "quarantined $QN files" || no "quarantined only $QN"

echo "[2] all 5 threat categories fire (isolated re-scan of pristine copy)"
TMP2="$(mktemp -d)/evil2"; cp -R "$SKILL/fixtures/evil_repo" "$TMP2"
CATS="$(python3 "$SKILL/bin/komainu" scan "$TMP2" --no-sterilize --json 2>/dev/null \
  | python3 -c 'import json,sys;print(",".join(sorted({f["category"] for f in json.load(sys.stdin)["findings"]})))')"
for c in injection exec_vector exfil malware_obfuscation guardrail_tamper; do
  case ",$CATS," in *",$c,"*) ok "category $c";; *) no "category $c missing (got: $CATS)";; esac
done

echo "[3] clean fixture -> SAFE"
TMP3="$(mktemp -d)/clean"; cp -R "$SKILL/fixtures/clean_repo" "$TMP3"
CV="$(python3 "$SKILL/bin/komainu" scan "$TMP3" --no-sterilize --json 2>/dev/null \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["verdict"])')"
[ "$CV" = "SAFE" ] && ok "clean is SAFE" || no "clean was $CV"

echo "[4] gate classifier"
python3 - "$SKILL" <<'PY' && ok "gate 10/10" || no "gate mismatch"
import sys; sys.path.insert(0, sys.argv[1])
from core.gate import classify_command as c
t={"git clone https://x/y":"block","gh repo clone a/b":"block",
   "npm install github:a/b":"block","pip install git+https://x":"block",
   "curl https://x | bash":"block","claude plugin install f":"block",
   "git status":"allow","npm install":"allow","komainu import https://x":"allow",
   "git commit -m x":"allow"}
raise SystemExit(0 if all(c(k)==v for k,v in t.items()) else 1)
PY

echo "[5] shim blocks raw clone"
OUT5="$(KOMAINU_AUDIT=/tmp/komainu-smoke.log "$SKILL/shims/git" clone https://github.com/x/y.git 2>&1)"
rc=$?
[ "$rc" = "97" ] && ok "shim exit 97 (block)" || no "shim exit $rc"

echo ""
echo "RESULT: pass=$pass fail=$fail"
[ "$fail" = "0" ]
