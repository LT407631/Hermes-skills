# Gateway Hook 自动归档 — HOOK.yaml 配置

## 目录结构

```
~/.hermes/hooks/auto-archive/
├── HOOK.yaml
└── handler.py
```

## HOOK.yaml

```yaml
name: auto-archive
description: Auto-archive weixin sessions to Obsidian when agent ends
events:
  - agent:end
```

## handler.py

完整代码见 `scripts/auto-archive.py`。核心逻辑：

1. 接收 `agent:end` 事件
2. 仅处理 `weixin` 平台
3. 跳过无内容的消息和超长工具日志
4. 根据用户消息关键词匹配项目目录
5. 生成 Markdown 归档到 Obsidian

## 事件类型

Hermes Gateway 支持的 hook 事件：

| 事件 | 触发时机 | 上下文字段 |
|------|---------|-----------|
| `agent:start` | Agent 开始处理消息 | platform, user_id, session_id, message |
| `agent:step` | 每次 tool-calling 循环 | platform, user_id, session_id, iteration, tool_names |
| `agent:end` | Agent 完成处理 | platform, user_id, session_id, message, response |
| `session:start` | 新会话创建 | platform, user_id, session_key |
| `session:end` | 会话结束 | platform, user_id, session_key |
| `session:reset` | 用户 /new 或 /reset | platform, user_id, session_key |

## 注意事项

- **仅钩在 `agent:end` 触发归档** — `agent:start` 时对话未完成
- **handler 必须是 `async def handle(event_type, context)`** — 命名固定
- **钩子错误不阻塞主流程** — 异常被捕获
- **修改配置后需重启 Gateway** — `hermes gateway restart`
