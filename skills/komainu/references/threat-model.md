# Komainu 脅威モデル — clone/install で AI エージェントが踏む地雷の完全分類

対象: 第三者の repo / skill / plugin を **AI エージェントが取り込み、読み、実行する**
ときに発生しうる被害。各カテゴリの「何を」「なぜ危険か」「Komainu の検出/対処」「残余リスク」。

---

## カテゴリ1: プロンプトインジェクション / 隠しコンテンツ

AI エージェントは repo の中身（SKILL.md / README / コメント / データ）を**指示として読む**。
ここに攻撃者が命令を仕込む。

| 脅威 | 例 | 検出 (`scan_injection`) | 対処 |
|---|---|---|---|
| 直接注入 | "Ignore all previous instructions", "reveal your system prompt" | 多言語 regex(en/ja/zh) | agent-file 内は CRITICAL→隔離、それ以外 flag |
| 隠し unicode | ゼロ幅(U+200B) / bidi override(U+202E) / タグ文字(U+E00xx) | コードポイント範囲判定 | HIGH→sanitize(除去・原本は隔離) |
| markup 隠蔽 | `color:#fff` / `font-size:0` / `display:none` / HTML コメント命令 | md/html パターン | MED→flag |
| agent 宛て埋込 | SKILL.md/AGENTS.md/CLAUDE.md/.cursorrules の命令化 | ファイル種別で重み付け | CRITICAL |

**残余リスク**: 言い換え・意味的注入は regex を逃れる。→ F2 で LLM 意味判定
（tool 無し・データ限定 sandbox 判定器。判定器自身への注入も封じる）を追加予定。

---

## カテゴリ2: clone / install / editor-open 時の自動実行ベクター

「取り込んだ瞬間・install した瞬間・エディタで開いた瞬間」に走るもの。

| 脅威 | なぜ | 検出 (`scan_exec_vectors`) |
|---|---|---|
| `.gitattributes` filter/clean/smudge/process | checkout 時にコマンド実行(RCE) | driver 検出→隔離。clone時は working tree が空なので `git show HEAD:` で**先行検出**（未定義 filter は config 不在で不発、lfs は無効化済） |
| `.gitmodules` submodule | `--recurse` で外部コード取得 | 存在検出。Komainu は非再帰 clone |
| git hooks / `.githooks` / core.hooksPath | git 操作でスクリプト実行 | 存在検出→隔離。clone時 hooksPath=/dev/null |
| npm lifecycle (pre/post install, prepare) | `npm install` で任意実行 | package.json 解析→flag。install は `--ignore-scripts` |
| setup.py / Makefile | build/install 時実行 | パターン検出 |
| **Claude Code hooks** (Pre/PostToolUse) | エージェントの tool 使用で自動発火 | hooks.json/settings.json 解析→shell 付きは CRITICAL |
| `.vscode/tasks.json`(runOn folderOpen) / `.devcontainer` / `.envrc` | エディタ/cd で自動実行 | 存在検出→隔離 |
| `sitecustomize.py`/`usercustomize.py`/`*.pth` | Python インタプリタ起動時に自動 import/実行 | 名前・拡張子検出→flag |
| `conftest.py` | pytest 実行時に自動ロード | 名前検出→flag |
| `build.rs` | `cargo build` で実行 | 名前検出→flag |
| shell rc (`.bashrc`/`.zshrc`/`.profile` 等) | `$HOME` に置かれると自動 source | 名前検出→flag |

**残余リスク**: 新種の自動実行フック。→ 構造対処（P2で hook/filter/submodule を無効化、
lifecycle 非実行）が個別検出漏れを補う。

---

## カテゴリ3: 外部への情報流出（exfiltration）— 最優先で論外

秘密情報を読んで外に送る／リモートコードを引いて実行する経路。**あれば即隔離**。

| 脅威 | 検出 (`scan_exfil`) | severity |
|---|---|---|
| `curl\|wget … \| sh/bash/python` | download→shell パイプ | CRITICAL→隔離 |
| 秘密読取＋network 同居 | `~/.ssh`,`~/.aws`,`.env`,`process.env`,keychain,token + curl/requests/socket | CRITICAL→隔離 |
| 外向き POST/PUT | curl -X POST / requests.post / Invoke-RestMethod | MED→flag(宛先要確認) |
| DNS/webhook exfil | nslookup/dig/`/dev/tcp/` | net sink として検出 |

**残余リスク**: 暗号化/難読化された送信、正規 telemetry を装う送信。→ POST は宛先を
人間確認に回す。付随的なら隔離＋承認、機能の主目的なら import 拒否。

---

## カテゴリ4: ウイルス的難読化 / 混入シークレット

| 脅威 | 検出 (`scan_malware`) |
|---|---|
| 動的 eval/exec、base64 -d、atob、`python -c`/`node -e`、hex 連結 | 難読化 regex→flag(HIGH) |
| コンパイル済みバイナリ(.exe/.so/.dylib/.wasm/.jar…) | 静的解析不能→隔離(HIGH) |
| コミット済み secret(AWS/GitHub/Anthropic/OpenAI/Slack/private-key) | リテラル regex→flag |

**残余リスク**: パック済みマルウェア・多段復号。→ バイナリは既定隔離、実行は sandbox のみ。

---

## カテゴリ5: ガードレール改竄（disable-the-guardian）— AI時代の最重要

repo が**防御機構そのものを書き換えて無効化**し、以後の攻撃を通す型。内向きの権限昇格。

