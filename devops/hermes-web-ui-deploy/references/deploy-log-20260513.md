# Hermes Web UI 部署记录 - 2026-05-13

## 问题记录

### 问题1：「升级后又变回老版本」的根因

**现象**：在 Web UI 内点了升级命令后，重启服务又变回 v0.4.0。

**根因**：
1. 系统存在两个 Node 版本：`/home/lt-pc/.hermes/node/bin/node` (v22.22.2) 和 `/home/lt-pc/.hermes/node-v23/bin/node` (v23.10.0)
2. v0.5.17 声明 `engines: {node: ">=23.0.0"}`，需 Node ≥ 23
3. `hermes-web-ui start` / hermlink 都用系统默认的 v22 Node 启动
4. 手动 `npm install -g hermes-web-ui` 只装到了 v23 的全局路径，系统 v22 路径下的旧 v0.4.0 还留着
5. 重启时系统又用 v22 拉起旧版 v0.4.0

**解决**：见 SKILL.md 中「多 Node 版本共存时升级 v0.5.17 的完整流程」。

### 问题2：`rm -rf` 删除旧 Web UI 目录超时

**现象**：`rm -rf /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui` 超时 10s。

**原因**：node_modules 目录层级深、文件多，rm -rf 在 WSL 上可能较慢，尤其在原目录被进程 mmap 后。

**解决**：先 `kill` 旧进程，再 `rm -rf`，或直接用 WSL 终端执行（非 Hermes terminal 工具）。

### 问题3：`hermes gateway restart` 超时

**现象**：在 Herlink 运行状态下执行 gateway restart，terminal timeout 15s 后 BLOCKED。

**原因**：gateway 重启涉及多个子进程重启 + 健康检查，可能耗时超过终端 timeout。

**解决**：直接在 WSL 终端执行，或设更长 timeout (~60s)。

### 问题4：替换 Node 软链后操作 hermes-web-ui 导致循环软链接自毁

**现象**：`hermes-web-ui start` 报错 `Too many levels of symbolic links`，v0.5.17 源码消失。

**触发步骤**：
```bash
# ① 先把 ~/.hermes/node 软链到 node-v23
cd /home/lt-pc/.hermes
rm -rf node
ln -s node-v23 node

# ② 然后 cd 到 node/lib/node_modules/（实际已进入 node-v23/lib/node_modules/）
cd /home/lt-pc/.hermes/node/lib/node_modules/

# ③ 删除 hermes-web-ui（以为删的是旧版，实际删的是新版源码）
rm -rf hermes-web-ui

# ④ 试图软链新版（实际链接到自己，形成循环）
ln -s /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui hermes-web-ui
```

**根因**：`node` → `node-v23` 软链后，两个路径物理上是同一个位置。操作者认知上有「旧版目录 vs 新版目录」的错觉，实际只有一个副本。

**修复命令**：
```bash
rm -f /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui
npm install -g hermes-web-ui@0.5.17 --registry=https://registry.npmmirror.com
```

### 问题5：新版 Web UI 看不到历史会话

**现象**：v0.5.17 启动后，Web UI 上看不到之前的 51 个历史会话。

**真相**：历史会话一个没丢，存放在 Hermes SQLite 数据库 `~/.hermes/state.db` 中（51 sessions, 3221 messages）。

**验证**：
```bash
hermes sessions stats                    # 总会话数
hermes sessions list --limit 100         # 列出所有会话
```

**解决**：Web UI 通过 Gateway API 同步会话，Gateway 健康后自动展示。无需手动恢复。

### 问题6：登录限流锁（.login-lock.json）

**现象**：在 Web UI 页面输入 Token 或账号密码登录失败多次后，提示「登录失败次数过多，请稍后重试」。即使 `hermes-web-ui restart` 也无法清空。

**原因**：限流记录存储在**磁盘文件** `.login-lock.json` 中，不是内存状态，重启进程不会清空。

**锁文件结构**：
```json
{
  "tokenIpMap": {           // Token 登录失败记录（独立锁）
    "127.0.0.1": {
      "count": 3,
      "firstFailureAt": 1778601829063,  // 时间戳(ms)
      "lockedUntil": 1778605673819
    }
  },
  "passwordIpMap": {},      // 密码登录失败记录（独立锁，空 = 没锁）
  "globalLockedUntil": 1778602073818   // 全局锁
}
```

**关键发现**：Token 登录和密码登录的限流是**独立**的。Token 被锁时密码可能没锁。

**解决（秒解，无需重启）**：
```bash
rm ~/.hermes-web-ui/.login-lock.json
```

**安全问题**：删锁文件不影响账号密码或 Token 凭证。凭证存在 `.credentials` 和 `.token` 文件中。

### 问题7：Web UI 所有 API 返回 429（非登录限流）

**现象**：Web UI 页面打开后所有功能不可用，`curl` 测试 API 全部返回 429。与登录失败限流不同，这是 API 调用频率限制。

**原因**：在 Web UI 前端短时间内快速点击导航/刷新按钮，触发了服务端 API 限流。

**唯一解决**：必须重启 Web UI 进程（限流在内存中）。
```bash
kill $(pgrep -f "hermes-web-ui") 2>/dev/null
hermes-web-ui start
```

**预防**：避免快速连续点击 Web UI 界面按钮。

### 问题8：`sqlite3` CLI 看不到 Web UI 数据库表

**现象**：`sqlite3 ~/.hermes-web-ui/hermes-web-ui.db .tables` 输出为空，但 `node:sqlite` 模块能读取 13 张表含 22 个会话。

**原因**：v0.5.17 使用 WAL（Write-Ahead Logging）模式，系统 `sqlite3` CLI 在未 checkpoint 前看不到 WAL 中的数据。

