---
name: hermes-web-ui-deploy
description: "Hermes Agent Web UI 部署、配置、故障排查 — 含 WSL 环境、多 Node 版本共存、npm 镜像源"
version: 2.4.0
author: 小何 + 腾哥
metadata:
  domain: devops
  tags: [Hermes, Web UI, 部署, WSL, Node.js, npm, GatewayManager, Profile]
---

# Hermes Agent Web UI 部署指南

> ⚠️ **腾哥的操作偏好（已演变）**：
> 1. **优先自己执行非 sudo 终端命令** — 用 terminal 工具直接跑。用户说「你自己跑」时不要只给命令让他复制。
> 2. **sudo 操作必须先问** — 格式：「腾哥，需要 sudo 权限，批准吗？」批准后再执行。
> 3. **自保原则**：不要执行会杀掉自己进程的命令（`kill -9 $(pidof python)` 会干掉 Hermes 自身）。如果要杀 Hermes 相关进程，确认目标 PID 不是自己的进程树，或者用 socat 等不杀进程的替代方案。
> 4. 不要连续发多条命令让用户一次性跑完。每次只给下一步，用户确认后继续。
> 5. **严禁推荐或使用 `0.0.0.0` 地址** — 腾哥明确排斥，任何场景都不要提。统一用 `127.0.0.1` + Windows portproxy 通路。

## 概述

Hermes Web UI（`hermes-web-ui`）是 Hermes Agent 的 Web 管理控制台，提供：
- 实时对话管理（SSE 流式、多会话、搜索 Ctrl+K）
- 8 个平台通道配置（含微信、Telegram、Discord 等）
- Token/成本用量分析
- 定时任务管理
- Profile 切换
- Web 终端
- 技能/记忆浏览

**安装方式：** `npm install -g hermes-web-ui`，默认端口 8648

---

## 前置条件

| 要求 | 标准 |
|------|------|
| Node.js | **v23+**（v22 可用但 npm install 极慢，不推荐） |
| npm | >= 10 |
| WSL | Ubuntu 24.04 |
| 网络 | 需能访问 npm registry |

---

## 标准安装流程

### 步骤 1：清理旧版本

```bash
# 先停旧服务
hermes-web-ui stop 2>/dev/null || true

# 卸载旧全局包
npm uninstall -g hermes-web-ui 2>/dev/null || true

# 清理残留目录（如 npm uninstall 不干净）
rm -rf <npm-global-path>/node_modules/hermes-web-ui 2>/dev/null || true
```

> ⚠️ **多 Node 版本共存时**，`npm uninstall -g` 只卸载当前 npm 指向的那个全局路径下的包，其他 Node 版本下的需要分别卸载。

### 步骤 2：设置国内镜像源（必须）

```bash
npm config set registry https://registry.npmmirror.com
```

### 步骤 3：安装

```bash
npm install -g hermes-web-ui
```

> ⚠️ `npm install` 编译 `node-pty`（原生 C 代码）可能耗时 30-60 秒，确保终端 timeout 设够，或确保有 `build-essential`。

### 步骤 4：启动

```bash
hermes-web-ui start
```

### 步骤 5：浏览器访问

```
http://localhost:8648
```

---

## 首次登录

启动后日志会输出 Token：
```
cat ~/.hermes-web-ui/server.log | grep "token"
```

浏览器打开后输入 Token 进入。

**强烈建议**：进入后 **Settings → Authentication → 设置用户名 + 密码**，设完后下次直接用账号密码，无需依赖 Token。

---

## 多 Node 版本共存方案

### 场景

WSL 同时有多个 Node 版本（如 v22 和 v23），每个有自己的全局 npm 路径。

### 判断命令

```bash
# 看 Web UI 二进制使用哪个 Node
head -1 /home/lt-pc/.hermes/node/bin/hermes-web-ui
# 输出 "#!/usr/bin/env node" → 使用 PATH 中第一个 node

# 看运行中进程的 Node 版本
ps aux | grep hermes-web | grep -v grep

# 当前 npm 的全局包安装路径
npm root -g
```

### 切换命令

```bash
# 方式1：直接用全路径
/home/lt-pc/.hermes/node-v23/bin/hermes-web-ui start

# 方式2：永久改 PATH
echo 'export PATH="$HOME/.hermes/node-v23/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 方式3：npm install 时指定 prefix
npm install -g hermes-web-ui --prefix /home/lt-pc/.hermes/node-v23
```

### ⚠️ 关键坑

Web UI 启动脚本 `bin/hermes-web-ui` 内使用 `process.execPath` 启动子进程：
```javascript
const child = spawn(process.execPath, [serverEntry], ...)
```
这意味着 **即使你用 v23 路径手动启动 CLI，子进程仍用 CLI 自己的 process.execPath**。如果 CLI 是从旧 v22 的 npm 路径来的，子进程也是 v22。

**解决**：在目标 Node 版本的全局路径下全新 `npm install -g hermes-web-ui`，不要用旧版本残留。

---

## 服务管理

```bash
hermes-web-ui start
hermes-web-ui stop
hermes-web-ui restart
hermes-web-ui status
hermes-web-ui update
```

---

### ⚠️ 手动升级后必须卸载旧版（高频坑）

手动在不同 Node 版本下安装 Web UI 后，**务必卸载旧路径下的版本**。否则 hermlink 下次重启会再次拉起旧版，你以为升了新但实际上跑的还是老的。

**检查命令：**
```bash
# 看当前 Web UI 用哪个 Node 路径
ps aux | grep hermes-web-ui | grep -v grep
```

**正确升级流程：**
1. `kill -9 <旧Web UI PID>`（确认杀干净）
2. `npm uninstall -g hermes-web-ui`（卸载旧版路径）
3. 切到目标 Node 版本
4. `npm install -g hermes-web-ui`（在新路径安装）
5. 手动用新路径启动：`<新路径>/bin/node <新路径>/lib/node_modules/hermes-web-ui/dist/server/index.js`

> ⚠️ 如果不用 hermlink 管理，必须手动用目标 Node 路径启动，`hermes-web-ui start` 仍会用系统默认路径。

---

## 多 Node 版本共存时升级 v0.5.17 的完整流程

### 场景

Hermes 自带 Node（`/home/lt-pc/.hermes/node/bin/node` 通常是 v22），而你手动安装了 v23 Node 到另一个路径（如 `/home/lt-pc/.hermes/node-v23/`）。新版 Web UI（v0.5.17）要求 **Node >= 23.0.0**，但 `hermes-web-ui start` 始终用系统 Node 旧版启动，导致「升级后又变回老版本」。

### 根因

- v0.5.17 的 `package.json` 声明 `"engines": {\"node\": \">=23.0.0\"}`
- 系统默认 Node 是 v22（`/home/lt-pc/.hermes/node/bin/node`）
- `hermes-web-ui start` / hermlink 都用系统 Node，不会自动用 v23

### 修复方法（选其一）

**方案 A：替换系统 Node 二进制（推荐）**
```bash
# 备份旧 node
mv /home/lt-pc/.hermes/node/bin/node /home/lt-pc/.hermes/node/bin/node.bak
# 软链到新版
ln -s /home/lt-pc/.hermes/node-v23/bin/node /home/lt-pc/.hermes/node/bin/node
# 验证
/home/lt-pc/.hermes/node/bin/node --version   # 应显示 v23.x
```

**方案 B：删除旧版 + 软链新版（配合方案A使用）**
```bash
# 1. 杀掉旧进程
kill $(ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}')
# 2. 删除旧版目录
rm -rf /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui
# 3. 软链新版到旧路径
ln -s /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui
# 4. 验证
grep version /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui/package.json
# 应显示 "version": "0.5.17"
# 5. 启动
nohup /home/lt-pc/.hermes/node/bin/node /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui/dist/server/index.js > ~/.hermes-web-ui/server.log 2>&1 &
```

> ⚠️ 方案 B 单独用不行 — 如果 Node 版本还是 v22，Web UI 启动时会报错。必须先换 Node 二进制（方案 A）或直接全路径指定 v23 的 Node。

**方案 C：直接全路径启动（最安全，不破坏系统）**
```bash
nohup /home/lt-pc/.hermes/node-v23/bin/node /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js > ~/.hermes-web-ui/server.log 2>&1 &
```

> ⚠️ 方案 C 缺点：`hermes-web-ui start` 仍会启动旧版，每次都要手动执行这条命令。

### 验证新版已正确启动

```bash
# 1. 查进程
ps aux | grep hermes-web-ui | grep -v grep
# 正确输出应包含 /home/lt-pc/.hermes/node-v23/...（方案C）或 /home/lt-pc/.hermes/node/... 但 version 为 0.5.17（方案A+B）

# 2. 查端口
ss -tlnp | grep 8648

# 3. 查启动日志
grep "version" ~/.hermes-web-ui/server.log
# 应显示 "hermes-web-ui v0.5.17 starting..."
```

