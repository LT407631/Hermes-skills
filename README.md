# Hermes-skills

当前位置：`~/.hermes/skills/` — Hermes Agent 技能仓库
远程仓库：`ssh://git@ssh.github.com:443/LT407631/Hermes-skills.git`

## 核心技能

| 分类 | 技能名 | 说明 |
|------|--------|------|
| `devops/` | **`hermes-webui-cross-profile-sync`** | ⭐ Web UI 跨 Profile 消息同步 — 后端合并+前端3秒轮询，op/me/dev 回复自动显示 |
| `devops/` | `hermes-web-ui-deploy` | Web UI 部署配置（WSL、Node多版本、npm配置） |
| `devops/` | `kanban-orchestrator` | 看板编排 — 分解任务+专家轮值 |
| `devops/` | `kanban-worker` | Kanban worker 使用陷阱和示例 |
| `devops/` | `webhook-subscriptions` | Webhook 事件驱动 |

## 快速使用

```bash
# 加载 skill 查看内容
skill_view(name='hermes-webui-cross-profile-sync')
```

## 首次部署（新电脑）

```bash
git clone ssh://git@ssh.github.com:443/LT407631/Hermes-skills.git ~/.hermes/skills
```

## 更新技能

```bash
cd ~/.hermes/skills && git pull
```

## 推送本地修改

```bash
cd ~/.hermes/skills
git add .
git commit -m "说明"
git push
```

## 完整分类索引

- `apple/` — Apple 生态相关（4 skills）
- `autonomous-ai-agents/` — AI 智能体（Claude Code、Codex、OpenCode）（4 skills）
- `creative/` — 创意生成（ASCII、SVG、漫画、信息图、设计系统等）（20 skills）
- `data-science/` — 数据科学（Jupyter）（1 skill）
- `devops/` — DevOps 与部署（5 skills）
- `dogfood/` — 质量检测（1 skill）
- `email/` — 邮件管理（1 skill）
- `find-skills/` — 技能发现（1 skill）
- `gaming/` — 游戏服务器（2 skills）
- `github/` — GitHub 工作流（PR、Code Review、Issue）（6 skills）
- `marketing/` — B端短视频获客（1 skill）
- `mcp/` — MCP 客户端配置（1 skill）
- `media/` — 媒体处理（YouTube、Spotify、音频）（5 skills）
- `mlops/` — 机器学习运维（13 skills）
- `multi-search-engine/` — 多搜索引擎（1 skill）
- `note-taking/` — 笔记（Obsidian）（1 skill）
- `productivity/` — 生产力工具（Airtable、Notion、Excel、PDF等）（9 skills）
- `red-teaming/` — 红队测试（1 skill）
- `research/` — 学术研究（arXiv、RSS、LLM Wiki等）（7 skills）
- `smart-home/` — 智能家居（Philips Hue）（1 skill）
- `social-media/` — 社交媒体（X/Twitter）（1 skill）
- `software-development/` — 软件开发（调试、测试、规划等）（11 skills）
- `tooling/` — 工具（Obsidian自动化）（1 skill）
- `yuanbao/` — 元宝（1 skill）

总计：**约 94 个 skills**
