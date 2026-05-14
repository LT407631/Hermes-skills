# Hermes Web UI 部署记录 - 2026-05-12

## 问题记录

### 问题1：npm install 超时
- **原因**：npmjs.org 国内直连慢
- **解决**：`npm config set registry https://registry.npmmirror.com`

### 问题2：ENOTEMPTY 错误
- **原因**：上次安装残留的目录存在
- **解决**：清理残留后重装

### 问题3：命令找不到
- **原因**：npm 全局 bin 路径未加入 PATH
- **解决**：加入 PATH 或使用全路径

### 问题4：Token 变了
- **原因**：服务重启后重新生成 Token
- **解决**：Settings 设用户名密码，之后不再依赖 Token

### 问题5：旧版 Node 启动失败
- **原因**：Node < 23 需要 experimental 标志
- **解决**：升级到 v23+

### 问题6：node-pty 编译超时
- **原因**：`node-pty` 需要编译原生 C 代码，`node-gyp rebuild` 耗时极长
- **解决**：安装 build-essential 后重试

---

## 2026-05-12 实战踩坑（本次）

### 坑1：多 Node 版本共存时 npm -g 路径混乱
`npm root -g` 显示的是 npm 自己的全局路径，而非 `node --version` 显示的版本。两个 Node 版本的 npm 各自维护独立的全局包目录，互不干扰。
**判断方法**：
```bash
# 看 Web UI 二进制使用哪个 Node
head -1 /home/lt-pc/.hermes/node/bin/hermes-web-ui
# 输出 "#!/usr/bin/env node" → 使用 PATH 中第一个 node
ps aux | grep hermes-web | grep -v grep
# 看运行中进程的 Node 路径
```

### 坑2：Web UI 启动脚本的 process.execPath 锁死 Node 版本
启动脚本里：
```javascript
const child = spawn(process.execPath, [serverEntry], ...)
```
它用 `process.execPath` 启动子进程，无法通过外部变量切换 Node 版本。
**解决**：在目标 Node 版本的全局路径下全新 `npm install -g hermes-web-ui`，不要用旧版本残留。

### 坑3：编译 node-pty 被终端超时中断
`npm install -g` 装 v23 时编译 `node-pty` 需要超过 60 秒，导致 `timeout=60` 的终端调用被中断。
**解决**：提前安装 build-essential，`timeout` 设 300+。

### 坑4：旧进程残留导致新服务启动失败
`hermes-web-ui is already running (PID: xxx)` — 旧 Web UI 进程还活着。
**解决**：先用 `hermes-web-ui stop` 停掉旧服务，再启动新的。

### 坑5：Web UI 不支持在界面内发送消息到微信/平台
Web UI 是**历史记录查看器 + 管理控制台**，不是消息发送入口。所有消息发送走各自平台通道。这与 OpenClaw 的 Web UI 不同，OpenClaw 支持双向桥接，Hermes Web UI 目前做不到在 Web UI 内回复微信。
