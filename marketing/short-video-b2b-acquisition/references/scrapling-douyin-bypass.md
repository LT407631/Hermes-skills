# Scrapling 抖音反爬绕过方案

## 概述

[Scrapling](https://github.com/D4Vinci/Scrapling) 是一个 Web 爬虫框架，支持隐匿浏览器自动化、Cloudflare 绕过。经实测，其 **StealthyFetcher** 可以绕过抖音的 headless 浏览器检测（返回 200 状态码 + 真实页面内容），这是目前唯一成功的自动化方案。

## 安装

```bash
pip install "scrapling[all]"
scrapling install       # 下载 Playwright Chromium
```

**注意：** `scrapling install` 需要 sudo 权限（安装系统依赖），且下载 Chromium 耗时较长（~110MB）。

## CLI 快速使用

### 获取抖音首页

```bash
scrapling extract stealthy-fetch 'https://www.douyin.com' output.html --block-webrtc --hide-canvas
```

结果：返回 200，成功获取真实首页 HTML（非验证码拦截页）。HTML 中包含部分预渲染内容（约 300KB）。

### 搜索账号

```bash
scrapling extract stealthy-fetch 'https://www.douyin.com/search/洛阳鑫德?type=user' output.html --block-webrtc --hide-canvas
```

结果：返回 200，但搜索结果为 **SPA 动态加载** + **加密 JS 渲染**。

**关键发现（2026-05-08 实测）：**
- HTML 约 242KB，但几乎全部是加密/混淆 JS 代码
- 搜索 keyword 以路由参数形式传入（`"keyword":"洛阳鑫德"`），但实际搜索结果不包含在 HTML 中
- 页面响应中明确返回了状态信息：
  - `isLogin: false` — 非登录态
  - `statusCode: 8` — 抖音反爬拦截码（非 200 正常）
- 没有任何用户数据、视频数据预埋在 HTML 中
- `<body>` 内几乎是纯 JS 代码（MutationObserver 监听 + 加密字节码解析）

## 抖音反爬技术栈（实测推断）

| 技术 | 效果 |
|------|------|
| WebDriver 检测 | ✅ Scrapling StealthyFetcher 已绕过 |
| 无头浏览器指纹 | ✅ Scrapling StealthyFetcher 已绕过 |
| JS 动态渲染 (SPA) | ❌ StealthyFetcher 无法完整执行渲染 |
| 服务端加密渲染 | ❌ 核心数据不进入 HTML |
| 复用请求检测 | ❌ 非登录态返回 statusCode: 8 |
| 验证码/JS Challenge | ✅ StealthyFetcher 绕过（首页返回 200） |

## 局限

1. **SPA JS 渲染不完整** — 抖音搜索结果由客户端 JS 动态加载 API 后渲染，StealthyFetcher 的 `network_idle` 和 `wait_selector` 策略在 WSL 环境下经常超时
2. **无法获取登录态数据** — Scrapling 运行在 WSL 的无头环境中，没有腾哥的抖音登录信息
3. **超时问题** — Python API 版（StealthyFetcher.fetch + network_idle）容易超时，CLI 版（`scrapling extract stealthy-fetch`）更稳定
4. **适用场景有限** — 只能获取首页/非登录公开页面，无法做竞品视频详情分析
5. **搜索页面 200 但无数据** — 实测 CLI 版获取抖音搜索页（如 `douyin.com/search/洛阳鑫德?type=user`）返回 HTTP 200 + 298KB 内容，但页面体几乎全是加密 JS，无用户数据 JSON 嵌入。`isLogin:false` + `statusCode:8` 表明抖音识别到未登录状态，拒绝返回数据。
5. **超时问题** — Python API 版（StealthyFetcher.fetch + network_idle）容易超时，CLI 版（`scrapling extract stealthy-fetch`）更稳定
6. **适用场景有限** — 只能获取首页/非登录公开页面，无法做竞品视频详情分析

## 最佳实践

### 优先级策略

| 优先级 | 方案 | 适用场景 |
|--------|------|---------|
| ⭐ 首选 | **腾哥手动提供信息** | 任何时候都可用，零技术风险 |
| ⭐ 第二 | **Scrapling CLI 版** | 需要采集抖音首页/搜索页非登录内容（但数据有限） |
| ❌ 放弃 | CDP/无头浏览器 | 已被反复验证失败，循环回避 |

### 当 Scrapling 返回 `isLogin: false` 时有用的信号

即使拿不到数据，以下返回信息仍有价值：
- 搜索是否被重定向（判断账号是否违规/被封）
- 页面响应状态码（判断反爬强度变化）
- keyword 参数是否正确传递（确认路由无问题）

### 核心原则（循环回避）

**如果同一个自动化方案失败 2 次，必须立刻完全切换方案。** 不纠缠。抖音反爬是持续升级的对抗赛，自动化采集作为 B 端引流工具的性价比很低——手动提供信息 + 内容创作方案才是主战场。
