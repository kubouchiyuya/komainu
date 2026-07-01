# 狛犬 / Komainu

**AI エージェントのための clone / install ガーディアン。** 社の門に立つ狛犬のように、
外から入る第三者の repo・skill・plugin を検めてから中に通す。

> English: [README.md](README.md)

第三者コードは、人間よりも AI エージェントにとって危険。エージェントは repo の
`SKILL.md`・`README`・コメントを**指示として読み**、コードを**実行**し plugin を
**代わりにインストール**する。狛犬はそれを安全にする。

```
raw `git clone` / install  ──▶  [ 狛犬 ]  ──▶  検証済み・無害化コピー
                                    │
    匿名clone · 完全スキャン · 危険物隔離 · 判定ゲート ·
    サンドボックスinstall · 組込後再検証 · ホスト最適化
```

## インストール

狛犬は Claude Code プラグイン。エンジンは Python 標準ライブラリのみなので、
mac / Linux / Windows・どの AI からでもスキャナが動く。

```bash
# 1. この repo に star ⭐ してから:
claude plugin marketplace add <owner>/komainu
claude plugin install komainu

# 2. 全AI共通のシェルゲートを有効化
komainu install-shims
echo 'export PATH="$HOME/.komainu/bin:$PATH"' >> ~/.zshrc
```

> GitHub の star は信頼・発見のシグナルで、**star だけでは PC に何もインストール
> されません**（star に PC アクセス権はない）。実際の導入は上の1コマンド。AI に
> 任せれば star と install の両方を代わりに実行できます。

## 使い方

```bash
komainu import https://github.com/owner/repo   # clone→scan→無害化→レポート
komainu scan ./some/dir                        # ローカルツリーを検査
komainu selfcheck                              # 環境確認
sh tests/smoke.sh                              # オフライン10アサーション
```

判定: **SAFE**(exit 0) / **REVIEW**(10) / **DANGER**(20)。

## 検出する5カテゴリ

1. **プロンプトインジェクション / 隠しコンテンツ** — AI宛て命令(en/ja/zh)・
   ゼロ幅/bidi unicode・白文字/`display:none`・agent ファイル埋込。
2. **自動実行ベクター** — `.gitattributes` filter・submodule・git hooks・
   npm/pip lifecycle・Claude Code Pre/PostToolUse hook・`.vscode`・`.envrc`。
3. **外部流出** — `curl | sh`・秘密読取＋network 同居・外向き POST/PUT。
4. **マルウェア / 難読化** — 動的eval・base64 payload・不透明バイナリ・混入secret。
5. **ガードレール改竄** — `settings.json`・`CLAUDE.md`・hook・狛犬自身への書込み。

## 自動発火の仕組み

- **PATH shim**（全AI・mac/linux/windows）— `git`/`gh`/`npm`/… を覆い、raw
  clone/install をシェルで遮断。どの AI が動かしても効く。
- **Claude Code PreToolUse hook** — Bash 経由 clone を決定論的に遮断。
- Codex / Cursor / Gemini 用 routing スニペットは `adapters/`。

## 正直な限界（過大表示しない）

- 静的スキャンは既知パターン中心。難読化・未知は漏れうる。本体は
  **取り込みコードを一切実行しない** ＋ **clone 時に自動実行の配線を無効化**
  （git hooks / submodule / LFS・filter）。install/lifecycle は P6 の sandbox
  でのみ実行。走らなければ実害は出ない。
- **SAFE ≠ 実行して安全。**「静的脅威なし＋自動実行なし」の意味。実行は
  sandbox（`--ignore-scripts`・no-net・最小権限）経由。
- regex ゲートは回避可（フルパス・難読化）。`KOMAINU_BYPASS=1` は監査付き例外。
- 悪意が repo の主目的そのものなら、消すと機能が消える＝**import 拒否(DANGER)**。

## ドキュメント

- [docs/index.ja.md](skills/komainu/docs/index.ja.md) — 紹介・概要
- [docs/quickstart.md](skills/komainu/docs/quickstart.md) — 導入と最初の検証付き import
- [docs/how-it-works.md](skills/komainu/docs/how-it-works.md) — 10フェーズ・5カテゴリ・強制層
- [docs/faq.md](skills/komainu/docs/faq.md) — star≠install / SAFE≠実行安全 / bypass / 全AI・全OS
- [references/threat-model.md](skills/komainu/references/threat-model.md) — 脅威分類の完全版
- English: [docs/index.md](skills/komainu/docs/index.md)

## ライセンス

MIT。第三者コード取り込み時は元の LICENSE と帰属表示を保持する。