---

## 常见故障处理

### 1. npm install 超时
**解决：** `npm config set registry https://registry.npmmirror.com`

### 2. ENOTEMPTY 错误
**解决：** 清理残留目录后重装

### 3. `hermes-web-ui` 命令找不到
**解决：** 加入 PATH 或使用全路径

### 4. 服务已运行但 Token 变了
**解决：** 查看日志 `cat ~/.hermes-web-ui/server.log | grep "token"`；最好设置用户名密码

### 5. 循环软链接自毁（⚠️ 高危坑，修复后首次出现）

**场景**：当 `~/.hermes/node` 已被替换为指向 `~/.hermes/node-v23` 的软链接后，用户按以下顺序操作：
```bash
cd /home/lt-pc/.hermes/node/lib/node_modules/
rm -rf hermes-web-ui          # ❗ 删的是 node-v23/lib/node_modules/hermes-web-ui（真正的源码）
ln -s /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui hermes-web-ui  # ❗ 链接到自己
```

**结果**：
- `hermes-web-ui start` 报错 `Too many levels of symbolic links`
- v0.5.17 源码完全消失（被 rm -rf 删掉了）

**根因**：`~/.hermes/node` → `~/.hermes/node-v23`（软链），所以两个路径指向同一个地方。`rm -rf` 时你以为删的是另一个副本，其实删的是原件。

**修复**：
```bash
# 1. 删除循环链接
rm -f /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui

# 2. 重新安装 v0.5.17
npm install -g hermes-web-ui@0.5.17 --registry=https://registry.npmmirror.com

# 3. 验证
grep version /home/lt-pc/.hermes/node/lib/node_modules/hermes-web-ui/package.json
# 应显示 "version": "0.5.17"

# 4. 启动
hermes-web-ui start
```

**预防**：替换 Node 软链后，永远不要在 `node/lib/node_modules/` 下直接操作 `hermes-web-ui` 目录。用 npm 管理，别手动删链。

### 6. Web UI API 速率限制（429 Too Many Requests）

**症状**：在 Web UI 页面频繁点击按钮（如切换页面、刷新、查询等）后，所有 API 调用返回 429。页面显示空白或「加载失败」。

**原因**：Web UI v0.5.17 内置了 API 限流机制，短时间内过多请求会触发封锁。

**解决（重启清空）**：
```bash
kill $(ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}')
hermes-web-ui start
```

**预防**：不要在页面内疯狂点击。每次加载数据前等待前一次完成。

---

### 6a. 登录失败次数限流 — 源码级分析（与 API 429 不同）

**症状**：输入账号密码或 Token 后提示「登录失败次数过多，请稍后重试」，但 Web UI 服务正常运行、页面能打开。

**原因**：Web UI v0.5.17 有独立的登录限流机制，记录在 `~/.hermes-web-ui/.login-lock.json` 中，与 API 请求限流（会返回 429）**是两个不同机制**。

**限流逻辑**（通过读取 `.login-lock.json` 分析）：

```javascript
// 用 Node.js 读取锁文件诊断（更准确，避免 Python sqlite3 的 WAL 问题）
/home/lt-pc/.hermes/node-v23/bin/node -e "
const d = JSON.parse(require('fs').readFileSync(
  process.env.HOME + '/.hermes-web-ui/.login-lock.json', 'utf-8'
));
console.log(JSON.stringify(d, null, 2));
"
```

输出示例及解读：
```json
{
  "tokenIpMap": {           // Token 登录失败记录
    "127.0.0.1": {          // 本机 IP 被锁
      "count": 3,           // 失败 3 次
      "firstFailureAt": 1778601829063,  // 第一次失败的时间戳(ms)
      "lockedUntil": 1778605673819      // 锁到什么时候
    }
  },
  "passwordIpMap": {},      // 密码登录失败记录 → 空 = 没锁
  "globalLockedUntil": 1778602073818   // 全局锁截止时间
}
```

**密码登录（passwordIpMap）和 Token 登录（tokenIpMap）的锁是独立的。** 一个被锁不影响另一个。

**解决（秒解，不需要重启 Web UI）**：
```bash
# 直接删除锁文件即可，不影响账号密码和 Token
rm ~/.hermes-web-ui/.login-lock.json
```
删完后刷新页面，两种方式都能登。

**⚠️ 极端情况：如果锁文件删了还报「Too many login attempts」**

某些极端场景下，Web UI 可能缓存了限流状态在内存中，或 `lockedUntil` 的时间戳指向未来很远的时间（锁并没有随文件删除而释放）。此时需要：

```bash
# 杀 Web UI 进程
kill $(cat ~/.hermes-web-ui/server.pid 2>/dev/null) 2>/dev/null
sleep 2

# 删锁文件（确保干净）
rm -f ~/.hermes-web-ui/.login-lock.json

# 重启 Web UI（用目标 Node 版本的全路径）
/home/lt-pc/.hermes/node-v23/bin/node \
  /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js \
  > ~/.hermes-web-ui/server.log 2>&1 &
```

重启后浏览器刷新页面，重新输入账号密码或 Token 即可。

**🔑 完整限流常量解析（从 minified JS 源码反编译）：**

Web UI v0.5.17 的 `dist/server/index.js` 中包含以下限流常量：

```javascript
ki = 3                      // 单 IP 最大失败次数
Pq = 15 * 6e4 = 900000ms    // 密码失败记录过期时间（15分钟）
zi = 60 * 6e4 = 3600000ms   // IP 锁定时长（60分钟！）
Ot = 10000ms                // IP Map 清理阈值（超过 10000 个条目才清理）
_q = 6e4                    // 每分钟窗口（60秒）
$q = 100                    // 每分钟最大请求数
xi = 50                     // 全局总失败阈值
Ui = 30 * 6e4 = 1800000ms   // 全局锁定时长（30分钟）
```

**四个关键函数的作用：**

| 函数 | 作用 | 白名单改造点 |
|------|------|------------|
| `Ki(I)` | 检查密码登录的限流状态 | 入口加白名单判断 |
| `Si(I)` | 检查 Token 登录的限流状态 | 入口加白名单判断 |
| `fi(I)` | 密码登录失败→记次数→可能上锁 | 入口加白名单跳过 |
| `Ti(I)` | Token 验证失败→记次数→可能上锁 | 入口加白名单跳过 |

**调用链：**

1. Token 验证中间件 `Tt(I)`：获取 IP → 调 `Si(ip)` 检查 → 如果失败调 `Ti(ip)` 记次数
2. 登录处理函数 `A5(I)`：获取 IP → 调 `Ki(ip)` 检查 → 如果密码错误调 `fi(ip)` 记次数

**🔧 修改方法：对 127.0.0.1 添加白名单**

在 `Ki`、`Si`、`fi`、`Ti` 四个函数入口增加白名单判断，让本地 IP 永远不被限流：

```javascript
// 修改前：
function Ki(I){let G=Mi();if(G)return G;...}
function Si(I){let G=Mi();if(G)return G;...}
function fi(I){let G=ji(S.passwordIpMap,I);...}
function Ti(I){let G=ji(S.tokenIpMap,I);...}

// 修改后：
function Ki(I){if(I==="127.0.0.1"||I==="::1")return{allowed:!0};let G=Mi();if(G)return G;...}
function Si(I){if(I==="127.0.0.1"||I==="::1")return{allowed:!0};let G=Mi();if(G)return G;...}
function fi(I){if(I==="127.0.0.1"||I==="::1")return;let G=ji(S.passwordIpMap,I);...}
function Ti(I){if(I==="127.0.0.1"||I==="::1")return;let G=ji(S.tokenIpMap,I);...}
```

**效果：**
- 127.0.0.1 可以无限次失败而不触发任何锁
- 127.0.0.1 也不计入全局失败计数器（`globalTotalFailures`）
- 其他 IP（如 WSL 网段的 172.x.x.x）继续受限流保护
- 修改后重启 Web UI 生效

**验证白名单是否生效：**
```bash
# 连续5次用错误 Token 请求受保护的 API
for i in 1 2 3 4 5; do
  curl -s http://localhost:8648/api/sessions \
    -H "Authorization: Bearer wrong_token$i"
done
# 全部返回 {"error":"Unauthorized"}，但没有「Too many login attempts」
# 且锁文件为空：
cat ~/.hermes-web-ui/.login-lock.json  # → 应输出 {} 或无内容
```
- IP 本地锁：`zi=60` — 约 60 秒
- 全局锁（50 次以上全局失败）：`Ui=30` — 约 30 秒
- 但在某些场景下（如连续多次快速失败），`lockedUntil` 的值会因 Web UI 内部的指数退避或累积机制而远大于预设值

