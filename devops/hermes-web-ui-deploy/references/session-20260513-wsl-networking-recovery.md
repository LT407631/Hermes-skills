# 2026-05-13 会话：Web UI 网络恢复 + GatewayManager 配置修复

## 场景

腾哥在 Web UI 终端内执行了以下命令：
```
rm -f /home/lt-pc/.hermes/profiles/dev/gateway.lock /home/lt-pc/.hermes/profiles/op/gateway.lock
kill -9 $(ps aux | grep -E 'profile.*dev.*gateway|profile.*op.*gateway' | grep -v grep | awk '{print $2}')
```

导致 Web UI 页面显示「未连接」、所有对话无响应。

## 诊断路径

### 阶段 1：确认服务存活

```bash
# Gateway 健康检查 → 返回 ok
curl -s http://127.0.0.1:8642/health

# Gateway 进程存在（自动重启了）
ps aux | grep 'hermes.*gateway' | grep -v grep

# Web UI 服务运行
ps aux | grep 'hermes-web-ui' | grep -v grep

# 端口监听
ss -tlnp | grep -E '8642|8648'
```

所有服务都活着，但 Web UI 代理不通。

### 阶段 2：发现 root cause

```bash
# Web UI 代理路径测试 → 返回 Proxy error: fetch failed
curl -s -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)" http://127.0.0.1:8648/v1/models

# 直接测 gateway → 正常返回模型列表
curl -s http://127.0.0.1:8642/v1/models -H "Authorization: Bearer API_SERVER_KEY"

# 检查 config.yaml → 发现 api_server.extra 被改成 host=0.0.0.0, port=8652
grep -A6 "api_server:" ~/.hermes/config.yaml
```

### 阶段 3：修复

```bash
# 修正 config.yaml 的 api_server.extra:
#   port: 8642
#   host: 127.0.0.1
#   key: lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE

# 清理 dev/op gateway 的锁和 PID 文件（用 Python，避免 rm 超时）
python3 -c "
import os
for f in ['dev/gateway.lock','dev/gateway.pid','op/gateway.lock','op/gateway.pid']:
    p = os.path.expanduser(f'~/.hermes/profiles/{f}')
    if os.path.exists(p): os.remove(p)
"

# 修正 dev/op 配置端口（dev: 8653, op: 8654）

# 重启 Web UI
kill $(ps aux | grep 'hermes-web-ui' | grep -v grep | awk '{print $2}')
BIND_HOST=127.0.0.1 /home/lt-pc/.hermes/node-v23/bin/node /home/lt-pc/.hermes/node-v23/lib/node_modules/hermes-web-ui/dist/server/index.js > ~/.hermes-web-ui/server.log 2>&1 &
```

### 阶段 4：WSL → Windows 网络通路

腾哥要求在 Windows 浏览器用 `127.0.0.1:8648` 访问 WSL 内的 Web UI（**必须用 127.0.0.1，不能用 0.0.0.0**）。

#### 4a. WSL 内 socat 转发
```bash
WSL_IP=$(hostname -I | awk '{print $1}')
socat TCP4-LISTEN:8648,bind=$WSL_IP,fork,reuseaddr TCP4:127.0.0.1:8648 &
```

#### 4b. Windows 端口转发（从 WSL 内执行）
```bash
powershell.exe -Command "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=8648 connectaddress=$WSL_IP connectport=8648"
```

#### 4c. 验证
```bash
# 从 WSL 内测试端口转发通路
powershell.exe -Command "netsh interface portproxy show v4tov4"
# 应有: 127.0.0.1:8648 → <WSL_IP>:8648

# 从 WSL 测试 Web UI 代理
curl -s -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)" http://127.0.0.1:8648/v1/models
# 应返回模型列表
```

## 知识点

| 项目 | 值 |
|------|-----|
| Web UI Token 路径 | `~/.hermes-web-ui/.token` |
| Web UI 登录锁 | `~/.hermes-web-ui/.login-lock.json`（删=解限流） |
| Gateway API Key（从 .env 读取） | `API_SERVER_KEY=lU5zJYjpGU8H8ecY78Inh8w7F2E0TobOsXrMVfLefeE` |
| 默认 gateway port | 8642 |
| dev profile port | 8653 |
| op profile port | 8654 |
| BIND_HOST 环境变量 | 控制 Web UI 监听地址，默认 0.0.0.0 |
| 腾哥的 0.0.0.0 立场 | 明确排斥，永远不要推荐或使用 |

## 关键坑汇总

1. **GatewayManager 会在 detectAllOnStartup() 时篡改 config.yaml** → 修复后必须重启 Web UI
2. **GatewayManager 对不同 profile 的端口分配可能不生效** → gateway 实际端口与配置不符→健康检查超时
3. **rm 命令在 WSL 特定目录下可能超时** → 用 Python os.remove() 替代
4. **WSL 127.0.0.1 与 Windows 127.0.0.1 不同** → 必须建 portproxy 或 socat 转发
