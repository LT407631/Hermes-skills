# API 派活会话在 Web UI 不可见（2026-05-14 实战）

## 问题

通过 `v1/chat/completions` API 给 op/dev/me 派活后，会话文件和数据库都有记录，但 Web UI 选对应 profile 时看不到。

## 详细分析

### 三层存储

| 存储层 | 文件位置 | API 是否写入 | Web UI 是否读取 |
|--------|---------|:------------:|:--------------:|
| sessions.json 索引 | `profiles/<name>/sessions/sessions.json` | ❌ | ✅ |
| state.db (SQLite) | `profiles/<name>/state.db` → sessions 表 | ✅ | ❌ |
| 会话文件 | `profiles/<name>/sessions/session_api-*.json` | ✅ | ❌ |

### 数据库验证

经查，op 的 state.db 中 sessions 表包含 API 创建的会话：

```python
# 验证 API 会话在 state.db 中
import sqlite3
conn = sqlite3.connect('~/.hermes/profiles/op/state.db')
cursor = conn.execute('SELECT id, source, user_id, started_at FROM sessions ORDER BY started_at')
for r in cursor.fetchall():
    print(f'{r[0][:40]:40s} | source={r[1]:15s} | {r[3]}')
```

输出显示 `api-xxxxx` 会话存在，但有 `user=None`，且 source 为 `api_server`。

### sessions.json 内容

仅包含一个 DingTalk 群聊会话：
```json
{
  "agent:main:dingtalk:group:xxx:xxx": {
    "session_id": "20260514_184305...",
    "platform": "dingtalk",
    "origin": { ... }
  }
}
```

### 根因

Web UI 读取 sessions.json 作为会话列表索引。API 派活 (`v1/chat/completions`) 通过 OpenAI 兼容接口处理，该接口是**无状态 completion**，不注册到 sessions.json 索引。

## 解决方案

### 方案A（推荐）：通过小何汇报

总监在 API 派活后，把结果通过微信回复给腾哥。微信对话自然记录在 default profile 的会话中，Web UI 选「小何」即可看到。

### 方案D（腾哥的 idea，待验证）：数据库直接注入

核心思路：用户在 Web UI 中手动创建一条会话 → 把会话 ID 给总监 → 总监直接向 state.db 的 messages 表写入派活记录和 op 的回复 → 刷新 Web UI 即可看到。

详见 `references/db-session-injection-20260514.md`。

⚠️ 尚未实战验证，理论可行但需测试：Web UI 能否实时刷新显示新插入的消息。

### 方案B：直接读 session 文件

小何通过 `read_file` 读取目标 profile 的 session 文件。

### 方案C：数据库直接修改 user_id（已验证不可行）

尝试：在 state.db 中直接 `UPDATE sessions SET user_id='xxx' WHERE id='api-xxx'`，将 API 会话的 user_id 设置为与 DingTalk 会话相同的值。

**结果**：user_id 更新成功，但 Web UI 仍不显示该会话。

**根因**：Web UI 读取 **sessions.json 索引文件**来列举会话，而不是直接从 state.db 读取。API 创建的会话未注册到 sessions.json 中，仅修改数据库中的 user_id 不足以让其出现在 Web UI 列表。

⚠️ 三个独立的「可见性」等级：
- state.db 中有记录 → 文件系统级可见
- sessions.json 中有索引 → Web UI 列表可见
- 消息内容完整 → 点开会话后可读

API 派活只达到第 1 层，缺第 2、3 层。

## 端口信息

各 profile 的 API 服务器端口（重启后可能变化，以 gateway.log 中 `listening on` 为准）：

| Profile | 配置端口 | 实际日志端口 |
|---------|---------|-------------|
| default | 8642 | 8642 |
| dev | 8651 | 8651 |
| me | 8643 → 8644 | 8644 |
| op | 8646 → 8645 | 8645 |

API Key：dev 和 op 使用相同 key（`lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE`），me 无需 key。
