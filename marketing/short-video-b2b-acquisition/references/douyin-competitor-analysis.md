# 抖音竞品分析工作流 — 技术实现细节

⚠️ **重要更新（2026-05-08）：CDP 方案已修复。** 以下为完整工作流程，包含所有坑点和修复方案。

---

## 方案选择（按优先级排序）

| 优先级 | 方案 | 适用场景 |
|--------|------|---------|
| ⭐ **首选** | **腾哥手动提供信息** | 任何时候都可用，零技术风险 |
| ⭐ **第二** | **CDP 连 Windows Chrome（带 `--user-data-dir`）** | 需要自动化采集抖音数据时，用户需配合操作 |
| ⭐ **第三** | **Scrapling StealthyFetcher** | 采集非登录公开页面（抖音首页/搜索页无登录内容） |
| ❌ 不推荐 | 无头浏览器直连抖音 | 100% 被验证码拦截 |

---

## CDP 连接 Windows Chrome（实测可行方案）

**核心理念：`--user-data-dir` 不是问题，而是解决方案。** 使用全新用户数据目录可以绕过 profile 锁文件问题，100% 确保 Chrome 监听调试端口。代价是用户需要在新窗口中重新登录抖音。

### 完整启动流程（从 WSL 执行）

```powershell
# 步骤 1：杀光所有 Chrome 进程
powershell.exe -Command "Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force"
Start-Sleep 3

# 步骤 2：清理可能的旧端口转发（避免冲突）
netsh.exe interface portproxy delete v4tov4 listenport=9222 listenaddress=0.0.0.0

# 步骤 3：用全新用户数据目录启动 Chrome
powershell.exe -Command "Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\temp\chrome-debug'"
Start-Sleep 5

# 步骤 4：设置端口转发（Chrome 绑定 127.0.0.1，需要转发到外部）
netsh.exe interface portproxy add v4tov4 listenport=9222 listenaddress=0.0.0.0 connectport=9222 connectaddress=127.0.0.1

# 步骤 5：验证连接
curl -s http://172.28.32.1:9222/json/version
# 期望输出：{"Browser": "Chrome/147.0.7727.138", ...}
```

### 验证结果

```
Browser: Chrome/147.0.7727.138
Protocol-Version: 1.3
WebSocket: ws://172.28.32.1:9222/devtools/browser/<uuid>
```

### 配置 Hermes CDP

```bash
hermes config set browser.cdp_url "ws://172.28.32.1:9222/devtools/browser/<uuid>"
```

### CDP 工具使用

连接后可通过 `browser_cdp` 工具直接操控用户 Chrome 浏览器：
- 列出所有标签页
- 导航到指定 URL
- 执行 JavaScript
- 获取页面截图/Snapshot

---

## ⚠️ 已知坑点完整排查

### 坑 1：Portproxy 与 Chrome 绑定冲突

**现象：** `netstat -ano | grep 9222` 显示 LISTENING，PID 是 svchost 而非 Chrome。

**原因：** netsh portproxy 规则（svchost 进程）占用了 0.0.0.0:9222，Chrome 无法绑定。

**修复：**
```powershell
# 先删除转发规则
netsh interface portproxy delete v4tov4 listenport=9222 listenaddress=0.0.0.0
# 再启动 Chrome
Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\temp\chrome-debug'
# Chrome 启动绑定 127.0.0.1:9222 后，再添加转发
netsh interface portproxy add v4tov4 listenport=9222 listenaddress=0.0.0.0 connectport=9222 connectaddress=127.0.0.1
```

**关键顺序：** 先删除转发 → 启动 Chrome → 再添加转发。

### 坑 2：Chrome 不监听调试端口

**现象：** Chrome 进程在运行，但 netstat 无 9222 LISTENING。

**根因（已确认）：** 不用 `--user-data-dir` 启动 Chrome 时，Chrome 会尝试复用已有 profile 目录的锁文件。如果之前暴力杀过 Chrome，锁文件残留导致 `--remote-debugging-port` 参数被忽略。

**唯一可靠解决方案：** 使用全新的用户数据目录。

```powershell
# ✅ 有效
Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\temp\chrome-debug'

# ❌ 无效（之前反复验证始终不通）
Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222'
```

**代价：** 新 profile → 用户未登录任何网站 → 需要用户在新窗口中手动登录抖音。

