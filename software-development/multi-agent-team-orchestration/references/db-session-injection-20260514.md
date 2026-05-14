# 数据库级会话注入（2026-05-14 实战思路）

> 腾哥提出的方案：在 op 的 Web UI 中新开一条会话 → 把会话 ID 给总监 → 总监直接向该会话的 state.db 中写入消息 → 刷新 Web UI 即可看到。

## 原理

每个 profile 的会话存储在 `state.db`（SQLite）中，包含两张核心表：

### sessions 表

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT,        -- 'dingtalk', 'api_server', 'web_ui' 等
    user_id TEXT,       -- 用户标识
    model TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    pricing_version TEXT,
    title TEXT,
    api_call_count INTEGER DEFAULT 0
);
```

### messages 表

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,          -- 'user', 'assistant', 'tool'
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL,
    token_count INTEGER DEFAULT 0,
    finish_reason TEXT
);
```

## 操作流程

### 1. 用户先在 Web UI 中创建会话

在 Web UI 选对应 profile → 新建会话 → 发送一条消息 → 拿到会话 ID

### 2. 总监从 state.db 读取会话信息

```python
import sqlite3, time

conn = sqlite3.connect('~/.hermes/profiles/op/state.db')

# 查会话详情
cursor = conn.execute('SELECT * FROM sessions WHERE id=?', ('session_id_from_user',))
cols = [d[0] for d in cursor.description]
row = cursor.fetchone()
# 拿到 user_id、source、model 等信息
```

### 3. 总监向 messages 表插入数据

```python
now = time.time()
session_id = '用户提供的ID'

# 插入用户消息（派活指令）
conn.execute('''
    INSERT INTO messages (session_id, role, content, timestamp)
    VALUES (?, 'user', ?, ?)
''', (session_id, '腾哥让你写条文案...', now))

# 插入助理回复（op 的产出）
conn.execute('''
    INSERT INTO messages (session_id, role, content, timestamp)
    VALUES (?, 'assistant', ?, ?)
''', (session_id, '收到，文案如下：...', now + 0.1))

# 更新会话消息计数
conn.execute('UPDATE sessions SET message_count = message_count + 2 WHERE id = ?', (session_id,))

conn.commit()
```

### 4. 用户刷新 Web UI 即可看到

## ⚠️ 注意事项

1. **sessions.json 索引**：Web UI 读取 sessions.json 作为会话列表索引。如果会话是通过 API 创建的（非用户手动创建），需要也在 sessions.json 中注册才能出现在会话列表中。
2. **时间戳递增**：消息的 timestamp 必须递增，否则 Web UI 排序会乱。
3. **role 交替**：确保 `user` 和 `assistant` 角色交替出现，不能两个 `user` 连续。
4. **已存在的会话**：如果会话已存在于 Web UI 列表中（用户手动创建的），直接写入 messages 表即可，无需修改 sessions.json。这是最可靠的使用场景——在用户已在 Web UI 打开的会话中追加消息。
5. **重启风险**：gateway 重启时可能重建或者清理数据库记录，直接写数据库属于非官方操作，可能被覆盖。

## 🟢 实战验证（2026-05-14 已验证通过）

### 验证结果：✅ 可行

**测试过程：**
1. 用户在 Web UI 的 op profile 下已有一个会话「小何与op」（session_id = `mp5guacelv7uea`，存储在 `~/.hermes-web-ui/hermes-web-ui.db` 的 sessions 表中）
2. 总监通过 Python sqlite3 直接向该会话追加了 user 消息和 assistant 消息（role 分别为 'user' 和 'assistant'，timestamp 递增）
3. 用户刷新 Web UI 后，成功看到追加的消息内容

### 关键发现：不是写 profile 的 state.db，而是写 Web UI 的 hermes-web-ui.db

**正确的注入目标：** 不是写 `~/.hermes/profiles/op/state.db` 的 messages 表，而是写 **`~/.hermes-web-ui/hermes-web-ui.db`** 的 messages 表。

Web UI 有自己的独立数据库，其 sessions 表结构不同（含 `profile` 字段），messages 表也有 Web UI 专用的字段。

**注入 SQL（已验证）：**

```python
import sqlite3, time

web_ui_db = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
w = web_ui_db.cursor()

# 获取 Web UI 本次会话的 session_id（通过查询 sessions 表获得）
w.execute('SELECT id FROM sessions WHERE profile="op" ORDER BY started_at DESC LIMIT 1')
session_id = w.fetchone()[0]

now = time.time()

# 插入 user 消息（总监的派活）
w.execute(
    'INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
    (session_id, 'user', '派活内容...', now)
)

# 插入 assistant 消息（op 的回复）
w.execute(
    'INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
    (session_id, 'assistant', '收到，产出内容...', now + 0.001)
)

web_ui_db.commit()
web_ui_db.close()
```

### 🔴 验证时间戳样式会掉，请注意使用规范格式

### ⚠️ 陷阱：直接写 hermes-web-ui.db 会导致 Web UI 断连

**严重性：高** — 每次直接写数据库都会导致 Web UI 显示「gateway 已断开」。

**根因：** Web UI 使用 Node.js 的 `node:sqlite`（WAL 模式），而 Python 的 `sqlite3` 默认使用 journal 模式。两个不同进程同时操作同一个 SQLite 数据库文件（且一个用 WAL 一个用 journal），会产生锁冲突。Web UI 的 Node 进程会因此崩溃连接，在浏览器端表现为「gateway 已断开」。

**表现：**
1. 数据写入成功（刷新后内容可见）
2. 但 Web UI 页面显示网关断连
3. 用户需要手动重启网关才能恢复
4. 重启后之前写入的数据仍然存在

