# Hermes-skills

Hermes Agent 技能仓库，包含短视频运营、多智能体协作、Web UI 部署等所有自定义技能。

## 首次部署（新电脑）

```bash
# 1. 先备份现有的 skills（如果有）
cd ~/.hermes
mv skills skills.bak  # 或者直接 rm -rf skills

# 2. 克隆仓库
git clone git@github.com:LT407631/Hermes-skills.git skills

# 3. 重启 Hermes 让新技能生效
hermes restart
# 或手动重启 gateway
```

## 更新技能（日常）

```bash
cd ~/.hermes/skills
git pull
```

## 推送本地修改（仅限主电脑）

```bash
cd ~/.hermes/skills
git add .
git commit -m "改了啥写啥"
git push
```

## 仓库结构

- `marketing/short-video-b2b-acquisition/` — 短视频获客运营
- `software-development/multi-agent-team-orchestration/` — 多智能体协作
- `devops/web-ui-pinia-refresh/` — Web UI 前端刷新方案
- `devops/hermes-web-ui-deploy/` — Hermes Web UI 部署
- `creative/sketch/` — UI 草图设计系统
- 其他为 Hermes 官方技能
