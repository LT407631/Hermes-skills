# 外部技能市场发现（skills.sh）

## 背景

2026-05-08 及后续在 skills.sh 生态中搜索与抖音运营、搜索引擎相关的技能，记录可用资源及迁移方法。

## 查找命令速查

| 生态系统 | 搜索命令 | 安装命令 |
|----------|---------|---------|
| **Hermes Hub** | `hermes skills search <query>` | `hermes skills install <id>` |
| **Hermes（直接 URL）** | — | `hermes skills install <https://.../SKILL.md> --name <name> -y` |
| **skills.sh 生态** | `npx skills find <query>` | `npx skills add <owner/repo@skill>` 或 `npx skills add <repo_url> --skill <name> -g -y` |

## ⚠️ 生态兼容性说明

skills.sh 的技能是为 **Claude Code / Codex / Cursor / Copilot** 设计的，和 Hermes 是不同的 AI Agent 生态。`npx skills add` 安装后的技能无法直接在 Hermes 中使用。

### 从 skills.sh 迁移到 Hermes 的方法

1. `npx skills find <query>` 找到需要的技能
2. 通过 skills.sh 或 skilld.dev 页面找到原始 SKILL.md 的 raw GitHub URL
3. `curl -sL <raw SKILL.md URL>` 查看内容
4. 方法 A：`hermes skills install <raw SKILL.md URL> --name <name> -y`
5. 方法 B：`skill_manage(action='create', name='<name>', content='<SKILL.md 完整内容>')`
6. 方法 C：手动创建 skill 文件到 `~/.hermes/skills/<name>/SKILL.md`

### npx skills add 常见失败原因

| 错误 | 原因 | 解决 |
|------|------|------|
| `No matching skills found` | `--skill` 参数指定的 skill 名不对 | 换用 npx skills find 确认准确的 skill 名和路径 |
| `No valid skills found` | 仓库克隆成功但找不到 SKILL.md | 直接走 raw URL 安装法 |
| `Authentication failed` | 仓库源不是 GitHub | 走 raw URL 安装法 |
| 超时 | 仓库过大（678+ skills） | 直接找 raw SKILL.md URL |

## 已安装的外部技能

| 技能名 | 来源 | 安装方式 | 状态 |
|--------|------|---------|------|
| `find-skills` | Hermes Hub | `hermes skills install find-skills -y` | ✅ |
| `multi-search-engine` | aaaaqwq/agi-super-skills (skills.sh) | 获取 raw SKILL.md → skill_manage create | ✅ |

## douyin-analytics

| 属性 | 值 |
|------|-----|
| 来源 | modelscope.cn（skills.sh） |
| 安装量 | 21 |
| 可用性 | ⚠️ 安装量极低，仓库链接失效 |
| 建议 | **不安装**。Hermes 已有 `scrapling` + `short-video-b2b-acquisition` + 抖音绕过方案，覆盖所有需求 |

## multi-search-engine

| 属性 | 值 |
|------|-----|
| 来源 | aaaaqwq/claude-code-skills（skills.sh）→ aaaaqwq/agi-super-skills |
| 安装量 | 2.7K |
| GitHub 星 | 56 |
| 安全扫描 | ✅ Pass × 2 (Agent Trust Hub, Socket) / ⚠️ Warn (Snyk) |
| 安装方式 | skill_manage(action='create') — 从 raw SKILL.md 手动创建 |
| SKILL.md 内容 | 多搜索引擎聚合查询——17 个搜索引擎一站式检索 |

### 支持的搜索引擎

| 区域 | 引擎 |
|------|------|
| CN | 百度、Bing CN、360、搜狗、头条搜索、微信搜狗、集思录 |
| Global | Google、Google HK、DuckDuckGo、Yahoo、Startpage、Brave、Ecosia、Qwant、WolframAlpha |

### 已安装路径

`~/.hermes/skills/multi-search-engine/SKILL.md`

### 使用策略

作为 `web_search` 的备用方案。当 web_search 不可用或结果不佳时自动切换。
