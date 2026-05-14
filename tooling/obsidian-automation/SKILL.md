---
name: obsidian-automation
description: "Obsidian 知识库自动化 — 自动归档对话、同步会话记录、维护 Wiki 结构、跨平台上下文恢复"
version: 1.0.0
author: 小何 + 腾哥
metadata:
  domain: tooling
  tags: [Obsidian, 自动化, 归档, 知识库, 上下文管理, 会话同步]
---

# Obsidian 自动化

将 Hermes Agent 的会话/对话自动归档到腾哥的 Obsidian 知识库，实现跨设备上下文恢复和项目管理。

## 适用场景

- 腾哥需要离开设备后（出门/关机）恢复之前的工作上下文
- 项目讨论需要自动存档为 Obsidian 笔记
- 从微信/Hermes 会话中提取关键信息存入知识库
- 跨平台（Web UI ↔ 微信）对话衔接

## 核心机制：Gateway Hook 自动归档

Hermes Gateway 的 event hooks 机制可以在 `agent:end` 事件触发时自动归档对话到 Obsidian。

### Hook 配置

**目录：** `~/.hermes/hooks/auto-archive/`

**文件：**
- `HOOK.yaml` — 声明监听 `agent:end` 事件
- `handler.py` — Python 处理器，从会话 JSON 提取对话并写入 Obsidian

### 归档规则

1. **仅归档 weixin 平台** — 避免 CLI 会话污染知识库
2. **关键词匹配项目目录** — 用户消息包含关键词时存入对应项目目录，否则入 `raw/`
3. **跳过工具调用日志** — 移除超长终端输出噪音（>500 字符）
4. **自动处理文件名冲突** — 重复标题加 `_1`, `_2` 后缀
5. **归档失败不影响主流程** — 钩子错误被捕获，不阻塞 Agent

### 项目目录映射（可配置）

> ⚠️ **2026-05-14 知识库重组**：`raw/` → `小何/`，新增 `dev/`、`me/`、`op/` 目录。
> 原 `微信小程序项目/` 移入 `dev/`，原 `自媒体运营/` 移入 `op/`。
> **归档脚本已同步更新**：`scripts/auto-archive.py` 的 `OBSIDIAN_PROJECTS` 映射路径已对应调整。

在 `handler.py` 的 `OBSIDIAN_PROJECTS` 字典中添加关键词-路径映射：

```python
OBSIDIAN_PROJECTS = {
    "微信小程序": "/mnt/d/Documents/Obsidian Vault/微信小程序项目/03-会话项目记录",
    "webui": "/mnt/d/Documents/Obsidian Vault/微信小程序项目/03-会话项目记录",
    "小程序": "/mnt/d/Documents/Obsidian Vault/微信小程序项目/03-会话项目记录",
}
```

### 手动触发归档

```bash
python3 /home/lt-pc/.hermes/scripts/auto-archive.py
```

### 启用后生效

```bash
hermes gateway restart
```

## Obsidian 目录结构

腾哥的 Obsidian vault 路径：`/mnt/d/Documents/Obsidian Vault/`

### 标准 Wiki 结构（多智能体团队版）

```
Obsidian Vault/
├── _INDEX.md            ← 总入口索引
├── 小何/                ← 总监（小何）文件夹
│   └── soul.md          ← 总监人设
│   └── work-log/        ← 团队工作进度日志
├── dev/                 ← 代码工程师文件夹
│   ├── soul.md          ← dev 人设
│   └── 微信小程序项目/   ← 项目档案（开发相关）
│       ├── 01-方案总览.md
│       ├── 02-数据看板.md
│       └── 03-会话项目记录/ ← 自动归档位置
├── me/                  ← 美工设计师文件夹
│   └── soul.md          ← me 人设
├── op/                  ← 运营专员文件夹
│   ├── soul.md          ← op 人设
│   └── 自媒体运营/      ← 完整运营知识库（原根目录移入）
│       ├── 01-成交体系/
│       ├── 02-邀约话术/
│       ├── 03-客户痛点/
│       ├── 04-转化SOP/
│       ├── 05-竞品分析/
│       ├── 06-脚本库/
│       ├── 07-行业数据/
│       └── 08-日常记录/
└── [其他项目]/          ← 自定义项目目录
    ├── 方案总览.md
    └── 会话项目记录/
```

