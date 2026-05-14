# Web UI 前端架构与数据同步机制 (2026-05-14)

## 背景

腾哥通过 Web UI 管理多个 Hermes 智能体（小何、dev、op、me）。小何（AI 助手）需要将 API 派活的结果同步到 Web UI 让腾哥可见。发现了 Web UI 数据同步的根本机制。

## 核心技术发现

### 1. 前端使用 socket.io（不是原生 WebSocket）

Web UI 前端通过 socket.io 连接到 gateway 的 `/chat-run` 命名空间：

```javascript
// 关键代码片段（从 index.js 反编译）
Y = Hn(`${o}/chat-run`, {
  auth: { token: e },           // e = 来自 localStorage hermes_api_key 或 .token 文件
  query: { profile: n },        // n = 当前 profile 名称
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 10000,
});
```

### 2. Socket.io 事件清单

| 事件名 | 方向 | 数据示例 | 说明 |
|--------|------|----------|------|
| `message.delta` | gateway → 前端 | `{session_id, content, delta}` | 流式消息内容 |
| `reasoning.delta` | gateway → 前端 | `{session_id, content}` | 推理过程 |
| `thinking.delta` | gateway → 前端 | `{session_id, content}` | 思考过程 |
| `run.started` | gateway → 前端 | `{session_id, run_id}` | 运行开始 |
| `run.completed` | gateway → 前端 | `{session_id, run_id}` | 运行完成 |
| `run.failed` | gateway → 前端 | `{session_id, error}` | 运行失败 |
| `run.queued` | gateway → 前端 | `{session_id, position}` | 排队通知 |
| `tool.started` | gateway → 前端 | `{session_id, tool_name}` | 工具开始调用 |
| `tool.completed` | gateway → 前端 | `{session_id, tool_name, result}` | 工具调用完成 |
| `abort.started` | gateway → 前端 | `{session_id}` | 中止开始 |
| `abort.completed` | gateway → 前端 | `{session_id}` | 中止完成 |
| `usage.updated` | gateway → 前端 | `{session_id, tokens}` | 用量更新 |
| `run` | 前端 → gateway | `{session_id, messages, ...}` | 发送消息请求 |
| `abort` | 前端 → gateway | `{session_id}` | 请求中止 |
| `resume` | 前端 → gateway | `{session_id}` | 恢复会话 |

### 3. Vue Pinia 状态管理

Web UI 使用 Vue 3 + Pinia 状态管理。通过 CDP 访问：

```javascript
document.querySelector('#app').__vue_app__.config.globalProperties.$pinia
// → 包含 stores: { app, chat, profiles, settings, session-browser-prefs, files }
```

**chat store 的核心结构：**
```javascript
{
  sessions: [
    { id: "mp5guacelv7uea", title: "小何与op", source: "api_server",
      messages: [{ id, role, content, timestamp }, ...], ... }
  ],
  activeSessionId: "mp5guacelv7uea",
  activeSession: { /* 当前会话完整对象含 messages */ },
  focusMessageId: null,
  isLoadingSessions: false,
  sessionsLoaded: true,
  isLoadingMessages: false
}
```

### 4. 数据加载机制

**页面初始加载时：**
```
浏览器加载 SPA
  → fetch GET /api/hermes/sessions         (会话列表)
  → fetch GET /api/hermes/sessions/:id     (当前会话消息)
  → 数据存入 Pinia store
  → 建立 socket.io 连接到 /chat-run
  → DOM 渲染
```

**切换会话时：**
```
用户点击另一个会话
  → 从 Pinia chat.sessions 缓存读取（不调 API）
  → DOM 更新显示新会话消息
  → NO network request
```

**发消息时（正常流程）：**
```
用户在输入框打字 → 点击发送
  → socket.emit("run", { session_id, messages })
  → gateway 处理请求，调用 LLM
  → socket.on("message.delta", ...)        ← 流式推送
  → Pinia store 实时更新
  → DOM 实时显示
  → socket.on("run.completed", ...)        ← 运行完成
```

### 5. Web UI 后端 API 端点

| 方法 | 路径 | 用途 | 数据来源 |
|------|------|------|----------|
| GET | `/api/hermes/sessions` | 会话列表 | `state.db` (node:sqlite 直读) → fallback `hermes sessions export` CLI |
| GET | `/api/hermes/sessions/:id` | 指定会话消息 | `hermes sessions export --session-id <id>` CLI |
| DELETE | `/api/hermes/sessions/:id` | 删除会话 | `hermes sessions delete` CLI |
| POST | `/api/hermes/sessions/:id/rename` | 重命名 | `hermes sessions rename` CLI |

## 数据同步实验记录

### 实验 1：Python 写数据库（WAL 模式）

```python
conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('BEGIN IMMEDIATE')
conn.execute('INSERT INTO messages (...) VALUES (...)')
conn.commit()
conn.close()
```
**结果**： ✅ 数据写入成功  ❌ 前端不显示  ❌ F5 才显示

### 实验 2：Python 写双库（state.db + hermes-web-ui.db）

写 `op/state.db`（让 gateway 知道）+ `hermes-web-ui.db`（让 Web UI 知道）。
**结果**： ✅ 双库写入成功  ❌ 前端仍不显示

### 实验 3：通过 Web UI 反向代理 gateway API

```
POST /v1/chat/completions -H "Authorization: Bearer <token>"
  → Web UI proxy 转发到 gateway
  → gateway 处理后推送 socket.io
```
**结果**： ✅ 消息发送成功（双库都有数据） ❌ 前端不自动显示（需要用户切会话或 F5）

### 实验 4：CDP 模拟点击切换会话

```javascript
document.querySelectorAll('.session-item')[1].click(); // 切到另一个会话
setTimeout(() => document.querySelectorAll('.session-item')[0].click(), 500); // 切回来
```
**结果**： ✅ 能切换会话  ❌ 数据仍不刷新（因为 Pinia 缓存不重新请求后端）

## 结论

1. **直接写数据库不是正确路径** — 前端不直接读数据库，只认 API + socket.io 推送
2. **socket.io 不广播"数据已更新"事件** — 只广播流式消息和运行状态
3. **Pinia 缓存会"卡住"旧数据** — 切换会话不从后端重新请求
4. **唯一靠谱的同步方式**：用户手动 F5 刷新，或通过正确链路（gateway API → socket.io）发送消息
5. **如果要在 Web UI 中看到新数据，用户必须手动**：
   - 刷新页面（F5 / Ctrl+R）
   - 或切到其他会话再切回当前会话
