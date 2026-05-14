# OpenClaw 互操作尝试记录

> 日期：2026-05-14
> 场景：腾哥问能否从 Hermes 控制 OpenClaw 干活

## 环境

- OpenClaw: 2026.5.6 (npm 全局安装于 Windows)
- Hermes: 运行于 WSL (Ubuntu)
- 操作系统: Windows 11 (主机) + WSL2 (Ubuntu)

## 能做什么

### 1. OpenClaw gateway 启动

```bash
# 从 WSL 通过 PowerShell 启动 Windows 上的 OpenClaw gateway
powershell.exe -Command "Start-Process -NoNewWindow -FilePath 'cmd.exe' -ArgumentList '/c openclaw gateway run'"
```

### 2. 端口转发（WSL → Windows）

OpenClaw gateway 绑定 Windows 127.0.0.1（loopback），从 WSL 无法直接访问。

```bash
# 创建 portproxy 从 Windows 主机 IP 转发到 Windows 127.0.0.1
powershell.exe -Command "netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_IP> listenport=18789 connectaddress=127.0.0.1 connectport=18789"

# 健康检查（从 WSL 访问 Windows IP）
curl -s http://<WINDOWS_IP>:18789/health
# 返回: {"ok":true,"status":"live"}
```

### 3. 发送消息给 OpenClaw agent

```bash
# 方法：通过 PowerShell 运行 OpenClaw CLI
powershell.exe -Command "openclaw agent -m '消息内容' --agent main --json 2>&1"
```

### 4. 获取回复

回复在 JSON 的 `payloads[].text` 字段中，支持多段回复。

## 局限性

| 问题 | 说明 |
|------|------|
| ⏱ 慢 | 每次对话需 60-120 秒（走 DeepSeek API） |
| 🔧 笨重 | 需写 ps1 脚本 → 执行 → 读文件 → 解析 JSON |
| 🧹 编码乱 | 中文返回有编码乱码问题 |
| 💸 双倍花钱 | 同时为 Hermes + OpenClaw 付 API 费 |
| ❌ 非原生 | 不是 Hermes 原生能力，是绕道控制 |

## 结论

OpenClaw 能通信但不推荐。delegate_task 或其他 Hermes 原生方案更好。
