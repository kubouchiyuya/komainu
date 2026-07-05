<div align="center">

# 🛡️ 狛犬 / Komainu

**在你的 AI 触碰任何 repo、skill、plugin 之前，它们都必须先经过这道门。**

无论是 clone 还是 install → 先深度扫描 → 使危险内容无害化 → 交还一份干净的副本。
它*从不执行被检查的代码*。

[![CI](https://github.com/kubouchiyuya/komainu/actions/workflows/ci.yml/badge.svg)](https://github.com/kubouchiyuya/komainu/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Pure Python](https://img.shields.io/badge/deps-zero%20(python%20stdlib)-black.svg)](#-快速开始)
[![Platforms](https://img.shields.io/badge/mac%20%7C%20linux%20%7C%20windows-black.svg)](#-适配所有ai所有系统)
[![Agents](https://img.shields.io/badge/Claude%20%7C%20OpenAI%20%7C%20Grok%20%7C%20Gemini%20%7C%20Cursor-black.svg)](#-适配所有ai所有系统)

[English](README.md) · [日本語](README.ja.md) · [Docs](skills/komainu/docs/index.md) · [Threat model](skills/komainu/references/threat-model.md)

**如果 Komainu 保护了你的安装，点一个 ⭐ 能帮助其他开发者发现它。**

</div>

---

你的 AI 每天都在安装陌生人写的代码 —— skill、plugin、repo、package。它会把这些文件
**当作指令来读取**，并**代替你**运行其中的脚本，而且是以机器的速度，通常没有人在
旁边盯着。一个被污染的文件，就能把你信赖的代理变成别人的工具，而你可能永远都不会
发现。

**狛犬补上了这道缺失的权限门。** 它的名字来自神社门前驱邪避凶的守护兽 —— 它以
只读方式 clone 代码，从每个文件中查找第三方代码攻击*代理*的各种手法，把危险内容
隔离（绝不删除），然后交还一份干净的副本 —— 或者直接拒绝。**做这一切的过程中，
没有执行任何代码。**

```bash
komainu import https://github.com/owner/repo
#   → SAFE      可以使用
#   → REVIEW    需要人工先看一眼
#   → DANGER    拒绝
```

## ✨ 核心能力

- **按攻击者武器化代码的方式来读取代码** —— 覆盖 **11 大类**：提示词注入、自动
  执行陷阱、机密数据外泄、伪装的恶意代码、护栏篡改、供应链/依赖风险、MCP 工具
  投毒、持久化与反弹 shell、破坏性载荷、路径穿越、以及权限提升。
- **从不执行被检查的内容。** 只读的静态分析。永远不会被触发的陷阱，也就无法
  伤人 —— 这是全部的安全保证。
- **只隔离，绝不删除。** 所有危险内容都会连同清单一起移入 `_QUARANTINE/`，你可以
  随时查看、恢复，或者不管它。
- **对任何代理都自动生效。** PATH shim 会拦截*任何*会调用 shell 的工具发起的
  clone/install —— Claude Code、OpenAI Codex、Grok、Cursor、Aider、Gemini CLI ——
  再加上一个确定性的 Claude Code hook。
- **零依赖。** 纯 Python 标准库。在 macOS、Linux、Windows 上给出完全相同的判定。
- **诚实、不夸大。** `SAFE` 的意思是"没有静态威胁 + 没有任何东西会自动执行"，
  而不是"可以放心运行任何东西"。文档从不夸大其词。

## 🚀 快速开始

```bash
# 作为 Claude Code 插件
claude plugin marketplace add kubouchiyuya/komainu
claude plugin install komainu

# 开启通用 shell 网关（适用于任何会调用 shell 的代理）
komainu install-shims
echo 'export PATH="$HOME/.komainu/bin:$PATH"' >> ~/.zshrc
```

之后就可以检查任何东西：

```bash
komainu import https://github.com/owner/repo   # clone → 扫描 → 无害化 → 报告
komainu scan ./local/dir                       # 检查你手头已有的代码
komainu selfcheck                              # 检查你的运行环境
sh skills/komainu/tests/smoke.sh               # 16 条离线断言
```

> **提示：** 给这个仓库点 star **不会**安装任何东西 —— star 本身到达不了你的机器。
> 真正的安装靠那一条命令完成，这两件事都可以交给你的 AI 去做。

## 🚪 它拦截的危险 —— 11 大类

| 危险 | 通俗地说 | Komainu 的应对 |
|---|---|---|
| 🩹 **提示词注入** | 隐藏的 README 一行字，命令你的 AI 泄露密钥 | 检测面向 AI 的文本（中/英/日）+ 不可见/双向 unicode；隔离并清除隐藏字符 |
| ⚡ **自动执行** | 一 clone/打开/`npm install` 就自动运行 | 在 clone 阶段就拆解 git hooks、`.gitattributes` filter、submodule、生命周期脚本、`.vscode`/`.envrc`/`.pth`/`conftest.py`/`build.rs` |
| 📤 **数据外泄** | 读取 `~/.ssh`/`.env` 并 `curl` 发送出去 | 标记"读取机密+联网"、`curl \| sh`、外发 POST —— 发现即隔离 |
| 🧬 **伪装恶意代码** | base64 数据块、不透明二进制文件 | 标记动态代码求值、编码载荷、不透明二进制、误提交的密钥 |
| 🔓 **护栏篡改** | 改写你的 `settings.json`/`CLAUDE.md`/hook 来关闭防护 | 专门监视 → **直接拒绝** |
| 📦 **供应链风险** | 依赖来自 git/URL、registry 覆盖、无 lockfile | 检测依赖混淆与版本未锁定（npm Shai-Hulud 时代的手法） |
| 🧩 **MCP 工具投毒** | 藏在 MCP 工具描述里的隐藏指令 | 对应 OWASP MCP03 —— 检测被投毒的描述及远程拉取型服务命令 |
| 🕳️ **持久化 / 后门** | 反弹 shell、cron 任务、被添加的 SSH 密钥 | 检测 `/dev/tcp`、`nc -e`、`authorized_keys`、cron/launchd/systemd |
| 💥 **破坏性操作** | `rm -rf /`、fork bomb、清空磁盘 | 检测大范围删除、fork bomb、`dd`/`mkfs` |
| 🧨 **路径穿越** | zip-slip、写入到仓库之外 | 检测 `extractall`、`../` 写入 |
| ⬆️ **权限提升** | setuid、`sudo`、`chown root` | 检测 setuid 位、`sudo`、root 所有权变更 |

完整分类与残余风险分析 → [threat-model.md](skills/komainu/references/threat-model.md)。

## 🧭 工作原理

共 10 个阶段，第 2–5 阶段**不会**触碰任何正在运行的代码。拦截 → 最小化只读
clone（锁定 SHA、丢弃 `.git`、关闭 filter/hook）→ 扫描 → 无害化 → 判定 →
沙箱安装（`--ignore-scripts`、无网络）→ 再验证 → 优化 → 激活 → 审计。深入了解 →
[how-it-works](skills/komainu/docs/how-it-works.md)。

## 🧪 测试 / CI

| 命令 | 用途 |
|---|---|
| `sh skills/komainu/tests/smoke.sh` | 16 条离线断言：每个类别都能检测、无害化、干净 repo 能通过、shim 能拦截 |
| GitHub Actions (`ci.yml`) | 每次 push 都会运行 smoke 套件 —— 上方的徽章就是证明 |

## 🌐 适配所有 AI，所有系统

两层强制执行，即便一层被绕过，另一层依然生效。扫描引擎是单一的纯 Python 实现，
因此**判定在任何环境下都完全一致** —— 不同的只是强制执行层。

| 层级 | 覆盖范围 | 强度 |
|---|---|---|
| **PATH shim** | 任何会调用 shell 的代理（Claude Code、OpenAI Codex、Grok、Cursor、Aider、Gemini CLI）—— macOS/Linux，Windows 上为 PowerShell | 强 / 确定性 |
| **Claude Code hook** | Claude Code 内通过 Bash 工具发起的 clone | 强 / 确定性 |
| **路由片段** | 通过各自配置文件引导 Codex / Grok / Cursor / Gemini | 建议性 |

## ⚖️ 诚实的局限

- `SAFE` ≠ 可以放心运行任何东西 —— 它的意思是"没有静态威胁 + 没有自动执行"。
- 静态扫描可能会漏掉新型或经过混淆的载荷；真正的防线是*什么都不会运行*，而不是
  一份规则列表。
- 正则式的关卡是可以被绕过的 —— `KOMAINU_BYPASS=1` 是经过审计的例外通道。
- 如果一个 repo 的全部目的就是恶意的，清理它就等于抹掉它的功能，因此 Komainu 会
  直接拒绝（DANGER），而不是交出一份空壳副本。

## 🤝 贡献与安全

- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- 发现漏洞？→ [SECURITY.md](SECURITY.md)（请不要为此开公开 issue）

## 📜 许可证

MIT —— 详见 [LICENSE](LICENSE)。当 Komainu 导入第三方代码时，会保留源代码的
LICENSE 与署名信息。

<div align="center">

在门口立一位守护者，这样你的 AI 就不必盲目信任陌生人。

</div>
