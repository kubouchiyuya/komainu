<div align="center">

# 🛡️ 狛犬 / Komainu

**あなたの AI が触れる前に、すべての repo・skill・plugin が通る門。**

clone も install も → まず徹底スキャン → 危険を無害化 → クリーンな形で返す。
*検査対象のコードは一切実行しない。*

[![CI](https://github.com/kubouchiyuya/komainu/actions/workflows/ci.yml/badge.svg)](https://github.com/kubouchiyuya/komainu/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Pure Python](https://img.shields.io/badge/deps-zero%20(python%20stdlib)-black.svg)](#-クイックスタート)
[![Platforms](https://img.shields.io/badge/mac%20%7C%20linux%20%7C%20windows-black.svg)](#-全ai全os)
[![Agents](https://img.shields.io/badge/Claude%20%7C%20OpenAI%20%7C%20Grok%20%7C%20Gemini%20%7C%20Cursor-black.svg)](#-全ai全os)

[English](README.md) · [中文](README.zh.md) · [Docs](skills/komainu/docs/index.ja.md) · [脅威モデル](skills/komainu/references/threat-model.md)

**導入を守れているなら、⭐ を。他の開発者が見つけやすくなります。**

</div>

---

あなたの AI は毎日、見知らぬ他人のコードを取り込みます — skill・plugin・repo・
package。AI はそのファイルを**指示として読み**、スクリプトを**あなたの代わりに
実行**します。機械速度で、たいてい誰も見ていない中で。汚染ファイル1つが、頼れる
相棒を他人の道具に変える — そして自動ワークフローの中で起きるため、**気づけない
かもしれない。**

**狛犬は、その欠けている「権限の門」です。** 社の門で邪を祓う守護獣の名の通り、
read-only clone し、第三者コードが*エージェント*を攻める手口を全ファイルから読み、
危険物を隔離（削除はしない）し、クリーンなコピーを返す — あるいは拒否する。
**これを一切コードを実行せずに行います。**

```bash
komainu import https://github.com/owner/repo
#   → SAFE      使ってよい
#   → REVIEW    人が先に確認
#   → DANGER    拒否
```

## ✨ 主な機能

- **攻撃者の武器化のしかたでコードを読む** — **11カテゴリ**: 注入・自動実行・
  情報流出・偽装マルウェア・ガードレール改竄・サプライチェーン・MCP汚染・
  永続化/逆シェル・破壊・パストラバーサル・権限昇格。
- **検査対象を実行しない。** 読み取り専用の静的解析。発動しない罠は無害 — これが核。
- **削除でなく隔離。** 危険物は控え付きで `_QUARANTINE/` へ。確認も復元も可。
- **全 AI で自動発火。** PATH shim がシェルを叩く*あらゆる*もの（Claude Code /
  OpenAI Codex / Grok / Cursor / Aider / Gemini CLI）を捕捉 ＋ Claude Code hook。
- **依存ゼロ。** Python 標準ライブラリのみ。mac/Linux/Windows で同一判定。
- **正直な設計。** `SAFE` は「静的脅威なし＋自動実行なし」で「何でも実行して安全」
  ではない。過大表示しない。

## 🚀 クイックスタート

```bash
# Claude Code プラグインとして
claude plugin marketplace add kubouchiyuya/komainu
claude plugin install komainu

# 全AI共通のシェルゲートを有効化
komainu install-shims
echo 'export PATH="$HOME/.komainu/bin:$PATH"' >> ~/.zshrc
```

```bash
komainu import https://github.com/owner/repo   # clone → scan → 無害化 → レポート
komainu scan ./local/dir                       # 手元の物を検査
sh skills/komainu/tests/smoke.sh               # オフライン16アサーション
```

> **Tip:** star してもインストールされません（star は PC に届かない）。実際の導入は
> 1コマンド。AI に両方任せられます。

## 🚪 止める危険 — 11カテゴリ

| 危険 | 平易にいうと | 狛犬 |
|---|---|---|
| 🩹 **注入** | 隠し README 行が AI に鍵を漏らせと命令 | AI 宛て文（英日中）＋不可視 unicode を検出・隔離・除去 |
| ⚡ **自動実行** | clone/開く/`npm install` の瞬間に走る | git hooks・filter・submodule・lifecycle・`.vscode`/`.envrc`/`.pth`/`conftest.py`/`build.rs` を clone 時に無効化 |
| 📤 **情報流出** | `~/.ssh`/`.env` を読んで `curl` 送信 | 秘密読取＋通信・`curl \| sh`・外向き POST を即隔離 |
| 🧬 **偽装マルウェア** | base64 blob・不透明バイナリ | 動的コード評価・エンコード payload・不透明バイナリ・混入 secret を検出 |
| 🔓 **ガードレール改竄** | `settings.json`/`CLAUDE.md`/hook を書き換えて守りを切る | 専用監視 → **拒否** |
| 📦 **サプライチェーン** | git/URL 由来の依存・registry 上書き・lock 無し | dependency-confusion・版未固定を検出（npm Shai-Hulud 時代） |
| 🧩 **MCP tool poisoning** | MCP tool の description に隠した命令 | OWASP MCP03 — 汚染 description＋remote-fetch サーバを検出 |
| 🕳️ **永続化/バックドア** | 逆シェル・cron・SSH 鍵追加 | `/dev/tcp`・`nc -e`・`authorized_keys`・cron/launchd/systemd を検出 |
| 💥 **破壊** | `rm -rf /`・fork bomb・ディスク破壊 | 広域削除・fork bomb・`dd`/`mkfs` を検出 |
| 🧨 **パストラバーサル** | zip-slip・repo 外書込 | `extractall`・`../` 書込を検出 |
| ⬆️ **権限昇格** | setuid・`sudo`・`chown root` | setuid ビット・`sudo`・root 化を検出 |

完全分類 → [threat-model.md](skills/komainu/references/threat-model.md)

## 🧭 仕組み

10フェーズ・フェーズ2〜5は**一切コードを走らせない**。遮断→最小 read-only clone（SHA固定・
`.git`破棄・filter/hook無効）→scan→無害化→判定→sandbox install→再検証→最適化→
活性化→監査。詳細 → [how-it-works](skills/komainu/docs/how-it-works.md)

## 🧪 テスト / CI

| コマンド | 目的 |
|---|---|
| `sh skills/komainu/tests/smoke.sh` | 10 アサーション（検出・無害化・クリーン通過・shim 遮断） |
| GitHub Actions (`ci.yml`) | push ごとに smoke 実行 — 上のバッジが証拠 |

## 🌐 全AI・全OS

2層強制。片方が破られてももう片方が持つ。スキャンエンジンは単一 pure-Python なので
**判定は全環境で同一**、違うのは強制層だけ。

| 層 | 対象 | 強度 |
|---|---|---|
| **PATH shim** | シェルを叩く全 AI（Claude/OpenAI Codex/Grok/Cursor/Aider/Gemini）mac/Linux・Windows は PowerShell | 強・決定論的 |
| **Claude Code hook** | Claude Code 内の Bash clone | 強・決定論的 |
| **routing スニペット** | Codex/Grok/Cursor/Gemini を各設定で誘導 | 助言的 |

## ⚖️ 正直な限界

- `SAFE` ≠ 実行して安全 — 「静的脅威なし＋自動実行なし」の意味。
- 静的スキャンは新種/難読化を漏らしうる。真の壁は*何も走らない*こと。
- regex ゲートは回避可 — `KOMAINU_BYPASS=1` が監査付き抜け道。
- 目的自体が悪意なら、消すと機能が消える → 空洞を渡さず DANGER で拒否。

## 🔗 関連プロジェクト

- 🧭 **[羅針盤 / Rashinban](https://github.com/kubouchiyuya/rashinban)** — 自律
  エージェントのゴールの羅針盤。ラフ依頼を検証可能な `/goal` に。狛犬は*入ってくる物*を
  守り、羅針盤は*向かう先*を定める。

## 🤝 コントリビュート & セキュリティ

- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- 脆弱性は → [SECURITY.md](SECURITY.md)（公開 issue にしないでください）

## 📜 ライセンス

MIT — [LICENSE](LICENSE) 参照。第三者コード取り込み時は元の LICENSE と帰属を保持。

<div align="center">

門に守護を立て、あなたの AI が見知らぬ他人を盲信せずに済むように。

</div>