### 项目目录规范

每个项目应在 Obsidian 中创建独立目录：

```bash
mkdir -p "/mnt/d/Documents/Obsidian Vault/[项目名]/03-会话项目记录"
```

归档脚本会自动创建目录（`os.makedirs(target_dir, exist_ok=True)`）。

## 会话数据格式

Hermes 会话存储在 `~/.hermes/sessions/`，分为两种格式：

### JSON 格式（推荐，微信默认）

```json
{
  "session_id": "20260512_171916_32a684",
  "model": "Qwen3.6-35B-AWQ",
  "base_url": "http://lyxinde.yicp.fun:9999/v1",
  "platform": "weixin",
  "session_start": "2026-05-12T17:19:16.012941",
  "last_updated": "2026-05-12T17:19:30.273833",
  "system_prompt": "...",
  "tools": [...],
  "message_count": 181,
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "tool", "name": "terminal", "content": "..."},
    ...
  ]
}
```

### JSONL 格式（部分会话）

每行一个 JSON 对象，结构类似但无顶层 metadata。

## 归档 Markdown 格式

归档后生成的 Markdown 文件：

```markdown
# [对话主题摘要]

**时间:** 2026-05-12 17:19
**平台:** weixin
**模型:** Qwen3.6-35B-AWQ
**会话ID:** 20260512_171916_32a684
**API地址:** http://lyxinde.yicp.fun:9999/v1
**对话轮次:** 11 轮
**工具调用:** 66 次

---

## 【用户】

[用户消息内容]

---

## 【小何回复】

[AI 回复内容]

---
```

## 手动归档流程（无自动归档时）

当自动归档未配置或未运行时：

1. 列出会话：`ls ~/.hermes/sessions/*.json`
2. 找到目标会话，读取 `messages` 提取 user/assistant 消息
3. 按上述格式整理为 Markdown
4. 写入 Obsidian 对应项目目录

## 跨平台上下文恢复

### 从 Obsidian 恢复上下文

Web UI 或微信中：

```
你是腾哥的全屋定制工厂智能助理小何。当前核心项目：[项目名称]。

【Obsidian知识库】
路径：/mnt/d/Documents/Obsidian Vault/
项目记录：/mnt/d/Documents/Obsidian Vault/[项目目录]/[文件名].md

【工作规则】
1. 每次讨论 [项目] 时，用 read_file 读取记录文件，基于已有内容继续
2. 讨论结束后，立即更新记录文件（追加新内容，不覆盖）
3. 不相关话题不写入记录
4. 更新后用 read_file 确认写入成功

【当前项目状态】
[从记录中总结当前状态]

请确认理解，以后每次聊 [项目] 都按此规则执行。
```

### 更新记录文件

讨论后追加新内容到 Obsidian 文件（append 模式）：

```bash
echo "
---

## [新讨论标题]
[时间、内容...]

---" >> "/mnt/d/Documents/Obsidian Vault/[项目目录]/[文件名].md"
```

## 注意事项

- **自动归档依赖 Gateway 运行** — 如果 Gateway 未运行（如纯 CLI 模式），自动归档不会触发
- **钩子不阻塞主流程** — 归档失败不影响对话，仅打印警告
- **Obsidian vault 在 Windows 上** — WSL 下通过 `/mnt/d/` 挂载访问
- **文件名可能过长** — 如果从用户消息生成标题过长（>40 字符），只保留前 40 字符

## 故障排查

| 问题 | 排查方法 | 解决 |
|------|---------|------|
| 钩子不触发 | `hermes hooks list` | 确认 `HOOK.yaml` 在 `~/.hermes/hooks/auto-archive/` |
| 钩子报 PermissionError | 检查 `.py` 文件权限 | `chmod +x handler.py` |
| 归档文件不存在 | 检查 Obsidian 路径 | `ls '/mnt/d/Documents/Obsidian Vault/'` |
| Gateway 没重启生效 | `hermes gateway restart` | 钩子配置修改后需重启 |
| 中文乱码 | 确认文件编码 | 读写时指定 `encoding="utf-8"` |

## 关联文件

- 归档脚本：`scripts/auto-archive.py`
- Gateway Hook 配置：`references/gateway-hook-configuration.md`
- 项目记录参考：`references/project-management-system-20260512.md`