**账号密码安全**：`.login-lock.json` 只管限流计数器，**不存密码**。用户凭据存在 `.credentials` 和 `.token` 文件中，删锁文件不影响。

---

### 6b. Web UI 凭据文件清单

| 文件 | 路径 | 作用 | 可以删吗？ |
|------|------|------|-----------|
| `.login-lock.json` | `~/.hermes-web-ui/.login-lock.json` | 登录失败次数和锁定时长 | ✅ 删了等于解限流 |
| `.credentials` | `~/.hermes-web-ui/.credentials` | 存储用户名和密码凭证 | ❌ 删了账号密码重置 |
| `.token` | `~/.hermes-web-ui/.token` | 存储登录 Token | ❌ 删了 Token 失效 |
| `server.pid` | `~/.hermes-web-ui/server.pid` | 记录 Web UI 进程 PID | ✅ 自动重建 |
| `hermes-web-ui.db` | `~/.hermes-web-ui/hermes-web-ui.db` | 会话数据（SQLite，含 WAL） | ✅ 删了重同步 |

---

### 7. 会话同步后 Web UI 仍显示「无数据」

**现象**：日志显示 `[session-sync] sync complete: synced=22, errors=0`，但 Web UI 页面空白无会话。

**原因**：属于不同层面的问题：
1. Web UI 在启动时通过 GatewayManager 连接 Hermes gateway API（端口 8642）
2. 同步成功写入 Web UI 自己的 SQLite 数据库
3. 但 Web UI 前端 API 如果被限流（429），前端拿不到数据所以显示空白
4. 或者数据库是空的（被删除过），同步未触发（因为同步只在新数据库时运行一次）

**诊断步骤**：
```bash
# ① 确认 Web UI 数据库有数据（用 Node.js 的 node:sqlite 模块，不要用 sqlite3 CLI）
/home/lt-pc/.hermes/node-v23/bin/node -e "
const sqlite = require('node:sqlite');
const db = new sqlite.DatabaseSync(process.env.HOME + '/.hermes-web-ui/hermes-web-ui.db');
console.log(db.prepare('SELECT COUNT(*) as c FROM sessions').all());
db.close();
"

# ② 确认 Hermes 后端有数据
hermes sessions stats

# ③ 确认 Gateway 健康
curl http://127.0.0.1:8642/health
```

**解决（强制重同步）**：
```bash
# 先停服务
hermes-web-ui stop || kill $(cat ~/.hermes-web-ui/server.pid)

# 删除数据库（让下次启动时重新同步）
rm -f ~/.hermes-web-ui/hermes-web-ui.db*

# 重启
hermes-web-ui start
```

> ⚠️ **生产路径 vs 开发路径双数据库坑：** v0.5.17 根据 `NODE_ENV` 决定数据库路径：
> - 生产模式（`NODE_ENV=production`）→ `~/.hermes-web-ui/hermes-web-ui.db`
> - 开发模式（未设置 `NODE_ENV`）→ `process.cwd() + "/packages/server/data/hermes-web-ui.db"`
>
> 如果你在桌面目录运行过开发模式，同步的数据会写进前者而 Web UI 读后者（或反之），造成「数据已同步但页面空白」的假象。**诊断时先确认两个路径的状态。**
>
> ⚠️ Web UI v0.5.17 使用 `node:sqlite`（Node ≥22.5 的实验性特性），数据库使用 **WAL 日志模式**。`sqlite3` 系统命令行工具可能因 WAL 未 checkpoint 而读不到数据（报告「no tables」），但 `node:sqlite` 模块能正常读取。**诊断时一定要用 node:sqlite 而非 sqlite3。**

---

### 8. `node-pty` 编译超时/失败
**原因：** node-pty 含原生 C 代码，需要编译工具链。`npm install` timeout 经常发生。
**解决：** 
```bash
apt-get install -y build-essential python3
npm uninstall -g hermes-web-ui && npm install -g hermes-web-ui
```
**注意：** 终端 timeout 至少设 300s+，否则编译中断会残留损坏状态。

### 9. 旧进程残留导致启动失败
**症状：** `hermes-web-ui is already running (PID: xxx)`
**解决：** 先 `hermes-web-ui stop` 停旧服务，再 `start`

### 10. Web UI 终端内杀 gateway 进程后页面断连（WebSocket 断开）

**症状：** 在 Web UI 的终端（Terminal）面板内执行了 `kill -9` 等命令杀掉 gateway 进程后，Web UI 页面卡住不响应、提示「无法连接」或显示断开状态。但 `hermes-web-ui` 和 `hermes gateway` 进程实际上都已自动恢复。

**根因：** Gateway 进程使用 `--replace` 参数启动，被杀后 **秒级自动重启**（PID 可能变化，端口按配置重新分配）。但浏览器与 Web UI 服务之间的 **WebSocket 连接** 在杀掉 gateway 进程的一系列连锁异常中断后被切断，且前端不会自动重连，页面停留在「断开」状态。

**Web UI 自己的 GatewayManager 机制** 会尝试重启网关进程，并且日志会显示 `[chat-run-socket] socket xxx resumed session` 等恢复行为 —— 但浏览器端无法感知。

**诊断确认服务是否真正恢复：**
```bash
# ① 确认 gateway 健康
curl -s http://127.0.0.1:8642/health
# 应返回 {"status": "ok"}

# ② 确认 Gateway 进程存在
ps aux | grep 'hermes.*gateway' | grep -v grep

# ③ 确认 Web UI 服务运行
ps aux | grep 'hermes-web-ui' | grep -v grep

# ④ 确认端口监听
ss -tlnp | grep -E '8642|8648'
```

**解决：**
1. **首选（90% 情况适用）**：直接**刷新浏览器页面**（F5 或 Ctrl+R），重新建立 WebSocket 连接
2. **如果刷新无效**：关掉 Web UI 全部标签页，重新打开 `http://localhost:8648` 登录
3. **极少数情况**：Web UI 服务自身也需要重启 → `kill $(cat ~/.hermes-web-ui/server.pid)` → `hermes-web-ui start`

> ⚠️ **预防**：不要在 Web UI 终端内执行 `kill -9` 操作 gateway 相关进程。如果确需操作，优先在 Web UI 的 Settings → Gateway 面板中操作，或直接在 WSL 终端（非 Web UI 内置终端）中执行。如果必须在 Web UI 终端内执行，预先了解会导致浏览器端 WebSocket 重连需要手动刷新。同时注意 `kill -9 $(pidof python)` 会杀掉 Hermes 自身进程 —— 自保原则：始终确认目标 PID 不在自己的进程树中。
>
> **⚠️ 更严重的连锁风险：** 在 Web UI 终端内 `kill -9` gateway 进程后，Web UI 的 GatewayManager 会在下一次启动时执行 `detectAllOnStartup()` → `startAll()`。此过程中它会：
> 1. 读取 `api_server.extra.host` → 如果之前被篡改为 `0.0.0.0`，会判断为「remote profile」跳过检测
> 2. 找不到已注册的 gateway → 调用 `resolvePort()` → 把 `0.0.0.0:8652` 等错误配置写入 `config.yaml`
> 3. 代理路由 `getUpstream()` fallback 到 `http://0.0.0.0:8652` → 所有 API 调用失败
>
> **最终表现：** Web UI 页面能打开但显示「未连接」，`curl` 代理路径返回 `Proxy error: fetch failed`，即使直接 `curl gateway` 健康检查正常。**杀 gateway 一个操作可能连带弄坏 config.yaml，需要修复后重启才能恢复。**

### 10a. 「Proxy error: fetch failed」— GatewayManager 改写 config.yaml 导致代理路由断裂

**症状：** 页面正常打开（SPA 加载成功），但显示「未连接」，对话无响应。`curl` 测试 Web UI 代理路径返回 `{"error":{"message":"Proxy error: fetch failed"}}`，但直接访问 gateway `/health` 和 `/v1/models` 均正常。

**根因链条（🔥 重点）：**

GatewayManager 在 `startAll()` 阶段执行以下逻辑，**篡改了 `~/.hermes/config.yaml`**：

