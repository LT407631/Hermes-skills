# 微信会话自动归档到 Obsidian 工作流

## 场景

将 Hermes Agent 的微信（Weixin）对话自动归档到 Obsidian 知识库，实现跨设备/跨会话上下文延续。

## 两种方案

### 方案 A：Gateway Event Hooks（推荐，全自动）

在 `~/.hermes/hooks/auto-archive/` 目录下创建 `HOOK.yaml` + `handler.py`：

**HOOK.yaml:**
```yaml
name: auto-archive
description: 微信会话自动归档到 Obsidian
events:
  - agent:end
```

**handler.py 关键逻辑:**
```python
async def handle(event_type: str, context: dict):
    if event_type != "agent:end":
        return
    platform = context.get("platform", "")
    if platform != "weixin":
        return
    # 读取 message/response 内容，生成 Markdown
    # 根据关键词匹配项目目录（如"微信小程序" → 小程序项目文件夹）
    # 写入 Obsidian vault
```

**钩子创建后必须 `hermes gateway restart` 生效。**

### 方案 B：手动 Python 脚本

```bash
# 读取 JSON 会话文件
python3 /home/lt-pc/.hermes/scripts/auto-archive.py

# 会话文件位置: ~/.hermes/sessions/session_YYYYMMDD_HHMMSS_XXXXXX.json
# 输出: /mnt/d/Documents/Obsidian Vault/raw/ 或项目目录
```

## 会话 JSON 格式

Hermes 会话存储为 `.json` 文件，结构:
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
    {"role": "tool", "content": "..."}
  ]
}
```

> 注意: 不是 .jsonl 格式！是完整 JSON 对象含 messages 数组。

## 自动归档后的 Obsidian 目录结构

```
Obsidian Vault/
├── raw/                          ← 无关键词匹配时存入此处
├── 微信小程序项目/
│   └── 03-会话项目记录/          ← 含"微信小程序"关键词的会话
│       ├── 微信小程序开发项目讨论记录.md
│       └── YYYY-MMDD_关键词.md
```

## 项目关键词映射表

| 关键词 | 目标目录 |
|--------|---------|
| 微信小程序 / 小程序 / webui | `/微信小程序项目/03-会话项目记录/` |
| (其他) | `/raw/` |

可通过修改 handler.py 中的 `OBSIDIAN_PROJECTS` 字典扩展映射。

## 注意事项

- 归档只保留有意义的对话（过滤空消息、超长工具日志）
- 同一关键词当日多次对话会生成递增序号文件（`_1.md`, `_2.md`）
- 归档失败不影响主对话流程（non-blocking hook）
- 归档脚本不会自动清理 `raw/` 中不相关的文件，需手动管理
