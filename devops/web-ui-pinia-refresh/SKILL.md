---
name: web-ui-pinia-refresh
description: Web UI 前台强制刷新 + 双库写入完整方案。无需 F5、无需重启网关
category: devops
version: 3.0.0
author: 小何
---

# Web UI Pinia Store 刷新方案

通过 CDP 直接调用 Pinia chat store 的 `refreshActiveSession()` 方法，强制 Web UI 前端从 REST API 重新加载当前会话数据，触发 Vue DOM 自动更新。

---

## 完整 SOP

### 部署前置条件

在新 PC 上部署此方案前，需要以下环境就绪：

| # | 条件 | 操作 |
|---|------|------|
| 1 | Chrome 远程调试端口 | Windows 启动 Chrome：`chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-debug` |
| 2 | Windows 防火墙 | `netsh advfirewall firewall add rule name='CDP9223' dir=in protocol=tcp localport=9223 action=allow` |
| 3 | Portproxy（WSL ↹ Windows） | `netsh interface portproxy add v4tov4 listenport=9223 listenaddress=0.0.0.0 connectport=9222 connectaddress=127.0.0.1` |
| 4 | CDP 连通验证 | WSL 执行 `curl http://<WINDOWS_IP>:9223/json/version`，拿到 webSocketDebuggerUrl |
| 5 | config.yaml 更新 | `browser.cdp_url = ws://<WINDOWS_IP>:9223/devtools/browser/<BROWSER_ID>` |
| 6 | Web UI 已登录 | 浏览器打开 localhost:8648 并登录 |
| 7 | Hermes gateway 运行 | default + op/dev/me gateway 健康 |
| 8 | 会话已存在 | `mp5guacelv7uea`（小何与op）已在 hermes-web-ui.db 中 |

### 工作流选择

```
                      ┌─────────────┐
                      │ 收到任务指令 │
                      └──────┬──────┘
                             ▼
                ┌────────────────────────┐
                │ 需要 LLM 参与？         │
                │ (写文案/分析/查资料等)    │
                └──────┬────────┬────────┘
                       YES       NO
                        │         │
                        ▼         ▼
           ┌──────────────────┐  ┌───────────────────────┐
           │ CLI 调 op/dev    │  │ 直接编好 Q&A 内容      │
           │ HERMES_HOME=xx   │  │ 零 API 费用            │
           │ hermes chat -q   │  └───────────┬───────────┘
           └───────┬──────────┘              │
                   │                         │
                   ▼                         ▼
           ┌───────────────────────────────────────┐
           │ 写 hermes-web-ui.db                    │
           │ (PRAGMA WAL + BEGIN IMMEDIATE)        │
           └──────────────────┬────────────────────┘
                              ▼
           ┌───────────────────────────────────────┐
           │ CDP 调 refreshActiveSession()         │
           │ → Vue store 更新 → DOM 自动刷新       │
           └──────────────────┬────────────────────┘
                              ▼
           ┌───────────────────────────────────────┐
           │ 通知腾哥查看                            │
           └───────────────────────────────────────┘
```

### 快速版（推荐，2秒，零API费）

不调 LLM，直接编好问答内容写入数据库再刷新前台。

**步骤 1：写入 hermes-web-ui.db**

```python
import sqlite3, time

now = time.time()
sid = "mp5guacelv7uea"
qa = [("user", "你的问题"), ("assistant", "你的回答")]

db = "/home/lt-pc/.hermes-web-ui/hermes-web-ui.db"
conn = sqlite3.connect(db)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("BEGIN IMMEDIATE")
c = conn.cursor()

c.execute("SELECT COALESCE(MAX(id), 0) FROM messages")
mid = c.fetchone()[0]

for role, content in qa:
    mid += 1
    c.execute("INSERT INTO messages (id, session_id, role, content, timestamp) VALUES (?,?,?,?,?)",
              (mid, sid, role, content, int(now)))

c.execute("UPDATE sessions SET message_count=message_count+?, last_active=? WHERE id=?", (len(qa), int(now+1), sid))
c.execute("UPDATE sessions SET preview=? WHERE id=?", (qa[0][1][:60], sid))
conn.commit()
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.close()
```

**步骤 2：CDP 刷新前台**

```javascript
const p = document.querySelector('#app').__vue_app__;
const pinia = p.config.globalProperties.$pinia;
const chat = pinia._s.get('chat');
await chat.refreshActiveSession();
```

### 双库版（op/state.db + hermes-web-ui.db）