```
① 触发场景：在 Web UI 终端内 kill -9 杀了 gateway 进程（如 dev/op profile）
   → GatewayManager 在 Web UI 重启后执行 detectAllOnStartup() → startAll()
   → 会清理旧进程并重新分配端口

② detectStatus() 检测 → 读取 api_server.extra.host 发现被之前 GatewayManager 写成了 "0.0.0.0" 
   → 第一次执行时还可能因为端口冲突（如 GatewayManager 自己在上一次启动时把端口改成了 8652）
   → 对 http://0.0.0.0:8652/health 健康检查 → 失败（gateway 实际在 127.0.0.1:8642）
   → 网关未注册到 this.gateways 列表

③ startAll() 阶段 → 看到 host=0.0.0.0（不是 127.0.0.1，不是 localhost）
   → 判断为 "remote profile" → 跳过 auto-start

④ 代理路由 fallback → getUpstream() 返回 readProfilePort() 的值
   → http://0.0.0.0:8652  ← 完全错误的地址
   → fetch 失败 → "Proxy error: fetch failed"
```

**关键诊断命令：**
```bash
# 查当前配置
grep -A6 "api_server:" ~/.hermes/config.yaml | head -10

# 如果发现 host=0.0.0.0 且 port 不是 8642，就是这个问题
```

**修复：**
```bash
# ① 停 Web UI
kill $(ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}')

# ② 修正 config.yaml
# 把 api_server.extra 段改为：
#   port: 8642
#   host: 127.0.0.1
# 直接用 sed：
sed -i '/api_server:/,/^[a-z]/{
  s/port:.*/port: 8642/
  s/host:.*/host: 127.0.0.1/
}' ~/.hermes/config.yaml

# ③ 重启 Web UI（用全路径，带 BIND_HOST）
BIND_HOST=127.0.0.1 /path/to/node /path/to/hermes-web-ui/dist/server/index.js > ~/.hermes-web-ui/server.log 2>&1 &

# ④ 验证代理链路
curl -s -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)" http://127.0.0.1:8648/v1/models
# 应返回模型列表，而非 "Proxy error"
```

**⚠️ 预防：**
- GatewayManager 的 `resolvePort()` 和 `writeProfilePort()` 在每次启动/检测时都可能改写 config.yaml。不要在 GatewayManager 介入之前手动运行 `hermes gateway run` 导致端口错乱。
- 如果在 Web UI 终端内 kill 了 gateway，重启 Web UI 后检查 config.yaml 是否被篡改。

---

### 10b. Dev/Op 多 Profile Gateway 端口分配 BUG — GatewayManager resolvePort() 错误重分配

**症状：** Web UI 网关管理页面中，Dev/Op 多个 profile 的 gateway 启动失败，日志显示 `Gateway health check timed out after 15000ms`。虽然默认 profile 的 gateway 正常运行，但多 profile 始终无法启动。

**根因链条：**

```
GatewayManager 日志显示：
  "Assigning port for profile "dev": 8653 → 8643"
  "Assigning port for profile "op": 8654 → 8644"

① GatewayManager 的 resolvePort() 正确读取了 dev/op 配置中的端口（8653/8654）
② 但在 checkPortAvailable() 检测时认为这两个端口"已被占用"
   → 即使 ss -tlnp 显示两个端口都是完全空闲的
   → 问题可能出在 allocatedPorts 集合的内存级校验误判，
     或 resolvePort 中 findFreePort() 的递增逻辑有 bug
③ 重新分配后，resolvePort() 调用 writeProfilePort() 将新端口（8643/8644）写入 config.yaml：
   dev: port: 8643（去掉了之前正确的 extra.key）
   op:  port: 8644
④ GatewayManager 启动 gateway 进程（HERMES_HOME 指向 profile 目录）：
   hermes gateway run --replace
⑤ 该 gateway 进程可能因 --replace 的自我检测机制，最终在**完全不同的端口**上启动
   （如 dev 进程监听 8651 而非 8643，op 监听 8646 而非 8644）
⑥ GatewayManager 的 waitForReady() 对配置端口（8643/8644）做健康检查 → 超时
⑦ 报错："Gateway health check timed out after 15000ms"
⑧ 偶尔还会出现 "Gateway for profile "dev" is alive but unhealthy" 
   （进程活着但在不同端口上没有健康响应）
```

**这是一个 GatewayManager 的 BUG** — `resolvePort()` 错误地重分配了原本空闲的端口，且 `hermes gateway run --replace` 的进程可能因锁定/端口探测机制不遵循配置端口。

**确认存在该 BUG 的日志信号：**
```bash
# 在 server.log 中搜索关键行
grep "Assigning port" ~/.hermes-web-ui/logs/server.log
# 如果看到 "8653 → 8643" 或 "8654 → 8644"，说明 resolvePort 在错误重分配

# 直接检查 config.yaml 是否被篡改
grep -A6 "api_server:" ~/.hermes/profiles/dev/config.yaml
grep -A6 "api_server:" ~/.hermes/profiles/op/config.yaml
# 如果 port 不是配置值且 extra.key 丢失，就是被 GatewayManager 覆盖了
```

**修复方法（推荐：手动启动，绕过 GatewayManager）：**

```bash
# 方法1：手动从终端启动（最可靠，完全绕过 GatewayManager）

# Dev profile
HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace &

# Op profile
HERMES_HOME=~/.hermes/profiles/op hermes gateway run --replace &
```

手动启动后，gateway 会读取 profile 的 config.yaml（注意：如果 config 已被 GatewayManager 篡改，先修正端口再启动）。

**修复方法（备选：重启 Web UI，但要修 config）：**

```bash
# ① 停 Web UI + 清理 dev/op lock/pid
kill $(ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}')
kill $(ps aux | grep 'gateway run' | grep -v '37575' | awk '{print $2}') 2>/dev/null

# ② 修正 dev/op 配置（Python 方式安全写入）
python3 -c "
import os, yaml
for pf, pt in [('dev', 8653), ('op', 8654)]:
    p = os.path.expanduser(f'~/.hermes/profiles/{pf}/config.yaml')
    with open(p) as f:
        c = yaml.safe_load(f) or {}
    c.setdefault('platforms', {})['api_server'] = {
        'enabled': True, 'key': '', 'cors_origins': '*',
        'extra': {'port': pt, 'host': '127.0.0.1', 'key': 'lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE'}
    }
    with open(p, 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    print(f'{pf}: fixed port={pt}')
"

# ③ 删除 lock/pid 文件
python3 -c "
import os
for f in ['dev/gateway.lock','dev/gateway.pid','op/gateway.lock','op/gateway.pid']:
    p = os.path.expanduser(f'~/.hermes/profiles/{f}')
    if os.path.exists(p): os.remove(p)
"

# ④ 清 Web UI 数据库（可选，建议清）
rm -f ~/.hermes-web-ui/hermes-web-ui.db*

# ⑤ 重启 Web UI
BIND_HOST=127.0.0.1 /home/lt-pc/.hermes/node-v23/bin/node \
  /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js \
  > ~/.hermes-web-ui/server.log 2>&1 &

# ⑥ 立刻手动启动 dev/op gateway（以防 GatewayManager 再次篡改）
sleep 5
HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace &
HERMES_HOME=~/.hermes/profiles/op hermes gateway run --replace &
```

**已知局限：**
- Web UI 网关管理页面的「启动」「停止」按钮对 dev/op 可能无效（因为 GatewayManager 的 resolvePort 有 bug）
- 在管理页面上**只能查看到状态**（运行/停止），不能依赖它来启动/停止多 profile 网关
- 多 profile gateways 手动启动后，所有平台通道都能正常路由到对应 profile

**⚠️ `--replace` 不保证使用配置端口的关键发现：**

即使手动执行 `HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace`，gateway 进程仍可能落在**完全不同于配置端口**的端口上。实测案例：

| Profile | 配置端口 | 实际监听端口 |
|---------|---------|-------------|
| dev | 8653 | 8651 |
| op | 8654 | 8646 |

且多次 kill + 重启后，**实际监听端口保持稳定**（dev 始终 8651，op 始终 8646），不受配置值影响。说明 `hermes gateway run --replace` 内部的端口分配机制完全独立于 `config.yaml` 的 `api_server.extra.port` 字段。

**被动修复方案（不对抗，只对齐）：**

如果 gateway 进程已在错误端口上正常运行，不要 kill 重跑（重跑还会落到同样的端口）。直接更新配置文件的端口为实际值：

```bash
# dev 实际在 8651，op 实际在 8646 → 把配置改成实际端口
python3 -c "
import os, yaml
for pf, pt in [('dev', 8651), ('op', 8646)]:
    p = os.path.expanduser(f'~/.hermes/profiles/{pf}/config.yaml')
    with open(p) as f:
        c = yaml.safe_load(f)
    api = c.setdefault('platforms', {}).setdefault('api_server', {})
    extra = api.setdefault('extra', {})
    extra['port'] = pt
    extra['host'] = '127.0.0.1'
    extra['key'] = 'lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE'
    api['enabled'] = True
    api['cors_origins'] = '*'
    with open(p, 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    print(f'{pf}: config port set to {pt}')
"
```

