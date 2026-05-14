# Web UI Pinia Refresh — 调试记录

## 背景

时间：2026-05-14
问题：通过 API/CLI 向 op gateway 发送消息后，数据已在 state.db 中，但 Web UI 前台不显示。
之前的解法：用户手动 F5 刷新 或 重启 gateway → socket.io 重连 → 触发 reload

## 调试过程

### 步骤 1：确认数据已写入数据库

- op/state.db 有 session "mp5guacelv7uea"（小何与op），86 条消息 ✅
- hermes-web-ui.db 有相同会话，74（后变72）条消息 ✅
- default/state.db 没有此会话 ❌

### 步骤 2：调查前端加载机制

通过 CDP Runtime.evaluate 反编译 Web UI 的 JS 代码：

**socket.io 连接（不是普通 WebSocket）：**
```javascript
Y = Hn(`${o}/chat-run`, {
    auth: { token: e },
    query: { profile: n },
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
});
```

**socket.io 事件清单（只处理流式推送，不负责会话刷新）：**
- message.delta → 流式消息
- reasoning.delta → 推理过程
- tool.started / tool.completed → 工具调用
- run.started / run.completed / run.failed → 运行生命周期
- abort.started / abort.completed → 中止
- usage.updated → 用量

**没有** refresh/reload/session.updated 等重载事件

### 步骤 3：发现 Pinia store

浏览器中可以访问 Vue 3 + Pinia：

Pinia stores: app, chat, profiles, settings, session-browser-prefs, files

**chat store 关键状态：**
```javascript
chat.sessions           // 会话列表（带缓存的 messages）
chat.activeSessionId    // 当前活跃会话 ID
chat.activeSession      // 当前会话对象（含 messages 数组）
chat.sessionsLoaded     // 加载状态
```

**chat store 关键方法（通过 pinia._s.get('chat') 访问）：**
```javascript
chat.refreshActiveSession()   // ✅ 刷新当前会话数据
chat.loadSessions()           // 加载会话列表
chat.switchSession(id)        // 切换会话
chat.sendMessage(content)     // 发消息
```

### 步骤 4：验证 refreshActiveSession 有效

首次调用后 Pinia store 从 71 条变为 74 条（我之前手动写入的测试消息出现）。
DOM 中的元素也从 229 变为 242，最后显示"op：收到，流程验证通过。"

### 步骤 5：发现刷新不从 profile state.db 读

后续用 CLI `hermes chat -q` 发出的天气询问虽然返回了结果，但数据写入 op/state.db 而非 hermes-web-ui.db。
Web UI 的 `GET /api/hermes/sessions/:id` 读取的是 hermes-web-ui.db，不是 profile 的 state.db。
→ 必须双库写入

### 步骤 6：最终解决方案验证

1. 手动写双库（op/state.db + hermes-web-ui.db）
2. CDP 调 refreshActiveSession()
3. 前台 DOM 显示天气问答结果 ✅
4. 无需 F5、无需切会话、无需重启网关 ✅

## 常见坑

### CDP Runtime.evaluate 变量名冲突
每次 `Runtime.evaluate` 调用都在同一页面作用域。如果声明了 `const _x`，下一次再用 `const _x` 会报错。
**解决**：每次用不同变量名，或一条语句完成所有操作。

### Session 在 op/state.db 但 CLI 找不到
gateway 运行时，`hermes sessions export --session-id` 可能报 `Session not found`。数据在数据库里但 CLI 读不到。
**解决**：直接 Python sqlite3 读 WAL 模式，不走 CLI。

### 只写一个库不生效
Web UI 读 hermes-web-ui.db，不读 op/state.db。必须双库都写。
