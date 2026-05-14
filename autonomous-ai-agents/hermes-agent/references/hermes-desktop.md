# Hermes Desktop — GUI 桌面客户端

## 概述

Hermes Desktop 是第三方开发者 [fathah](https://github.com/fathah/hermes-desktop) 基于 Electron 构建的 Hermes Agent 桌面 GUI。**不是 Nous Research 官方出品。** MIT 开源免费。

## 技术栈

- Electron 39 — 跨平台桌面壳
- React 19 — UI 框架
- TypeScript 5.9 — 类型安全
- Tailwind CSS 4 — 样式
- Vite 7 + electron-vite — 构建工具
- i18next — 国际化框架

## 与 Web UI 功能对比

| 功能 | Hermes Desktop | Web UI (v0.5.17) |
|------|---------------|-----------------|
| 模型选择下拉框 | ✅ 内置 | ❌ 无，需微信发 /model |
| 斜杠命令面板 | ✅ 22个命令 | ❌ 不支持 |
| 推理强度设置 | ✅ 低/中/高 | ❌ 不支持 |
| Token 用量明细 | ✅ 每会话统计 | ❌ 无 |
| 工具调用可视化 | ✅ 进度条显示 | ✅ 有(简要) |
| 安装配置图形化 | ✅ 有安装向导 | ❌ 需手动配 yaml |
| 会话管理 | ✅ 列表+搜索 | ✅ 有 |
| 中文界面 | ✅ 内置 zh-CN | ❌ 英文 |
| 跨平台 | Win/Mac/Linux | 浏览器即可 |
| 启动速度 | 快(独立窗口) | 依赖浏览器 |

## 中文支持

项目已内置完整中文翻译。`src/shared/i18n/locales/zh-CN/` 目录包含 20 个翻译文件（common、chat、navigation、settings、tools、sessions、models、providers 等），均已完成真实翻译，非空壳。

### 如何切换为中文

**方式一（安装后设置里切）：** 下载安装后，大概率在 Settings 中有 Language 选项直接选中文。

**方式二（改默认配置）：** 如果默认英文不想手动切，修改源码：
```
src/shared/i18n/config.ts
```
将 `DEFAULT_ACTIVE_LOCALE: AppLocale = "en"` 改为 `"zh-CN"`，然后重新构建。

### 语言配置参数

在 `src/shared/i18n/config.ts`：
- `SOURCE_LOCALE: "en"` — 源语言
- `FALLBACK_LOCALE: "en"` — 回退语言
- `DEFAULT_ACTIVE_LOCALE: "en"` — 默认显示语言
- `APP_LOCALES: ["en", "es", "pt-BR", "zh-CN"]` — 支持的语言列表

## 远程连接模式（WSL2 核心配置）

Hermes Desktop 支持三种连接模式：Local（本地运行 Hermes CLI）、Remote（远程连接 WSL / 服务器的 Hermes Gateway API）、SSH（SSH 隧道）。

**腾哥的典型场景：** Windows Desktop → WSL2 的 Hermes Gateway API。

### 前置检查：WSL2 的 Gateway 监听地址

Hermes Gateway 的 API Server 默认只绑 `127.0.0.1:8642`（WSL 内部），Windows 连不上。需要先确认：

```bash
ss -tlnp | grep 8642
```

如果显示 `127.0.0.1:8642` 而非 `0.0.0.0:8642`，Windows 无法直连。

### 方案 A：socat 转发（推荐，不改源码不重启网关）

socat 在 WSL 内部监听 WSL 的虚拟 IP + 8642 端口，转发到网关的 `127.0.0.1:8642`：

```bash
# 获取 WSL 虚拟 IP
hostname -I
# 假设输出 172.28.40.234

# socat 只绑 WSL IP（不绑 127.0.0.1，不与网关冲突）
socat TCP4-LISTEN:8642,bind=172.28.40.234,fork,reuseaddr TCP4:127.0.0.1:8642 &
```

**⚠️ 关键坑：**
- 必须用 `TCP4` 而不是 `TCP`，否则 socat 默认绑 IPv6 导致端口冲突
- 必须 `bind=172.28.40.234`（WSL 的虚拟 IP），而不是 `bind=0.0.0.0`，否则和网关的 `127.0.0.1:8642` 冲突
- socat 进程会后台运行，WSL 关机后失效

**验证转发成功（从 Windows 浏览器打开）：**
```
http://172.28.40.234:8642/health
```
返回 `{"status": "ok", "platform": "hermes-agent"}` 表示通路已通。

### 方案 B：改 Gateway 监听地址（永久方案）

修改源码默认值，然后重启网关：

```bash
# 改 DEFAULT_HOST
sed -i 's/DEFAULT_HOST = "127.0.0.1"/DEFAULT_HOST = "0.0.0.0"/' ~/.hermes/hermes-agent/gateway/platforms/api_server.py

# 清 Python 缓存（防止旧 .pyc 残留导致改动不生效）
find ~/.hermes/hermes-agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~/.hermes/hermes-agent -name "*.pyc" -delete 2>/dev/null

# 停 systemd 服务（否则自动拉回旧进程）
sudo systemctl stop hermes-gateway.service 2>/dev/null
sudo systemctl disable hermes-gateway.service 2>/dev/null

# 杀光旧进程
kill -9 $(ps aux | grep -E 'gateway|hermes.*gateway|python.*8642' | grep -v grep | awk '{print $2}') 2>/dev/null

# 启动
hermes gateway run
```

**验证绑定生效：**
```bash
ss -tlnp | grep 8642
# 应显示 0.0.0.0:8642 而非 127.0.0.1:8642
```

### Hermes Desktop 设置步骤（Remote 模式）

在 Windows Hermes Desktop 内：

1. 打开 **Settings** → 找到 **Connection** 区域
2. 连接模式切换到 **Remote**
3. **Remote URL** 填：`http://<WSL_IP>:8642`（如 `http://172.28.40.234:8642`）
4. **API Key** 填：config.yaml 里 gateway.api_key 的值
5. 点击 **Test Connection** — 5 秒内应显示 "Connected successfully!"
6. 点击 **Save** 保存配置

**关键认知：** 填上 URL 不会自动连接。必须点击「Test Connection」按钮进行连接测试，再点「Save」保存配置。这两步缺一不可。

### 连接测试源码逻辑

Desktop 的 `testRemoteConnection` 函数（位于 `src/main/hermes.ts`）：

```typescript
testRemoteConnection(url: string, apiKey?: string): Promise<boolean> {
  const target = `${url.replace(/\/+$/, "")}/health`;
  const mod = target.startsWith("https") ? https : http;
  const headers: Record<string, string> = {};
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
  const req = mod.request(target, { method: "GET", timeout: 5000, headers },
    (res) => resolve(res.statusCode === 200));
}
```

即：GET `{URL}/health`，5 秒超时，携带 Bearer token，状态码 200 即视为连接成功。

### 常见故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 浏览器能打开 `/health`，但 Desktop 连不上 | Electron 的网络上下文不同（如公司代理/Win防火墙） | 检查 Windows 防火墙、代理设置；尝试在 Desktop 的 Network Settings 中配置 HTTP Proxy |
| Desktop 提示 "Could not reach server" | URL 少了 `http://` 前缀、IP 不对、端口不对 | 确认 URL 格式 `http://172.28.40.234:8642`（必须有 `http://`） |
| Desktop 显示 "Connected successfully!" 但聊天窗口空白 | 网关版本与 Desktop 不兼容 | 升级网关或降低 Desktop 版本 |
| 填上 URL 没反应 | 没有点击 Test Connection | URL 输入框不会自动触发连接测试，要手动点 Test 按钮 |
| WSL 重启后连不上 | socat 进程丢失 | 重新执行 socat 转发命令 |
| socat 启动报 "address already in use" | socat 默认绑 IPv6 冲突 | 用 `TCP4` 而非 `TCP`，或换端口（如 8643） |

## 下载安装

最新版本 v0.3.6 (2026-05-12 发布)。

### Windows 用户

直接下载 exe 安装包：
```
https://github.com/fathah/hermes-desktop/releases/download/v0.3.6/hermes-desktop-0.3.6-setup.exe
```

### 其他平台

- Mac (Intel): `Hermes.Agent-0.3.6-mac.zip`
- Mac (Apple Silicon): `Hermes.Agent-0.3.6-arm64-mac.zip`
- Linux: `.AppImage` / `.rpm` / `.deb`

## 从源码构建（如需改语言/定制）

```bash
git clone https://github.com/fathah/hermes-desktop.git
cd hermes-desktop
npm install
# 如果需要中文默认语言，先改 src/shared/i18n/config.ts
npm run build
```

## 关键路径

- 源码: `src/shared/i18n/locales/zh-CN/` — 中文翻译文件
- 配置: `src/shared/i18n/config.ts` — 语言选择
- 电子主进程: `src/main/hermes.ts` — testRemoteConnection 函数
- 设置页面: `src/renderer/src/screens/Settings/Settings.tsx` — Remote 模式 UI

## 参考链接

- GitHub: https://github.com/fathah/hermes-desktop
- 介绍文章: https://www.hongkiat.com/blog/hermes-desktop-gui-for-hermes-agent/
- Hermes Atlas: https://hermesatlas.com/projects/fathah/hermes-desktop
