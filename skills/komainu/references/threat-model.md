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
| `.gitattributes` filter/clean/smudge/process | checkout 時にコマンド実行(RCE) | driver 検出→隔離。**clone時に先行無効化** |
| `.gitmodules` submodule | `--recurse` で外部コード取得 | 存在検出。Komainu は非再帰 clone |
| git hooks / `.githooks` / core.hooksPath | git 操作でスクリプト実行 | 存在検出→隔離。clone時 hooksPath=/dev/null |
| npm lifecycle (pre/post install, prepare) | `npm install` で任意実行 | package.json 解析→flag。install は `--ignore-scripts` |
| setup.py / Makefile | build/install 時実行 | パターン検出 |
| **Claude Code hooks** (Pre/PostToolUse) | エージェントの tool 使用で自動発火 | hooks.json/settings.json 解析→shell 付きは CRITICAL |
| `.vscode/tasks.json`(runOn folderOpen) / `.devcontainer` / `.envrc` | エディタ/cd で自動実行 | 存在検出→隔離 |

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