原理：Web UI 的 `detectStatus()` 读取 `config.yaml (platforms.api_server.extra.port)` → 对配置端口做健康检查。如果配置文件端口与实际运行端口一致，健康检查通过，Web UI 正确显示「运行中」。

**适用场景：** 手动启动后 gateway 进程正常运行（端口能连通），但 Web UI 显示「已停止」。**不需要 kill 任何进程，只改配置文件。**

**配置文件完整性检查清单（修复后）：**

```yaml
# ~/.hermes/profiles/dev/config.yaml 的 platforms 段应该是：
platforms:
  api_server:
    enabled: true
    key: ''
    cors_origins: '*'
    extra:
      port: 8653          # 唯一区别
      host: 127.0.0.1
      key: lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE  # 必须保留！
```

```yaml
# ~/.hermes/profiles/op/config.yaml 同理，port 改为 8654
```

> ⚠️ **GatewayManager 会反复篡改配置**：每次 Web UI 启动，GatewayManager 的 `detectAllOnStartup()` → `startAll()` 流程都可能重新调用 `resolvePort()`，把端口改回错误值。手动修复配置后**必须在 Web UI 启动后立即手动拉起 gateway**，不给 GatewayManager 再次改写的机会。

### 10c. detectStatus 盲点：Web UI 显示「已停止」但 gateway 进程实际在跑

**症状：** Web UI 网关管理页面上，某个 profile（如 dev 或 op）显示「已停止」或状态异常，但：

```bash
hermes gateway list
# → Gateways: ✓ dev (PID 12345)  — 显示运行中

ss -tlnp | grep hermes
# → LISTEN 0.0.0.0:8651  users:(("hermes",pid=12345))  — 进程活着且在监听
```

直接健康检查到实际端口也能通：
```bash
curl -s http://127.0.0.1:8651/health
# → {"status":"ok"}
```

但 Web UI 列表里 dev 就是灰色/已停止。

**根因（GatewayManager 的 detectStatus 源码）：**

```javascript
async detectStatus(name) {
    const pid = this.readPidFile(name);
    const { port, host } = this.readProfilePort(name);  // ← 读的是 config.yaml 的配置端口
    const url = `http://${host}:${port}`;                 // ← 健康检查对配置端口，不是实际端口
    if (pid && this.isProcessAlive(pid) && await this.checkHealth(url)) {
        // 配置端口与实际一致 → 健康检查通过 → 显示「运行中」
        this.gateways.set(name, { pid, port, host, url });
        return { profile: name, port, host, url, running: true, pid };
    }
    // 配置端口与实际不一致 → 健康检查失败 → 标记为未运行
    this.gateways.delete(name);
    return { profile: name, port, host, url, running: false };  // ← Web UI 显示「已停止」
}
```

`detectStatus()` 只检查**配置文件中记录的端口**的 `/health`，不会去扫描进程实际监听的端口。当 GatewayManager 的 `resolvePort()` 或 `hermes gateway run --replace` 的自主端口分配导致实际端口 ≠ 配置端口时，健康检查走错地址，Web UI 误判为「已停止」。

**诊断三步曲：**

```bash
# ① 看 Web UI 认为的端口（从 config.yaml）
grep -A3 "api_server" ~/.hermes/profiles/<profile>/config.yaml | grep port
# → port: 8643

# ② 看进程实际监听的端口
ss -tlnp | grep hermes | grep -v 8648
# → LISTEN 0.0.0.0:8651  users:(("hermes",pid=65862))
# → LISTEN 127.0.0.1:8642  users:(("hermes",pid=63575))

# ③ 确认哪个 PID 属于哪个 profile
cat /proc/<PID>/environ 2>/dev/null | tr '\0' '\n' | grep HERMES_HOME
# → HERMES_HOME=/home/lt-pc/.hermes/profiles/dev
```

**修复方案（二选一）：**

**方案 A：重启到正确端口（不保留现有 gateway 进程）**
```bash
# 杀掉跑偏的进程
kill <dev-pid>
sleep 1

# 确认端口空闲
ss -tlnp | grep 8643 || echo "port 8643 is free"

# 用正确端口启动
HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace &
sleep 3

# 验证
ss -tlnp | grep 8643
# → LISTEN 127.0.0.1:8643  — 需要跑到配置端口才叫成功
```

**方案 B：改配置对齐实际端口（最稳妥，不杀进程不丢连接）**
```bash
# 确认实际端口（从 ss 查）
# 把 config.yaml 的 port 改为实际值
python3 -c "
import os, yaml
actual_port = 8651  # 从 ss 查到的实际端口
profile = 'dev'
p = os.path.expanduser(f'~/.hermes/profiles/{profile}/config.yaml')
with open(p) as f: c = yaml.safe_load(f)
api = c.setdefault('platforms', {}).setdefault('api_server', {})
extra = api.setdefault('extra', {})
extra['port'] = actual_port
extra['host'] = '127.0.0.1'
extra['key'] = 'lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE'
api['enabled'] = True
api['cors_origins'] = '*'
with open(p, 'w') as f: yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
print(f'{profile}: config port set to {actual_port}')
"

# 刷新 Web UI 页面（F5）
# GatewayManager 的 detectStatus 会重新读取 config — 现在配置与实际一致 → 健康检查通过 → 显示「运行中」
```

**方案 B 的优势：** 不杀进程、不丢微信/钉钉连接、立竿见影。缺点是一次性修复，GatewayManager 下一次调用 `resolvePort()` 仍可能再次改写。

**预防：**
- 多 profile 场景下，不要通过 Web UI 网关管理页面的「启动/停止」按钮操作 dev/op/me 网关 — 用 WSL 终端手动 `HERMES_HOME=` 方式启动
- 如果必须在 Web UI 操作，启动后核实端口是否匹配
- 发现端口偏移后，优先方案 B（改配置对齐实际端口）

---

### 11. Web UI 监听地址控制（BIND_HOST）

**症状：** Web UI 默认监听 `0.0.0.0`（所有网卡），用户浏览器访问时提示「登录尝试过多」、页面断连、或只想限制为本地访问。

**根因：** Web UI v0.5.17 的配置代码中，监听地址逻辑为：
```javascript
function qq(I=process.env){
    return I.BIND_HOST?.trim() || "0.0.0.0"
}
// 使用方式：app.listen(port, BIND_HOST || "0.0.0.0")
```

默认值 `0.0.0.0` 表示监听所有网络接口。修改为 `127.0.0.1` 则仅本机可访问。

**解决（修改监听地址）：**

```bash
# ① 查当前 Web UI PID
ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}'

# ② 杀旧进程
kill <PID>

# ③ 确认端口已释放
ss -tlnp | grep 8648   # 应无输出

# ④ 重启，带 BIND_HOST 环境变量
# 注意：hermes-web-ui start 不支持传环境变量，必须全路径启动
BIND_HOST=127.0.0.1 /path/to/node /path/to/hermes-web-ui/dist/server/index.js > ~/.hermes-web-ui/server.log 2>&1 &

# ⑤ 验证
ss -tlnp | grep 8648
# 应显示 LISTEN 127.0.0.1:8648（而不是 0.0.0.0:8648）
tail -5 ~/.hermes-web-ui/server.log
# 应显示 [bootstrap] listening on 127.0.0.1:8648
```

**浏览器访问：**
- ✅ `http://127.0.0.1:8648`
- ✅ `http://localhost:8648`
- ❌ `http://0.0.0.0:8648`（浏览器中无意义，且用户明确排斥 0.0.0.0 地址，任何场景都不要推荐或使用）
- ❌ 其他机器/其他 WSL IP 无法访问

**⚠️ 注意事项：**
- `BIND_HOST` 只影响 Web UI 服务本身的监听地址，**不影响 gateway（端口 8642）的监听地址**。gateway 的地址由 `config.yaml` 的 `platforms.api_server.extra.host` 控制。
- 重启后浏览器端需要**刷新页面**重新建立 WebSocket 连接。
- **如果在 WSL 中绑定 127.0.0.1，Windows 浏览器的 `localhost:8648` 无法直接访问**（Windows 的 `127.0.0.1` ≠ WSL 的 `127.0.0.1`）。如果你仍需要在 Windows 浏览器中用 `127.0.0.1:8648` 访问，需要双层转发：
  ```
  Windows 浏览器                          WSL 内
  127.0.0.1:8648     Windows 端口转发      WSL 外网 IP:8648    socat    WSL 127.0.0.1:8648
  ─────────────────▶  portproxy       ─────────────────▶       ───────▶  Web UI
  ```
  搭建步骤：
  ```bash
  # ① 在 WSL 内启动 socat（监听 WSL 外网 IP → 转发到 WSL 127.0.0.1:8648）
  # 先查 WSL IP
  WSL_IP=$(hostname -I | awk '{print $1}')
  socat TCP4-LISTEN:8648,bind=$WSL_IP,fork,reuseaddr TCP4:127.0.0.1:8648 &

  # ② 在 Windows 上添加端口转发
  powershell.exe -Command "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=8648 connectaddress=$WSL_IP connectport=8648"

  # ③ 验证
  powershell.exe -Command "netsh interface portproxy show v4tov4"
  # 应显示一行：127.0.0.1:8648 → <WSL_IP>:8648
  ```
  完成后 Windows 浏览器访问 `http://127.0.0.1:8648` 即可通达 WSL 内的 Web UI。

