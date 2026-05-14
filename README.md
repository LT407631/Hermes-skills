# Hermes-skills

## 包含技能

**`multi-agent-team-orchestration/`** — Hermes 多智能体团队编排

通过 Web UI 通讯指派智能体同步会话的完整方案。包括：
- Profile 创建与进程隔离
- 灵魂设定（SOUL.md）、知识库分区
- 总监调度流程（小何派活给 dev/me/op）
- 死循环防治
- 会话同步与数据流

## 首次部署（新电脑）

```bash
# 先进入 Hermes 配置目录
cd ~/.hermes

# 如果有旧 skills 文件夹，先删掉（没有就跳过这步）
rm -rf skills

# 克隆技能仓库
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