### 🟢 2026-05-14 晚：双库写入 + 告知用户刷新 是当前唯一可靠路径

#### 什么试了不行

| 尝试 | 结果 | 原因 |
|------|------|------|
| `send_message` 工具 | ❌ 创建新 api-* 会话 | 工具本身设计如此，无法指定已有 session_id |
| `hermes chat --resume <session_id>` | ❌ 进程挂死 | CLI chat 在有 gateway 运行的 profile 下会卡住，无法正常响应 |
| 重启 op gateway | ❌ 用户说「不行啊」 | Web UI 重连后前端的消息列表缓存未刷新 |
| 只写 profile 的 state.db | ❌ 用户看不到 | Web UI 有自己的缓存数据库 |
| 直接写 Web UI 的 hermes-web-ui.db (WAL模式) | ⚠️ 数据入库但不显示 | 前端 Vue Pinia store 内存缓存不重读 |
| 写库 + F5 刷新页面 | ⚠️ 时灵时不灵 | 前端有 15 秒轮询间隔，刷新时机不确定 |

#### ✅ 当前最可靠的折中方案

**流程：**
1. 用 WAL+`BEGIN IMMEDIATE` 写两个库（目标 profile 的 state.db + Web UI 的 hermes-web-ui.db）
2. 告诉用户 F5 刷新页面或切换会话再切回
3. 必须写 user + assistant 成对消息（op 不会自动从写库中生成响应）

**示例代码（2026-05-14 验证）：**
```python
import sqlite3, time

session_id = "mp5guacelv7uea"  # 固定的"小何与op"会话ID
now_ts = int(time.time())

# 写 op/state.db
op = sqlite3.connect("~/.hermes/profiles/op/state.db")
op.execute("PRAGMA journal_mode=WAL")
op.execute("BEGIN IMMEDIATE")
op.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)", 
           (session_id, "user", "问题", now_ts))
op.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)", 
           (session_id, "assistant", "回答", now_ts+1))
op.execute("UPDATE sessions SET message_count = message_count + 2 WHERE id = ?", (session_id,))
op.commit(); op.close()

# 写 Web UI DB
wu = sqlite3.connect("~/.hermes-web-ui/hermes-web-ui.db")
wu.execute("PRAGMA journal_mode=WAL")
wu.execute("BEGIN IMMEDIATE")
wu.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)", 
           (session_id, "user", "问题", now_ts))
wu.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)", 
           (session_id, "assistant", "回答", now_ts+1))
wu.execute("UPDATE sessions SET message_count = message_count + 2, last_active = ? WHERE id = ?", 
           (now_ts+1, session_id))
wu.commit(); wu.close()
```

**验证结果：**
- ✅ hermes-web-ui.db 写入成功（无锁冲突，Web UI 不断连）
- ✅ op/state.db 写入成功
- ⚠️ 用户需手动 F5 或切换会话才能看到（数据在库，前端不自动刷新）
- ❌ 用户不手动操作则一直不可见

#### 尚未解决的问题：前端自动刷新

Web UI 前端有 15 秒的轮询间隔（`setInterval(..., 15000)`），理论上会调用 API 重新拉取消息。但实际测试中即使等待超过 15 秒，新消息仍未自动出现。推测前端轮询仅在「会话列表页」有效，不在「会话详情页」自动拉取消息。

#### 尝试 WAL 模式的安全写入

```python
import sqlite3, time
conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
conn.execute('PRAGMA journal_mode=WAL')   # 匹配 Web UI 的 WAL 模式
conn.execute('BEGIN IMMEDIATE')            # 立即锁，减少竞争窗口
# ... 写入操作 ...
conn.commit()
conn.close()
```

**结果：** ✅ Web UI 没有断连，页面正常运行。❌ 但写入的消息在前端不显示。

#### 根因：Web UI 前端不重读数据库

Web UI 的 Vue 前端（Pinia store）在页面加载时从后端 API 读取会话消息列表，然后全部缓存在内存中。后续页面交互不会重新查询数据库。**即使你成功写入了 hermes-web-ui.db 的 messages 表，前端不会因此刷新消息列表。**

💡 **刷新浏览器（F5）后仍可能看不到**，因为：
1. Web UI 的消息列表是通过 `/api/sessions/<id>/messages` API 获取的，不是直接读 SQLite
2. 该 API 端点在 Web UI 内部可能有缓存层
3. 直接写库绕过了 Web UI 的同步/通知机制

#### 让写入内容可见的条件

需要同时满足两个条件：
1. **数据写入 Web UI 的 hermes-web-ui.db**（✅ 通过 WAL 模式可安全完成）
2. **Web UI 重新加载消息列表**（❌ 写库本身不触发刷新）

**让 Web UI 刷新消息列表的方法：**
- **方案一：用户手动刷新浏览器页面（F5）** → 页面重新加载 → API 重新请求 → 可能看到
- **方案二：先写库，再通过 Web UI 后端 API 触发一次同步/刷新** → 需研究 Web UI 是否有这样的端点
- **方案三：在 Web UI 的当前会话中模拟一次消息发送** → 触发 Pinia store 重新读取消息列表
- **方案四：先停 Web UI，写库，重启 Web UI** → 启动时重新从 gateway 同步 → 能看见

**更新结论（2026-05-14 晚）：** 直接写 hermes-web-ui.db 用 WAL + BEGIN IMMEDIATE 模式是**可行的折中方案**：数据安全写入，Web UI 不断连，用户 F5 或切会话后可见。但这仍不是实时方案——前端不会自动刷新消息列表。在 Web UI 提供 REST API 写消息端点之前，这是唯一可行的路径。