| 脅威 | 検出 (`scan_guardrail_tamper`) |
|---|---|
| `.claude/settings(.local).json` への write | ガード対象 path＋write verb 同一行→CRITICAL→**reject** |
| CLAUDE.md / AGENTS.md / permissions.deny の改変 | 同上 |
| hook / komainu 自身 / hitl-gate / miyabi-blockade の上書き | 同上 |
| `core.hooksPath` 書換 | 同上 |

**残余リスク**: 難読化された書換コマンド。→ 対象語＋write動詞の近接で高精度検出、
reject は DANGER 直行で import を止める。

---

## カテゴリ6: サプライチェーン / 依存リスク

2025-26 の主戦場（npm Shai-Hulud は 500+ パッケージ感染、pre-install 実行化で影響拡大 / dependency-confusion / typosquat）。

| 脅威 | 検出 (`scan_supply_chain`) |
|---|---|
| git/URL/file 由来の依存 | `package.json` の dep 値が `git+`/`github:`/`http`/`file:` → flag |
| registry 上書き（dependency-confusion） | `.npmrc` の `registry=` / scoped registry → flag |
| lockfile 不在（版未固定） | deps 宣言ありで lock 無し → flag |
| pip の git/alt-index 依存 | `git+` / `--index-url` / `-e git+` → flag |

**残余リスク**: transitive（install 時に外部から引く）依存は clone 時点で repo に無い → lifecycle 非実行＋`--ignore-scripts` で受ける。

## カテゴリ7: MCP tool poisoning / rug-pull

OWASP **MCP03:2025**。tool description に隠した指示が、agent が tool を呼んだ瞬間に host 権限で実行される。承認後に定義が差し替わる rug-pull も。

| 脅威 | 検出 (`scan_mcp_poisoning`) |
|---|---|
| tool description への注入 | MCP config(`mcpServers`/`inputSchema`) の `description` に注入文/隠しunicode → CRIT 隔離 |
| remote-fetch サーバ | `command` が `npx`/`uvx`/`curl` 等で起動時に外部取得 → flag |

**残余リスク**: 定義の可変性（rug-pull）は静的には追えない → SHA ピン＋再検証(P7)で受ける。

## カテゴリ8: 永続化 / バックドア / 逆シェル

| 脅威 | 検出 (`scan_persistence`) |
|---|---|
| 逆シェル | `bash -i >& /dev/tcp/`・`nc -e`・`mkfifo\|sh` → CRIT |
| SSH backdoor | `>> ~/.ssh/authorized_keys` → CRIT |
| 常駐 | crontab / LaunchAgents / systemd / shell-rc への追記 → HIGH |

## カテゴリ9: 破壊的ペイロード

| 脅威 | 検出 (`scan_destructive`) |
|---|---|
| 広域削除 | `rm -rf /` `~` `$HOME` `/*` → CRIT |
| fork bomb | `:(){ :\|:& };:` → CRIT |
| ディスク破壊 | `dd if=/dev/zero of=/dev/…`・`mkfs /dev/…`・`> /dev/sd*` → CRIT |
| 一括削除 | `find … -delete`・`chmod -R 000` → HIGH |

## カテゴリ10: パストラバーサル / zip-slip

| 脅威 | 検出 (`scan_path_traversal`) |
|---|---|
| zip-slip | `extractall(` の member 未検証 → HIGH |
| `../` 書込 | `open/writeFile(… ../ … 'w')` → HIGH |

## カテゴリ11: 権限昇格

| 脅威 | 検出 (`scan_privesc`) |
|---|---|
| setuid | `chmod +s` / setuid ビット / `setuid()` → HIGH |
| root 化 | `chown root` → MED |
| sudo | `sudo …` → MED（install script で頻出のため中） |

---

## バージョン管理と新事案への更新

- 検出ルールは `core/util.py` の `RULESET_VERSION`（日付版）で一元管理。全レポートに版を刻む（監査・再現・「いつの脅威まで見たか」の証跡）。
- 新事案が出たら: `core/scan.py` に規則追加 → `fixtures/evil_repo/` に再現 fixture → `tests/smoke.sh` にアサーション → `RULESET_VERSION` を上げ、`CHANGELOG.md` に記録。
- スキャンは既知パターン中心なので、この更新ループが「新種ウイルス/事案への追随」を担う。

## 出典（2025-26）

- MCP tool poisoning / rug-pull（OWASP MCP03）: mcpmanager.ai/blog/tool-poisoning, glasp.co/articles/mcp-security-tool-poisoning-supply-chain, checkmarx.com（11 emerging AI/MCP risks）
- npm サプライチェーン（Shai-Hulud, dependency-confusion）: unit42.paloaltonetworks.com（npm threat landscape）, sonatype（state of the software supply chain 2026）

---

## 全体の設計原則（なぜ「ほぼ防げる」と言えるか）

1. **不実行** — Komainu は取り込んだコードを一切実行しない。スキャン漏れがあっても
   走らなければ実害は出ない。
2. **構造的無害化** — clone 時点で hook/filter/submodule/lifecycle を無効化し、
   自動実行の芽を摘む（P2）。
3. **隔離優先** — 危険物は削除でなく `_QUARANTINE/`（復元可・監査可）。
4. **多層** — shim（全AI・shell）＋ hook（Claude）＋ 各AI routing。片方が抜けても他方。
5. **正直な境界** — SAFE≠実行安全 / regex ゲートは回避可 / 未知は構造で受ける、を明記。

→ スキャン精度ではなく **(1)(2)(3) が実害（コード実行・情報流出）をほぼゼロ化**する。
スキャンは「早期に気づく」ためのシグナル層。