op profile 也需要看到数据时，额外写入 op/state.db（注意 timestamp 用浮点数）：

```python
op_db = "/home/lt-pc/.hermes/profiles/op/state.db"
conn = sqlite3.connect(op_db)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("BEGIN IMMEDIATE")
c = conn.cursor()

c.execute("SELECT COALESCE(MAX(id), 0) FROM messages")
gmax = c.fetchone()[0]

c.execute("INSERT INTO messages (id, session_id, role, content, timestamp) VALUES (?,?,?,?,?)",
          (gmax+1, sid, "user", qa[0][1], now))  # REAL，不用 int()

c.execute("UPDATE sessions SET message_count=message_count+1, ended_at=? WHERE id=?", (int(now+1), sid))
conn.commit()
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.close()
```

---

## 数据库结构

### messages 表差异

| 列 | op/state.db | hermes-web-ui.db |
|----|-------------|-----------------|
| id | INTEGER PK | INTEGER PK |
| session_id | TEXT | TEXT |
| role | TEXT | TEXT |
| content | TEXT | TEXT |
| tool_call_id | TEXT | TEXT |
| tool_calls | TEXT | TEXT |
| tool_name | TEXT | TEXT |
| timestamp | **REAL**（浮点秒） | **INTEGER**（整型秒） |
| token_count | INTEGER | INTEGER |
| finish_reason | TEXT | TEXT |
| reasoning | TEXT | TEXT |
| reasoning_content | TEXT | TEXT |
| reasoning_details | TEXT | TEXT |
| codex_reasoning_items | TEXT | ❌ |
| codex_message_items | TEXT | ❌ |

### sessions 表差异

| 列 | op/state.db | hermes-web-ui.db |
|----|-------------|-----------------|
| id | TEXT PK | TEXT PK |
| profile | ❌ | TEXT |
| source | TEXT | TEXT |
| user_id | TEXT | TEXT |
| model | TEXT | TEXT |
| title | TEXT | TEXT |
| started_at | REAL | INTEGER |
| ended_at | REAL | INTEGER |
| message_count | INTEGER | INTEGER |
| preview | ❌ | TEXT |
| last_active | ❌ | INTEGER |
| workspace | ❌ | TEXT |
| 其他扩展列 | model_config, system_prompt, billing_* 等 | ❌ |

### 写入注意事项

1. **hermes-web-ui.db 必须用 WAL 模式 + BEGIN IMMEDIATE**：否则锁冲突会导致 Node.js 进程崩溃
2. **timestamp 格式**：op/state.db 用浮点数 `time.time()`，hermes-web-ui.db 用整型 `int(time.time())`
3. **消息 ID**：用 `SELECT COALESCE(MAX(id), 0) FROM messages`（全局最大 ID，不是会话内最大 ID）避免重复
4. **WAL checkpoint**：写完后执行 `PRAGMA wal_checkpoint(TRUNCATE)`，确保 WAL 合并到主文件

---

## 工作机制

### 数据流

```
[Python脚本] 写入 hermes-web-ui.db
       │
       ▼
CDP → refreshActiveSession() → REST API GET /api/hermes/sessions/:id
       │                          │
       │                          ▼ 从 hermes-web-ui.db 读取
       ▼                          │
Vue Pinia store 更新               ▼ 返回 JSON 数据
       │
       ▼
Vue reactivity → DOM 自动更新（无需 F5）
```

### 关键发现

- `refreshActiveSession()` 从 **hermes-web-ui.db** 读取数据，不是 profile 的 `state.db`
- 前端没有轮询机制，必须通过 CDP 手动触发刷新
- socket.io 只负责流式消息推送，不负责会话列表刷新
- 点击切换会话**不会触发** REST API 重请求——数据从 Pinia store 缓存读取

---

## 已知问题

| 问题 | 原因 | 解决 |
|------|------|------|
| refreshActiveSession() 返回 ok 但数据没变 | API 返回了缓存数据 | 检查 hermes-web-ui.db 是否真的写入新消息 |
| INSERT 报 UNIQUE constraint | 消息 ID 重复 | 用全局 MAX(id)，不是会话内 MAX(id) |
| Web UI 白屏崩溃 | SQLite 锁冲突 | 必须用 WAL + BEGIN IMMEDIATE |
| 限流 429 | API 被频繁调用 | 等待 30 秒或检查 login-lock.json |
| CDP 连接拒绝 | 端口被占或 Chrome 没启动 | 检查 portproxy、杀旧 Chrome、重启 Chrome |