### 坑 3：Chrome 进程杀不干净

Chrome 有后台自愈机制，一次杀可能不够：

```powershell
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 3
# 检查
Get-Process chrome -ErrorAction SilentlyContinue | Format-Table Id
# 还有 → 再杀
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 5
```

### 坑 4：netsh 命令从 WSL bash 执行失败

**现象：** `系统找不到指定的文件`

**原因：** WSL bash 对特殊字符（如 `%`、`|`）的转义问题。

**修复：** 用 PowerShell 或 cmd.exe 执行：
```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "netsh interface portproxy add v4tov4 listenport=9222 listenaddress=0.0.0.0 connectport=9222 connectaddress=127.0.0.1"
```

或直接调用 netsh.exe：
```bash
/mnt/c/Windows/System32/netsh.exe interface portproxy add v4tov4 listenport=9222 listenaddress=0.0.0.0 connectport=9222 connectaddress=127.0.0.1
```

### 坑 5：从 WSL 调用 PowerShell 启动 Chrome

**✅ 有效的方式：**
```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\temp\chrome-debug'"
```

**❌ 无效的方式：**
```bash
# cmd /c start /B 从 WSL调用可能卡住
/mnt/c/Windows/System32/cmd.exe /c "start /B \"\" \"C:\Program Files\Google\Chrome\Application\chrome.exe\" --remote-debugging-port=9222"
```

### 坑 6：TIME_WAIT 洪水

每次失败的 curl 请求都会留下 TIME_WAIT 记录。不影响功能但会让 netstat 输出变得巨大。在排查时用 `grep LISTEN` 过滤：
```bash
netstat -ano | grep 9222 | grep LISTEN
```

### 坑 7：从 WSL 无法直接通过 127.0.0.1 访问 Windows 端口

WSL2 的 `127.0.0.1` 是 WSL 自己的回环地址，不是 Windows 的。必须通过 Windows 宿主机 IP（默认网关 IP）访问。

```bash
# 获取 Windows 宿主机 IP
grep nameserver /etc/resolv.conf | awk '{print $2}'
# 输出类似：172.28.32.1
```

然后用 `http://172.28.32.1:9222` 访问。

### 坑 8：Chrome 提取的 webSocketDebuggerUrl 需要 IP 替换

从 `/json/version` 返回的 `webSocketDebuggerUrl` 中 IP 可能是外网 IP。在 WSL 中需要将其替换为 Windows 宿主机 IP 以建立 WebSocket 连接。

---

## 端口转发与防火墙（一次性设置）

以下操作只需在首次设置时运行一次。后续只需启动 Chrome + 添加转发规则即可。

### 端口转发（netsh）

```powershell
# 添加
netsh interface portproxy add v4tov4 listenport=9222 listenaddress=0.0.0.0 connectport=9222 connectaddress=127.0.0.1

# 查看
netsh interface portproxy show all

# 删除（需要清理时）
netsh interface portproxy delete v4tov4 listenport=9222 listenaddress=0.0.0.0
```

### 防火墙规则

```powershell
New-NetFirewallRule -DisplayName 'Chrome Remote Debug' -Direction Inbound -Protocol TCP -LocalPort 9222 -Action Allow

# 查看
netsh advfirewall firewall show rule name="Chrome Remote Debug"

# 删除
netsh advfirewall firewall delete rule name="Chrome Remote Debug"
```

### 检查端口归属

`netstat` 显示的 LISTENING PID 可能是 `svchost`（portproxy 服务），不是 Chrome。必须用 `tasklist` 确认：

```bash
/mnt/c/Windows/System32/tasklist.exe /FI "PID eq <PID>" 2>/dev/null
```

---

## 故障快速诊断清单

| 现象 | 可能原因 | 解决办法 |
|------|---------|---------|
| curl 返回 `Connection refused` | Chrome 没启动 / 端口错误 | 确认 Chrome 进程存在 |
| curl 返回 `Empty reply from server` | Portproxy 冲突 | 先删转发再添加 |
| netstat 无 LISTENING 只有 TIME_WAIT | Chrome 没带 debug 端口启动 | 使用 `--user-data-dir` 强制新配置 |
| LISTENING PID 是 svchost | Portproxy 在监听 | tasklist 确认，Chrome 可能没绑上 |
| Websocket 连不上 | IP 地址需替换 | 用 127.0.0.1 替换 webSocketDebuggerUrl 中的 IP |

