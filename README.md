# Hermes-skills

## 包含技能

**`devops/web-ui-pinia-refresh/`** — Web UI 前端刷新方案（v3.0）
通过 Chrome CDP 操作 Pinia store 刷新前端页面，无需手动 F5 或重启网关。

## 首次部署（新电脑）

```bash
cd ~/.hermes
mv skills skills.bak  # 或 rm -rf skills
git clone git@github.com:LT407631/Hermes-skills.git skills
```

## 更新技能

```bash
cd ~/.hermes/skills && git pull
```

## 推送本地修改（仅限主电脑）

```bash
cd ~/.hermes/skills
git add .
git commit -m "修改内容说明"
git push
```