- 如果 socat 和 portproxy 已就位但在 Web UI 中仍然对话无响应 → 检查 `config.yaml` 是否被 GatewayManager 篡改（见 10a/10b 节）。
- 如果想改回 `0.0.0.0`，重启时不传 `BIND_HOST` 即可。

| 文件 | 路径 |
|------|------|
| PID 文件 | `~/.hermes-web-ui/server.pid` |
| 日志文件 | `~/.hermes-web-ui/server.log` |
| Token 文件 | `~/.hermes-web-ui/.token` |

---

## 切换模型

Hermes 提供两种方式切换模型，推荐优先使用第一种。

### 方式一（推荐）：微信/通道内用 `/model` 命令

**任何通道下（微信、Web UI 新对话 CLI、Telegram 等）**，直接在对话中输入：

```
/model Qwen3.6-35B-AWQ --provider custom:qwen3.6-35b
```

**切回 DeepSeek：**
```
/model deepseek-v4-flash --provider deepseek
```

**别名：** `/provider` 命令效果相同。

**优点：** 
- 即时生效，**无需重启网关**（仅当前会话生效）
- 带 `--global` 参数可永久切换：`/model Qwen3.6-35B-AWQ --provider custom:qwen3.6-35b --global`
- 可在任意平台执行（微信、Web UI CLI 终端、Telegram 等）

> ⚠️ **注意事项：**
> - 不带 `--global` 时，切换仅在当前会话生效，新对话仍用默认模型
> - 自定义 provider 必须先在 `~/.hermes/config.yaml` 中注册（见下方示例）
> - Web UI 的 Settings → AI Model 下拉菜单**不显示自定义 provider 模型**（它是从远程模型目录读取的，只显示内置 provider）

### 方式二（备用）：改配置文件永久切换

```bash
# 切到 DeepSeek
sed -i 's/default: .*$/default: deepseek-v4-flash/' ~/.hermes/config.yaml && \
sed -i 's/provider: .*$/provider: deepseek/' ~/.hermes/config.yaml && \
hermes gateway restart

# 切到 Qwen3.6-35B（本地模型）
sed -i 's/default: .*$/default: Qwen3.6-35B-AWQ/' ~/.hermes/config.yaml && \
sed -i 's/provider: .*$/provider: custom:qwen3.6-35b/' ~/.hermes/config.yaml && \
hermes gateway restart
```

### 多个 Provider 配置示例

在 `~/.hermes/config.yaml` 中配置多个 provider：

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1
providers:
  qwen3.6-35b:
    base_url: http://192.168.31.219:8000/v1
    api_key: sk-123456
    models:
      Qwen3.6-35B-AWQ:
        context_length: 262144
fallback_model:
  provider: custom:qwen3.6-35b
  model: Qwen3.6-35B-AWQ
```

> ⚠️ **配置迁移注意：** 旧版 Hermes 使用 `custom_providers` 段，新版使用 `providers` 段。两者配置文件可能同时存在但只有第一个生效。确保删除旧的 `custom_providers`，只保留 `providers`。
>
> **Web UI 模型下拉不显示自定义 provider 的原因：** Web UI 的 `/api/hermes/available-models` API 返回的 `groups` 列表只包含默认 provider，所有其他自定义 provider 不被自动识别。`model_catalog.providers` 段的配置仍不足以让自定义模型出现在下拉菜单中。**这不是配置问题，是 Web UI 前端的硬限制。** 通过 `/model` 命令切换才是最可靠的方式。
>
> `fallback_model` 可用于让 Qwen 模型在 Hermes 的容灾列表中可见，但不改变 Web UI 模型下拉菜单的显示。

### 查看当前可用模型

```bash
curl -s -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)" \
  http://localhost:8648/api/hermes/available-models | python3 -m json.tool
```

> ⚠️ 必须用 Web UI 登录后的 session cookie 或正确的 Bearer Token 访问。直接用初始安装 Token（硬复制）可能返回 401 Unauthorized。

---

---

## 前端自定义 — 注入自定义 JS/CSS

Web UI 的 SPA 是静态资源（Vue 构建产物），可通过直接编辑 `dist/client/` 下的文件来注入自定义 JS/CSS，无需重新构建。

### 文件结构

```
dist/client/
├── index.html              # 入口 HTML
├── assets/
│   ├── css/                # 构建后的 CSS
│   ├── js/                 # 构建后的 JS + 自定义注入 JS
│   │   ├── index-xxx.js    # 主 App 入口（构建产物）
│   │   ├── slash-picker.js # ✅ 自定义注入的斜杠命令菜单
│   │   └── ...
```

### 注入方法

1. 编写 JS 文件放到 `dist/client/assets/js/` 目录
2. 在 `dist/client/index.html` 中添加 `<script src="/assets/js/your-file.js"></script>`
3. 重启 Web UI 生效

### 主题自适应（CSS Variables）

Web UI 使用 CSS 自定义属性实现主题切换，`MarkdownRenderer-xEKocnSy.css` 中定义了**全局（unscoped）CSS 变量**：

| 变量 | 浅色主题 | 深色主题 (`.dark`) |
|------|---------|-------------------|
| `--bg-primary` | `#fafafa` | `#1a1a1a` |
| `--bg-secondary` | `#f0f0f0` | `#252525` |
| `--bg-card` | `#fff` | `#333` |
| `--bg-card-hover` | `#fafafa` | `#333` |
| `--bg-input` | `#fff` | `#2a2a2a` |
| `--border-color` | `#e0e0e0` | `#3a3a3a` |
| `--border-light` | `#ebebeb` | `#333` |
| `--accent-primary` | `#333` | `#e0e0e0` |
| `--accent-hover` | `#1a1a1a` | `#f5f5f5` |
| `--accent-muted` | `#888` | `#888` |
| `--text-primary` | `#1a1a1a` | `#f0f0f0` |
| `--text-secondary` | `#666` | `silver` |
| `--text-muted` | `#999` | `#888` |
| `--success` | `#2e7d32` | `#66bb6a` |
| `--error` | `#c62828` | `#ef5350` |
| `--warning` | `#f57f17` | `#ffb74d` |
| `--accent-info` | `#4a90d9` | `#6ba3d6` |
| `--code-bg` | `#f4f4f4` | `#1e1e1e` |

**注意**：Vue scoped CSS 使用 `[data-v-xxx]:root` 选择器，这些变量只对 Vue 组件内部生效。**自定义注入的 JS/CSS 必须使用 `:root`（unscoped）定义的变量**（来自 MarkdownRenderer CSS）。`.dark` 类由 HTML 的 `<script>` 在页面加载前添加，自定义 JS 的 CSS 中直接使用 `.dark` 选择器或者 `var(--xxx)` 即可自动适配。

**最佳实践**：自定义注入的 CSS 中所有颜色值都用 `var(--xxx)` 引用，并加 fallback：
```css
background: var(--bg-card, #18181e);
color: var(--text-primary, #eee);
border: 1px solid var(--border-color, #2a2a3a);
```

### 参考实现：slash-picker.js

slach-picker.js 是一个完整的 Web UI 前端自定义参考实现，实现了：
- **斜杠命令菜单**：输入 `/` 弹出，支持 /stop, /clear, /model, /think, /fallback, /reasoning, /backup, /help
- **主题自适应**：全部颜色使用 CSS 变量，自动适配深色/浅色模式
- **键盘导航**：⬆⬇ 选择、⏎ 执行、⬅ 返回、Esc 关闭
- **层级子菜单**：/think 展开子菜单，键盘可进入/退出子菜单导航
- **API 调用**：/reasoning 切换显示推理过程、/backup 调用备份 API
- **帮助弹窗**：/help 显示全量命令列表

详细实现见 reference 文件：**[references/slash-picker-impl.md](references/slash-picker-impl.md)**

### 注入后的重启流程

修改 JS/CSS/HTML 后必须重启 Web UI：