---

## 终极建议

✅ **CDP 方案现在可行的条件：**
1. 使用 `--user-data-dir` 创建全新 Chrome profile
2. 用户在新窗口中手动登录抖音
3. portproxy 转发 + 防火墙已设置
4. 先删转发 → 启 Chrome → 再加转发的顺序不能错

❌ **以下情况仍不适合用 CDP：**
- 用户无法在新 Chrome 窗口中登录抖音（没手机收验证码）
- 环境已从 WSL2 切换到其他平台
- 只需要静态页面采集（此时用 Scrapling 更快）



---

---

## 主动搜索流程（用户无具体竞品名时使用）

当腾哥不知道具体竞品账号名，只知道内容方向时使用此流程。

### 搜索策略

**三个方向并行搜索（2026-05-09 实战验证）：**
1. **工厂实力类** — 搜「全屋定制工厂」「源头工厂」「全屋定制代工」
2. **门店获客引流类** — 搜「全屋定制门店获客引流」「全屋定制获客方法」「全屋定制工厂获客」
3. **门店销售技巧类** — 搜「全屋定制门店销售技巧」「全屋定制签单技巧」「全屋定制逼单话术」

### 搜索步骤（CDP 浏览器模式）

```
步骤 1：确认用户已登录抖音（在 Chrome 中手动登录）
步骤 2：关键词搜索 → 切换到「视频」tab → 采集近期视频结果
步骤 3：关键词搜索 → 切换到「用户」tab → 采集竞品账号信息
步骤 4：综合两个维度的结果，挑选 3-5 个高价值竞品
步骤 5：用「用户」tab 进入竞品主页，采集作品列表
```

### 数据采集字段

**账号级：**
- 账号名、抖音号
- 粉丝数、获赞数
- 简介（判断定位）
- 是否认证/企业号

**视频级（搜索结果页提取）：**
- 视频标题/文案片段
- 播放量/点赞数（抖音搜索页会显示）
- 发布时间（几周前/几月前）
- 视频时长

### 结果呈现

采集完成后按以下格式整理给腾哥筛选：

```
方向一：XXXX类
| 账号 | 粉丝 | 获赞 | 近期爆款 | 播放 |
|------|------|------|---------|:----:|
| @XXX | XX万 | XX万 | 「标题」⏰1周前 | 338 |
```

---

## 执行流程（手动模式 — 推荐）

### 标准流程

```
腾哥提供竞品账号名（3-5个）
  → 腾哥截图/粘贴竞品爆款视频信息
  → 小何分析爆款结构 + 提取可复用模板
  → 腾哥确认方向 → 小何输出二次创作脚本
```

### 腾哥需要提供的信息（越多分析越准）

**账号级：**
- 竞品抖音号/名称
- 竞品粉丝数、作品数（截图）
- 竞品账号定位描述

**视频级（每账号 3-5 条爆款）：**
- 视频标题/文案（手动粘贴或截图OCR）
- 播放量、点赞数
- 视频时长、发布时间
- 视频链接（分享链接，小何可以尝试直接解析）

### 小何的产出格式

```markdown
【竞品账号】洛阳XX全屋定制
【爆款视频1】标题：xxx
【爆款因子】利益钩子 + 焦虑触发 + 工厂实拍画面
【可复用模板】开头：利益钩子 → 中间：工厂实景 + 数据佐证 → 结尾：引导私信
【二次创作方案】
  - 差异化方向：XX（与竞品不同的切入角度）
  - 标题：XXX
  - 文案框架：XXX（可直接复制填内容）
  - 拍摄建议：XXX
```

---

## 二次创作脚本产出流程

```
原始视频文案提取
  → 拆解爆款结构（钩子/正文/引导）
  → 差异化改编（视角/深度/案例/本地化）
  → 产出腾哥版脚本
```

### 二次创作原则
1. **不同角度同一话题** — 同一个行业痛点，换角度重新解读
2. **升级版表达** — 竞品说得浅的挖深；竞品讲得泛的给具体案例
3. **反向切入** — 竞品说 A 好，你可以说 A 的坑在哪
4. **本地化落地** — 竞品讲理论，你结合自家工厂/案例落地
5. **格式改编** — 口播改工厂实拍+画外音；剧情改干货讲解
