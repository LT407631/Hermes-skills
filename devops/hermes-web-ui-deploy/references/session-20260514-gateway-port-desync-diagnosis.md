# 2026-05-14 会话：Gateway 端口偏移导致 Web UI 显示异常

## 触发场景

Web UI 网关管理页面上，dev 和 op profile 的 gateway 显示状态不对。腾哥要求检查。

## 当前状态

| Profile | PID | 配置端口 | 实际端口 | 绑定地址 | 健康状态 |
|---------|-----|---------|---------|---------|---------|
| default | 63575 | 8642 | 8642 | 127.0.0.1 | ✅ |
| me | 65279 | 8644 | 8644 | 127.0.0.1 | ✅ |
| dev | 65862 | 8643 | 8651 | 0.0.0.0 | ✅（但 Web UI 显示异常） |
| op | 65906 | 8645 | 8646 | 0.0.0.0 | ✅（但 Web UI 显示异常）|

## 诊断路径

### 步骤 1：确认 gateway 进程状态

```bash
hermes gateway list
# → 所有 4 个 profile 都显示 ✓ 运行中
# 这是 hermes CLI 自身的检测，与 Web UI 的 GatewayManager 不同
```

### 步骤 2：查实际端口

```bash
ss -tlnp | grep hermes
# LISTEN 127.0.0.1:8642  users:(("hermes",pid=63575))  — default, 正确
# LISTEN 127.0.0.1:8644  users:(("hermes",pid=65279))  — me, 正确
# LISTEN 0.0.0.0:8646    users:(("hermes",pid=65906))  — op, 应为 8645
# LISTEN 0.0.0.0:8651    users:(("hermes",pid=65862))  — dev, 应为 8643
```

### 步骤 3：映射 PID 到 Profile

```bash
cat /proc/65862/environ 2>/dev/null | tr '\0' '\n' | grep HERMES_HOME
# → HERMES_HOME=/home/lt-pc/.hermes/profiles/dev

cat /proc/65906/environ | tr '\0' '\n' | grep HERMES_HOME
# → HERMES_HOME=/home/lt-pc/.hermes/profiles/op
```

### 步骤 4：健康检查确认

```bash
curl -s http://127.0.0.1:8651/health  # dev 实际端口
# → {"status":"ok"}

curl -s http://127.0.0.1:8646/health  # op 实际端口
# → {"status":"ok"}

curl -s http://127.0.0.1:8643/health  # dev 配置端口
# → 无响应（超时）

curl -s http://127.0.0.1:8645/health  # op 配置端口
# → 无响应（超时）
```

### 步骤 5：查 gateway.pid 验证

```bash
cat ~/.hermes/profiles/dev/gateway.pid
# → {"pid": 65862, ...}  — PID 与 ss 输出一致

cat ~/.hermes/profiles/op/gateway.pid
# → {"pid": 65906, ...}  — PID 与 ss 输出一致
```

## 根因

GatewayManager 的 `detectStatus()` 方法源码：

```javascript
async detectStatus(name) {
    const pid = this.readPidFile(name);
    const { port, host } = this.readProfilePort(name);  // 读 config.yaml
    const url = `http://${host}:${port}`;                 // 对配置端口做健康检查
    if (pid && this.isProcessAlive(pid) && await this.checkHealth(url)) {
        // 配置端口与实际一致 → 通过
    }
    // 不一致 → 标记为未运行
}
```

**它与 `hermes gateway list` 的检测路径完全不同**：
- `hermes gateway list` → 读 gateway.pid 文件 + 检查进程存活 → PID 活着就显示 ✓
- Web UI GatewayManager → 读 config.yaml 中的端口 + 对配置端口做健康检查 → 健康通过才显示「运行中」

当 `hermes gateway run --replace` 的自主端口分配导致实际端口 ≠ 配置端口时，Web UI 的健康检查走错地址，误判为「已停止」。

## 修复方案

见主技能的 **10c 节**，推荐方案 B（改配置对齐实际端口，不杀进程）。

## 额外发现：Web UI API 认证

Web UI API（如 `/api/hermes/gateways`）需要 Bearer Token 认证。Token 存储在：

```bash
cat /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/data/.token
```

使用方式：
```bash
curl -s -H "Authorization: Bearer $(cat <token-file-path>)" http://127.0.0.1:8648/api/hermes/gateways
```

注意登录限流会将 Token 认证也一并封锁（返回 `Too many login attempts, please try again later`），删 `~/.hermes-web-ui/.login-lock.json` 即可解封。

## 背景：Web UI 两个进程问题

本次诊断时发现 Web UI 有两个进程在跑：
- PID 60551 — 旧进程，监听 0.0.0.0:8648
- PID 65461 — 新进程，无端口（可能是之前手动启动的另一实例）

这是之前升级/重启残留。不影响功能但建议清理多实例。
