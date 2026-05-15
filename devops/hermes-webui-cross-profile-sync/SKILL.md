---
name: hermes-webui-cross-profile-sync
description: "Web UI 跨 Profile 消息同步方案 — 后端合并 + 前端3秒轮询，让 op/dev/me 的回复自动显示在浏览器中"
version: 1.0.0
author: 小何 + 腾哥
metadata:
  domain: devops
  tags: [Hermes, WebUI, Profile, CrossProfile, Sync, StateDB]
---

# Web UI 跨 Profile 消息同步方案（SOP）

## 问题

通过 REST API 向 op/dev/me gateway 发送消息后，回复写入了对应 profile 的 `state.db`，但 **Web UI 主聊天面板看不到**。

## 根因

每 profile 有独立的 `state.db`（`~/.hermes/profiles/<name>/state.db`），Web UI 主面板默认只读自己的 `hermes-web-ui.db` 和 default 的 `state.db`，**不读取其他 profile 的 state.db**。

```
POST /v1/runs → op gateway (8645) → op 回复
                                          ↓
                              op/state.db（数据在这里）
                                          ↓
                          Web UI 不读这个库 → ❌ 浏览器看不到
```

## 最终方案：后端合并 + 前端轮询

### 原理

不推数据、不搬数据库、不改 gateway。只在 Web UI 后端 `get()` 加 fallback，前端加 3 秒轮询。

### 改动文件（仅 2 处）

#### 1. 后端：`packages/server/src/controllers/hermes/sessions.ts`

`get()` 函数，先读 Web UI 自己的库，再从所有 profile state.db 读取额外消息，去重合并。完全不在 Web UI 库中时，直接从 profile state.db 构造 session。

添加辅助函数 `fetchAdditionalMessages()`，遍历 `~/.hermes/profiles/<name>/state.db`，按 session_id 查消息，去重后返回。

**类型处理：** 返回 `any[]`，合并时用 `m as any` 推入。

#### 2. 前端：`packages/client/src/stores/hermes/chat.ts`

在 store 初始化结束时加入：

```typescript
if (typeof window !== 'undefined') {
  setInterval(() => {
    if (activeSessionId.value && !isStreaming.value) {
      refreshActiveSession()
    }
  }, 3000)
}
```

### 部署步骤

```bash
# 1. 停 Web UI
hermes-web-ui stop

# 2. 修改源码 → 构建
cd ~/hermes-web-ui
# 手动修改 sessions.ts 和 chat.ts
npm run build

# 3. 部署到 npm 安装目录
NPM_DIR="/home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui"
rm -rf $NPM_DIR/dist/server $NPM_DIR/dist/client
cp -r ~/hermes-web-ui/dist/server $NPM_DIR/dist/
cp -r ~/hermes-web-ui/dist/client $NPM_DIR/dist/

# 4. 更新版本号（可选）
sed -i 's/"version": "0.5.17"/"version": "0.5.22"/' $NPM_DIR/package.json

# 5. 启动
hermes-web-ui start
```

### ⚠️ 部署陷阱

**错误做法：** `cp -r ~/hermes-web-ui/dist /npm/pkg/dist/` → 产生嵌套 `dist/dist/` 目录

**正确做法：** 分别复制 server 和 client：
```bash
rm -rf $NPM_DIR/dist/server $NPM_DIR/dist/client
cp -r ~/hermes-web-ui/dist/server $NPM_DIR/dist/
cp -r ~/hermes-web-ui/dist/client $NPM_DIR/dist/
```

### 启动方式

- ✅ `hermes-web-ui start` / `hermes-web-ui stop` — 原生命令
- ❌ 不用 PM2（PM2 有 2784 次重试记录）
- ❌ 不用 `kill` 手动杀进程

Web UI 和 gateway 进程独立（gateway PPID=1），互不影响。

### 验证命令

```bash
# 1. 发消息给 op
TOKEN=$(cat ~/.hermes-web-ui/.token)
OP_KEY="lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE"

curl -s -X POST http://127.0.0.1:8645/v1/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_KEY" \
  -d '{"input":"回复2个字：测试","session_id":"mp5guacelv7uea","source":"api_server"}'

# 2. 等 5 秒后验证浏览器 API 可见
sleep 5
curl -s "http://localhost:8648/api/hermes/sessions/mp5guacelv7uea" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['session']['messages'][-1]['content'])"
```

### 各 gateway 端口与 Key

| Profile | 端口 | API Key |
|---------|------|---------|
| op | 8645 | `lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE` |
| me | 8644 | `lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE` |
| dev | 8643 | `lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE` |

### 已知会话 ID

| 会话 | session_id |
|------|-----------|
| 小何与op | `mp5guacelv7uea` |
| 小何与me | `mp5oxk4yzvjrnb` |
| 小何与dev | `mp5oybo1k0wa0q` |

### 架构对比

| 方案 | 复杂度 | 稳定性 | 守护脚本 | 改文件数 |
|------|-------|-------|---------|---------|
| ✅ **后端合并+前端轮询（当前）** | 低 | ✅ 高 | ❌ 不需要 | 2 |
| ❌ 旧同步守护（sync-op-to-webui.sh） | 高 | ❌ 低（OOM） | ✅ 需要 | 5+ |
| ❌ 旧 push-message API | 中 | ❌ 低（Web UI 崩溃） | ✅ 需要 | 4+ |
| ❌ 旧 socket.io 推送 | 中 | ❌ 低（事件名不匹配） | ❌ 不需要 | 3+ |

### 5 轮稳定性验证（2026-05-15）

| 轮次 | 发送内容 | op 回复 | 浏览器可见 |
|------|---------|--------|-----------|
| 1 | 回复3个字：第一轮通过 | ✅ 第一轮通过 | ✅ |
| 2 | 回复3个字：第二轮稳 | ✅ 第二轮稳 | ✅ |
| 3 | 回复3个字：三轮过 | ✅ 三轮过 | ✅ |
| 4 | 回复3个字：四轮稳 | ✅ 四轮稳 | ✅ |
| 5 | 回复3个字：五轮过 | ✅ 五轮过 | ✅ |

**系统状态：** Web UI 无崩溃、无异常日志、4 gateway 全部存活、15G 内存用 4.8G。
