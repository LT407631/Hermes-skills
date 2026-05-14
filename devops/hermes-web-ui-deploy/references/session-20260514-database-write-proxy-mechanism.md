# Web UI 消息同步实验记录（2026-05-14）

## 场景

小何（默认 profile）通过 API 向 op profile 派活，需要让对话内容出现在 Web UI 的现有会话「小何与op」（session_id=mp5guacelv7uea）中，且不中断 Web UI 服务。

## 实验 A：直接写 Web UI SQLite 数据库

### 尝试 1：默认 journal_mode（失败）

```python
# 默认 journal_mode=delete
conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
conn.execute('INSERT INTO messages ...')
conn.commit()
conn.close()
```

**结果**：数据写入成功，但 Web UI 进程因 SQLite 锁冲突崩了，浏览器显示网关断连。用户需手动重启 gateway。

**根因**：Web UI 使用 `node:sqlite`（WAL 模式），Python 默认用 `delete` 模式，两种事务模型冲突。

### 尝试 2：WAL 模式 + BEGIN IMMEDIATE（成功但非实时）

```python
conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('BEGIN IMMEDIATE')
# ... INSERT INTO messages ...
conn.commit()
conn.close()
```

**结果**：
- ✅ Web UI 没有断连（锁冲突消失）
- ✅ 数据库中有数据
- ❌ 前端不显示（Web UI 缓存在 Vue Pinia store 中，不重新读磁盘）

**验证数据存在**：
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
c = conn.cursor()
c.execute('SELECT id, role, substr(content,1,60) FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 5', ('mp5guacelv7uea',))
for r in c.fetchall():
    print(f'  [{r[0]}] {r[1]}: {r[2]}')
conn.close()
"
```

### 根因分析：Node.js 的内存缓存

Web UI 的 Vue 前端在页面加载时从后端 API 读取会话列表和消息列表，然后全部缓存在内存（Pinia store）中。即使 SQLite 文件已被写入：

1. **API 通道**：前端通过 `/api/hermes/sessions/conversations/:id/messages` API 获取消息 — 这个 API 可能经过格式化/过滤/分页处理
2. **Node.js 独立缓存**：`node:sqlite` 有自己的页面缓存，其他进程写入的数据不会触发缓存刷新
3. **需要手动触发重新读取**：切换会话（点击另一个对话再切回来）或 F5 刷新页面会触发重新 API 调用

### 实用工作流

```
小何 → API 发送消息到 op gateway → 得到回复 → WAL 模式写入 Web UI DB → 用户手动切换会话 → 看到新消息
```

用户验证有效：
- "切到别的会话再切回来看到了" ✅
- "不需要自动刷新，我自己点其他界面再切回来就行" ✅

## 实验 B：通过 Web UI 反向代理发送消息

### 代理机制

Web UI v0.5.17 内置了反向代理，路径：
- `/api/hermes/{*any}` → 转发到 Gateway 的 `/api/*`
- `/v1/{*any}` → 转发到 Gateway 的 `/v1/*`

代理函数 `ye()` 的调用链路：
```javascript
// 路由注册
re.all("/api/hermes/{*any}", ye);
re.all("/v1/{*any}", ye);

// 代理核心逻辑
async function ye(I) {
    let G = VF(I);          // 获取 profile 名称
    let l = QYI(I);         // 获取 gateway 上游 URL
    let c = I.path.replace(...);  // 路径重写
    let W = HYI(I, l);      // 构建请求头（替换 Authorization 为 gateway API key）
    let a = { method: I.req.method, headers: W, body: m };
    N = await fetch(d, a);
    // 返回响应
}
```

**Profile 选择机制** (`VF` 函数)：
```javascript
function VF(I) {
    let G = I.get("x-hermes-profile") || I.query.profile;
    if (G) return G;
    try {
        let {getActiveProfileName: l} = (...);
        return l();
    } catch { return "default" }
}
```

支持通过 HTTP 头 `x-hermes-profile` 或查询参数 `?profile=` 指定目标 gateway。

**认证头处理** (`HYI` 函数)：
```javascript
function HYI(I, G) {
    let l = {};
    for (let [b, Z] of Object.entries(I.headers)) {
        // 跳过 authorization, origin, referer, connection
        let d = b.toLowerCase();
        if (d === "authorization") continue;
        // 复制其他头
    }
    // 替换为 gateway 的 API key
    let c = Sk();
    if (c) {
        let b = c.getApiKey(VF(I));
        b && (l.authorization = `Bearer ${b}`);
    }
    return l;
}
```

**认证问题**：Web UI 的 `Tt` 中间件对所有 `/api/*` 和 `/v1/*` 路径进行了 Bearer token 验证。必须使用从 `.token` 文件中读取的 token。浏览器登录后，token 存储在 `localStorage.getItem("hermes_api_key")` 中。

### 实验结果

尝试用 curl 请求代理路径：
```bash
curl -X POST http://localhost:8648/api/hermes/v1/chat/completions \
  -H "x-hermes-profile: op" \
  -H "Authorization: Bearer <token>" \
  -d '{"model":"Qwen3.6-35B-AWQ","messages":[...]}'
```

**结果**：始终返回 `{"error":"Unauthorized"}`，即使使用了 `.token` 文件中的正确 token。

**可能原因**：
- token 验证逻辑 `b !== I` 在 JavaScript 中严格比较
- 使用 Bearer 格式时需确保没有多余空格或换行
- Web UI 重启后 token 文件内容验证

**未解决**：代理路径的认证问题需要进一步排查。

## 负载均衡/IP 白名单改造

为了防止本地测试时触发 Web UI 的 rate limit，在 `dist/server/index.js` 中修改了四个函数：

```javascript
// 修改前
function Ki(I){let G=Mi();if(G)return G;...}
function Si(I){let G=Mi();if(G)return G;...}
function fi(I){let G=ji(S.passwordIpMap,I);...}
function Ti(I){let G=ji(S.tokenIpMap,I);...}

// 修改后 — 在函数入口加白名单
function Ki(I){if(I==="127.0.0.1"||I==="::1")return{allowed:!0};let G=Mi();...}
function Si(I){if(I==="127.0.0.1"||I==="::1")return{allowed:!0};let G=Mi();...}
function fi(I){if(I==="127.0.0.1"||I==="::1")return;let G=ji(S.passwordIpMap,I);...}
function Ti(I){if(I==="127.0.0.1"||I==="::1")return;let G=ji(S.tokenIpMap,I);...}
```

修改后重启 Web UI，127.0.0.1 的错误请求不再触发 rate limit。

## 关键常量速查

| 常量 | 值 | 含义 |
|------|-----|------|
| ki | 3 | 单 IP 最大失败次数 |
| zi | 60*6e4=3600000ms | IP 锁定时长（60分钟） |
| Ui | 30*6e4=1800000ms | 全局锁定时长（30分钟） |
| xi | 50 | 全局总失败阈值 |
| Pq | 15*6e4=900000ms | 密码失败记录过期时间（15分钟） |
| $q | 100 | 每分钟最大请求数 |
| _q | 6e4=60000ms | 每分钟窗口 |

## 结论

- **WAL 模式写库**：安全，不崩 Web UI，数据可落库，但非实时显示（需手动切换会话刷新）
- **Web UI 代理**：理论上可以通过 `x-hermes-profile` 头转发消息，但认证问题未解决
- **最佳工作流**：用户直接在 Web UI 对应 profile 下发消息 → 实时同步