**正确诊断方法**（必须用 `node:sqlite`）：
```bash
/home/lt-pc/.hermes/node-v23/bin/node -e "
const sqlite = require('node:sqlite');
const db = new sqlite.DatabaseSync(process.env.HOME + '/.hermes-web-ui/hermes-web-ui.db');
console.log('Tables:', JSON.stringify(db.prepare(\"SELECT name FROM sqlite_master WHERE type='table'\").all()));
console.log('Sessions:', JSON.stringify(db.prepare('SELECT COUNT(*) as c FROM sessions').all()));
db.close();
"
```

### 问题9：Web UI 数据库使用 WAL 模式后的 WAL 文件过大

**现象**：`hermes-web-ui.db-wal` 文件大小达到 1.8MB，而主 DB 仅 4KB。

**根因**：`node:sqlite` 在 v0.5.17 中使用 WAL 模式（`PRAGMA journal_mode=WAL`），写入的数据暂存在 WAL 文件中，未及时 checkpoint 到主文件。

**不影响功能**：`node:sqlite` 模块能正常读取 WAL 中的数据。仅当使用系统 `sqlite3` CLI 时才会看不到数据。

### 问题10：两个 Web UI 数据库路径导致数据不同步

**现象**：`~/.hermes-web-ui/hermes-web-ui.db`（4KB）和 `~/packages/server/data/hermes-web-ui.db`（442KB）同时存在，内容相似但启动时只用前者。

**根因**：v0.5.17 根据 `NODE_ENV` 决定数据库路径：
- `NODE_ENV=production` → `~/.hermes-web-ui/hermes-web-ui.db`
- 其他情况 → `<process.cwd()>/packages/server/data/hermes-web-ui.db`

**解决**：确保 `NODE_ENV=production`，并删除开发路径的旧数据库避免混淆。

---

## 会话数据概要

| 项目 | 值 |
|------|-----|
| 总会话数 | 51（Hermes 后端 `hermes sessions stats`）|
| Web UI 同步数 | 22（部分较旧会话未同步）|
| 总消息数 | 3221 |
| Hermes 后端 DB | `~/.hermes/state.db`（36.3 MB）|
| Web UI 数据库 | `~/.hermes-web-ui/hermes-web-ui.db` |
| Gateway 端口 | 8642 |
| Gateway 健康 | `curl http://127.0.0.1:8642/health` → `{"status": "ok"}` |

---

## 会话同步架构

### 数据流

```
Hermes 后端 (state.db, 51 sessions)
    ↕ Gateway API (端口 8642, /api/sessions)
Web UI 启动时 → [session-sync] 从 Gateway 拉取
    ↕ 写入
Web UI 自己的 SQLite 数据库 (~/.hermes-web-ui/hermes-web-ui.db)
    ↕ Web UI API (端口 8648, /api/hermes/sessions)
Web UI 前端 (浏览器)
```

### Web UI 数据库结构（已验证）

共 13 张表：
- `sessions` — 22 行（会话元数据：profile, source, user_id, model, title, started_at, message_count 等）
- `messages` — 76 行（消息内容：session_id, role, content, tool_calls, reasoning 等）
- `session_usage` — 0 行（用量统计）
- `chat_compression_snapshots`, `model_context` — 0 行（压缩与上下文）
- `gc_rooms`, `gc_messages`, `gc_*` — 0 行（群聊功能，未使用）
- `sqlite_sequence` — 1 行（自增 ID 序列）

---

## Web UI 凭据文件清单

| 文件 | 路径 | 大小 | 作用 | 能否安全删除 |
|------|------|------|------|-------------|
| `.login-lock.json` | `~/.hermes-web-ui/.login-lock.json` | ~300B | 登录失败次数和锁定时长 | ✅ 删了等于解限流 |
| `.credentials` | `~/.hermes-web-ui/.credentials` | ~250B | 用户名和密码凭证 | ❌ 删了账号密码重置 |
| `.token` | `~/.hermes-web-ui/.token` | ~65B | 登录 Token | ❌ 删了 Token 失效 |
| `server.pid` | `~/.hermes-web-ui/server.pid` | ~4B | Web UI 进程 PID | ✅ 自动重建 |
| `hermes-web-ui.db` | `~/.hermes-web-ui/hermes-web-ui.db` | 4KB~442KB | 会话数据（SQLite，含 WAL） | ✅ 删了下次启动自动重同步 |

---

## API 端点映射

Web UI v0.5.17 的 API 路由路径为 `/api/hermes/...`（不是 `/api/...`）：

| 用途 | 路径 |
|------|------|
| 认证状态 | `/api/auth/status` |
| 登录 | `/api/auth/login` |
| 会话列表 | `/api/hermes/sessions` |
| 会话详情 | `/api/hermes/sessions/<id>` |
| 模型列表 | `/api/hermes/available-models` |
| 配置信息 | `/api/hermes/config` |
| 网关列表 | `/api/hermes/gateways` |
| 配置文件 | `/api/hermes/config/providers` |

---

## 操作偏好记录

- 用户要求：给终端命令让用户自己复制执行，不要直接操作文件系统
- 用户偏好：先给完整的命令序列，标明步骤序号，用户按顺序执行
- 用户偏好：解释清楚「为什么」比直接给答案更重要（如 429 的含义、锁文件结构）
- 命令间距：用户会确认操作顺序（如「需要先停服务再删吗？」），给予明确的前后置条件

---

## 日志时间线参考

| 时间 (CST) | 事件 |
|-----------|------|
| 00:03:49 | 首次 Token 登录失败 |
| 00:07:53 | 全局锁窗口结束 |
| 01:03:19 | 诊断当前状态 |
| 01:07:53 | Token 登录锁自动解开 |

所有时间戳为 2026-05-13。