```bash
# 1. 杀旧进程
kill $(ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}')

# 2. 启动
/home/lt-pc/.hermes/node-v23/bin/node \
  /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js

# 3. 验证
ss -tlnp | grep 8648
```

浏览器端只需**刷新页面**（F5/Ctrl+R），新注入的 JS 会被浏览器缓存的可能需要强制刷新（Ctrl+Shift+R）。

---

## 重要认知

**Web UI 不是消息发送入口。** 它只负责查看历史会话、管理配置、查看用量等。所有消息发送走各自平台通道（微信、Telegram 等）。这与 OpenClaw 等框架不同，Hermes 的 Web UI 是只读的管理面板。

---

### 12. Web UI 前端架构：数据同步与实时更新机制

#### 概述

Web UI 前端（Vue 3 + socket.io + Pinia）的数据同步机制决定了什么数据能「实时显示」、什么需要「手动刷新」。

#### 架构图

```
                      REST API (initial load)
   Web UI Frontend  ──────────────────────────►  Hermes Gateway
   (Vue + Pinia)    ◄──────────────────────────  (port 8642)
                      socket.io (/chat-run)
                           │
                           │ real-time push
                           ▼
                   Vue Pinia Store
                   (chat.sessions,
                    chat.activeSession,
                    chat.activeSessionId)
                           │
                           ▼
                   DOM / Display
```

#### 前端连接机制

Web UI 使用 **socket.io**（不是原生 WebSocket）连到 Hermes Gateway：

```javascript
// 源代码反编译要点
function Bo() {
  if (Y?.connected) return Y;
  Y && (Y.removeAllListeners(), Y.disconnect());
  const o = zo(), e = wo();  // o = gateway URL, e = auth token
  return Y = Hn(`${o}/chat-run`, {
    auth: { token: e },
    query: { profile: n },
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
  });
  // Register event handlers...
}
```

关键配置：
- 连接地址：`<gateway_url>/chat-run`
- 认证方式：Bearer token（来自 `.token` 文件或 localStorage `hermes_api_key`）
- 传输协议：WebSocket 优先，降级到 HTTP polling
- 重连：无限重试，间隔 1-10 秒

#### Socket.io 事件清单

| 事件 | 方向 | 用途 |
|------|------|------|
| `message.delta` | Gateway → Frontend | 流式消息内容推送 |
| `reasoning.delta` | Gateway → Frontend | 推理过程推送 |
| `thinking.delta` | Gateway → Frontend | 思考过程推送 |
| `tool.started` / `tool.completed` | Gateway → Frontend | 工具调用状态 |
| `run.started` / `run.completed` / `run.failed` | Gateway → Frontend | 运行生命周期 |
| `run.queued` | Gateway → Frontend | 排队通知 |
| `compression.started` / `compression.completed` | Gateway → Frontend | 上下文压缩 |
| `abort.started` / `abort.completed` | Gateway → Frontend | 中止事件 |
| `usage.updated` | Gateway → Frontend | 用量更新 |
| `run` | Frontend → Gateway | 发送新消息（emit） |
| `abort` | Frontend → Gateway | 中止当前运行 |
| `resume` | Frontend → Gateway | 恢复会话 |

**注意**：socket.io 只处理**流式数据推送**（新消息的发送和接收），不负责会话列表刷新。没有 `refresh`、`reload`、`session.updated` 等事件。

#### Pinia 状态管理（前端关键数据结构）

通过 CDP 调试发现 Pinia 有以下 stores：

```javascript
// 通过浏览器控制台访问
const pinia = document.querySelector('#app').__vue_app__.config.globalProperties.$pinia;
pinia.state.value  // 包含以下 store:
// { app, chat, profiles, settings, session-browser-prefs, files }
```

**chat store 的核心状态：**
```
chat.sessions         → 会话列表（含消息，在内存中缓存）
chat.activeSessionId  → 当前活跃会话 ID
chat.activeSession    → 当前活跃会话对象（含 messages 数组）
chat.focusMessageId   → 焦点消息 ID
chat.isLoadingSessions → 加载状态
chat.sessionsLoaded   → 是否已加载
chat.isLoadingMessages → 消息加载状态
```

#### 数据缓存生命周期

```
页面加载
  │
  ├── fetch /api/hermes/sessions          → 获取会话列表 → 存入 chat.sessions
  ├── fetch /api/hermes/sessions/:id      → 获取当前会话消息 → 存入 chat.activeSession
  │
  ├── 用户切换会话
  │     └── NO API CALL（从 chat.sessions 缓存中读取，不重新请求后端）
  │
  ├── 用户发消息
  │     └── socket.emit("run", {...})     → Gateway 处理
  │     └── socket.on("message.delta")    → 流式更新到 Pinia → DOM
  │
  ├── 用户刷新页面 (F5)
  │     └── 重新执行初始加载流程
  │
  ├── socket 重连（gateway 重启后）
  │     └── 重新加载会话列表（部分场景）
  │
  └── 用户切到其他会话再切回
        └── 从 Pinia 缓存读取，不会重新请求后端
```

#### 数据同步的根本瓶颈

**直接写数据库为什么不会显示：**
```
[Python/小何] 写入 state.db + hermes-web-ui.db
       │
       ▼
Web UI 服务器（Node.js）
       │
       ├── 数据库有数据 ✅
       ├── 没有 API 请求触发新的数据库读取 ❌
       │
       ▼
Web UI 前端（浏览器）
       │
       ├── Pinia store 仍持有旧数据 ❌
       ├── 没有 socket.io 推新消息 ❌
       └── 没有轮询机制 ❌
```

**为什么 gateway 重启几次后才显示：**
之前观察到的「断网关后数据出现了」是**凑巧**——不是 gateway 重启触发的，而是：
1. 用户执行了 F5 刷新（手动）
2. 或用户切换了会话再切回
3. 或页面因 WebSocket 断连自动重连后重新加载

**解决方案（2026-05-14 验证通过）**：通过 CDP 调用 Pinia chat store 的 `refreshActiveSession()` 方法可以强制触发前端重新从 REST API 加载数据。完整工作流见 `web-ui-pinia-refresh` 技能。

**总结**：前端刷新有三种方式：
1. ✅ **CDP + refreshActiveSession()** — 不中断体验、无需用户操作（推荐）
2. ✅ **用户手动 F5 或切会话** — 传统方式
3. ✅ **通过 gateway API 正常发消息** — socket.io 自动推送

#### CDP 调试 Web UI 前端的方法

通过 Chrome DevTools Protocol 可以直接在浏览器中操作 Vue 应用：

```javascript
// 1. 访问 Vue App
const app = document.querySelector('#app').__vue_app__;

// 2. 访问 Pinia store
const pinia = app.config.globalProperties.$pinia;

// 3. 查看 chat store
const chatState = pinia.state.value.chat;
console.log('Sessions:', chatState.sessions?.length);
console.log('Active session:', chatState.activeSessionId);
console.log('Messages count:', chatState.activeSession?.messages?.length);

// 4. 查看是否有其他 store
console.log('Store keys:', Object.keys(pinia.state.value));

// 5. 手动触发会话重新加载（需要找到 store 的 action 方法）
// 但注意：Vue 3 中 store 的 actions 不暴露在 .state.value 上
// 需要找到 pinia._s.get('chat') 来访问 actions
```

**通过 CDP 模拟用户操作：**
```javascript
// 点击会话列表中的另一个会话，然后点回来（触发重新加载）
const items = document.querySelectorAll('.session-item');
if (items.length >= 2) {
  items[1].click();  // 切到第二个会话
  setTimeout(() => items[0].click(), 500);  // 切回来
}
```

#### 实用调试命令

```javascript
// 检查 Web  UI 的 WebSocket/socket.io 连接
const conns = performance.getEntriesByType('resource');
const ws = conns.filter(e => e.name.includes('chat-run'));
console.log('Socket connections:', ws.map(e => e.name));

// 覆盖 fetch 捕获网络请求（检测切换会话时是否有 API 调用）
const origFetch = window.fetch;
const captured = [];
window.fetch = function(url, opts) {
  captured.push(url);
  return origFetch.apply(this, arguments);
};
// 执行操作后检查 captured 数组

// 检查页面身份验证
const token = localStorage.getItem('hermes_api_key');
console.log('API key present:', !!token);
```

#### 已知限制

- 没有 `refresh()` 或 `reload()` 等前端 API 来强制从服务器重新加载会话数据
- 通过直接写数据库 + 断开 gateway 的组合方式不稳定，每次都需要用户手动干预
- 唯一能可靠触发前端刷新的方式是：**通过正确链路发消息**（API/gateway → socket.io → Pinia → DOM）或**用户手动刷新页面**

--- 

### 13. 数据库写入实验：WAL 模式可行但非实时

**场景**：小何（默认 profile）通过 API 向 op/me/dev profile 派活后，需要让对话内容出现在 Web UI 的现有会话中（如「小何与op」）。

**核心发现**：WAL 模式写库**不会崩 Web UI**，但数据不会实时显示，需要用户手动切换会话触发重新加载。

#### 正确的写入方式（WAL 模式 + BEGIN IMMEDIATE）

```python
import sqlite3, time

conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')
conn.execute('PRAGMA journal_mode=WAL')    # ✅ 关键：匹配 Web UI 的 WAL 模式
conn.execute('BEGIN IMMEDIATE')            # ✅ 关键：立即锁定防止竞争

now = time.time()
conn.execute(
    'INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
    ('mp5guacelv7uea', 'user', '消息内容', now)
)
conn.execute(
    'INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
    ('mp5guacelv7uea', 'assistant', 'op回复', now + 0.001)
)
conn.commit()
conn.close()
```

**验证记录（2026-05-14）**：
- ✅ Web UI 进程不断、网关不崩
- ✅ 数据库正确写入（`SELECT` 可查到）
- ❌ 前端不实时显示（Vue Pinia store 缓存问题）
- ✅ 用户切换到其他会话再切回即可看到（已验证可行）

> ⚠️ **不要用默认 journal_mode**（=delete），那会与 Web UI 的 WAL 模式冲突，导致 Node.js 进程崩溃、浏览器显示「网关断连」。
>
> ⚠️ 写入后 WAL checkpoint（`PRAGMA wal_checkpoint(TRUNCATE)`）不是必须的 — 数据已在主库。checkpoint 返回 `(0, 0, 0)` 是正常的，表示没有需要合并的 WAL 帧。

**问题根因**：Web UI 的前端（Vue + Pinia store）在页面加载时通过后端 API `/api/hermes/sessions/conversations/:id/messages` 读取消息并缓存到内存中。直接写数据库绕过了 API 层，前端不知道有数据更新，所以不显示。切换会话或 F5 刷新会触发重新 API 调用，此时新数据才可见。

#### 另一条路径：Web UI 反向代理

Web UI 内置反向代理，可通过 `x-hermes-profile` 头或 `?profile=` 参数指定目标 gateway：

| 请求路径 | 转发路径 | 目标 |
|---------|---------|------|
| `/api/hermes/v1/chat/completions` | `/v1/chat/completions` | Gateway |
| `/api/hermes/sessions` | `/api/sessions` | Gateway |
| `/v1/chat/completions` | `/v1/chat/completions` | Gateway |

关键函数 `HYI(I, G)` 自动**跳过传入的 authorization 头**，替换为 Gateway 的 API key（通过 `Sk().getApiKey(VF(I))` 获取）。这意味着你不需要手动传递 Gateway 的 API key。

**认证问题（未完全解决）**：Web UI 的 `Tt` 中间件对所有 `/api/*` 和 `/v1/*` 路径进行 Bearer token 验证（token 来自 `~/.hermes-web-ui/.token` 文件）。用 curl 请求代理路径时，即使传了正确的 token 仍返回 401。浏览器端登录后 token 存储在 `localStorage.getItem("hermes_api_key")` 中，前端发请求时自动附带。

**认证中间件调用链**：
```javascript
// 启动初始化
let I = await sl();            // 从 .token 文件读取
let b = Tk(G, Tt(I));         // 创建路由链，Tt(I) 作为中间件
G.use(b);                      // 整个应用加载路由链

// Tt 函数
function Tt(I) {
    return async (G, l) => {
        if (!I) { await l(); return }  // 无 token → 跳过认证
        let c = G.headers.authorization || "",
            b = c.startsWith("Bearer ") ? c.slice(7) : G.query.token || "";
        if (!b || b !== I) {            // token 不匹配
            // 只对 /api/* /v1/* /upload/* 做认证
            let d = eY(G);              // 获取 IP
            let W = Si(d);              // 检查 rate limit（127.0.0.1 已白名单化）
            if (!W.allowed) { G.status = W.status; return }  // 被限流
            Ti(d);                      // 记次数
            G.status = 401; return      // 返回未授权
        }
        await l()  // 认证通过，继续
    }
}
```

#### 对比三种方案

| 方案 | 实时性 | 稳定性 | 需要用户操作 |
|------|--------|--------|------------|
| 用户在 Web UI 直接发消息 | ✅ 实时 | ✅ 稳定 | 用户自行操作 |
| API 派活 + WAL 写库 | ❌ 非实时 | ✅ 稳定（WAL模式） | 用户切会话刷新 |
| Web UI 代理转发 | 待定 | 待定 | 待定（认证未解决） |

#### 推荐工作流

```
[用户] 在 Web UI 切到 op profile → 打字发指令 → op 回复 → [用户] 切回 default 跟我说结果
```

或：

```
[小何] API 派活给 op → [小何] WAL 写库（双库） → [小何] 重启 op gateway → Web UI 自动重连同步
```

#### 最优方案：双库写入 + gateway 重启触发同步

**在 2026-05-14 会话中验证的完整流程：**

```python
# 1. 写两个库（op/state.db + hermes-web-ui.db）
import sqlite3, time

session_id = "mp5guacelv7uea"  # 已有的"小何与op"会话ID

for db_path in ["/home/lt-pc/.hermes/profiles/op/state.db",
                 "/home/lt-pc/.hermes-web-ui/hermes-web-ui.db"]:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("BEGIN IMMEDIATE")
    now = int(time.time())
    conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                 (session_id, "user", "消息内容", now))
    conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                 (session_id, "assistant", "回复内容", now + 1))
    conn.execute("UPDATE sessions SET message_count = message_count + 1 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# 2. 重启目标 profile 的 gateway（触发 Web UI 重连 → 重刷会话状态）
import subprocess
# 找目标 gateway 的 PID（通过端口）
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if '8645' in line:  # op 网关端口
        pid = line.split('pid=')[1].split(',')[0] if 'pid=' in line else None
        if pid:
            subprocess.run(["kill", pid])
            # gateway 会自动用 --replace 重新起来
```

**验证结论（2026-05-14 晚更新）：**
- ✅ 双库写入成功
- ❌ **gateway 重启不会触发 Web UI 前端刷新消息列表**（用户反馈「不行啊」）
- ⚠️ 用户需要手动 **F5 刷新页面** 或 **切换会话再切回** 才能看到新消息
- ❌ `hermes chat --resume <session_id>` 挂死不可用（gateway 运行时 CLI 阻塞）
- ✅ WAL + BEGIN IMMEDIATE 写入 hermes-web-ui.db 无锁冲突（Web UI 不断连）

**关键注意事项：**
- 双库都要写，Web UI 不读 op/state.db，只读自己的 hermes-web-ui.db
- 写 hermes-web-ui.db 必须用 `PRAGMA journal_mode=WAL` + `BEGIN IMMEDIATE`，否则锁冲突崩 Web UI
- op/state.db 的 `messages` 表没有 auto_increment ID，手动插入即可
- hermes-web-ui.db 的 `messages` 表有 auto_increment ID（SQLite 自动处理）
- **gateway 重启不会自动同步**，用户需手动 F5 刷新或切会话
- session consolidation：所有 op 消息必须写入现有会话（如"小何与op"的 `mp5guacelv7uea`），不创建新会话才能让用户在 Web UI 中连续查看

#### 更轻量的替代：纯 WAL 写库（跳过 gateway 重启）

如果不想中断用户的 Web UI 体验，只用 WAL 写库不加 gateway 重启：

---

## 参考

- GitHub: https://github.com/EKKOLearnAI/hermes-web-ui
- npm: https://www.npmjs.com/package/hermes-web-ui
- 限流源码分析 & 127.0.0.1 白名单改造 (2026-05-14): [references/session-20260514-ratelimit-source-code-analysis.md](references/session-20260514-ratelimit-source-code-analysis.md)
- 部署日志 (2026-05-12): [references/deploy-log-20260512.md](references/deploy-log-20260512.md)
- 部署日志 (2026-05-13 续): [references/deploy-log-20260513.md](references/deploy-log-20260513.md)
- WSL 网络恢复 + GatewayManager 配置修复 (2026-05-13): [references/session-20260513-wsl-networking-recovery.md](references/session-20260513-wsl-networking-recovery.md)
- Dev/Op Profile Gateway 端口分配 BUG (2026-05-13): [references/session-20260513-dev-op-profile-gateway-bug.md](references/session-20260513-dev-op-profile-gateway-bug.md)
- Web UI 反向代理 & 数据库 WAL 模式写入实验 (2026-05-14): [references/session-20260514-database-write-proxy-mechanism.md](references/session-20260514-database-write-proxy-mechanism.md)
