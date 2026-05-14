---
name: multi-agent-team-orchestration
description: "Hermes 多智能体团队编排：Profile 创建/隔离、灵魂设定、知识库分区、总监调度流程、协作协议、死循环防治"
version: 2.1.0
author: 小何 + 腾哥
metadata:
  domain: software-development
  tags: [Hermes, Multi-Agent, Profile, SOUL.md, TeamOrchestration, Director, Collaboration, DingTalk]
---

# Hermes 多智能体团队编排指南

> 适用于：腾哥团队的三智能体架构（小何总监 + dev代码 + me美工 + op运营）

## 概述

多智能体协作不是把多个 Agent 扔到一个房间就完了。真正的协作需要：
1. **物理隔离** — 每个 Agent 有自己的进程、配置、记忆
2. **灵魂设定** — 每个 Agent 有清晰的边界和能力描述
3. **知识库分区** — 每个 Agent 有自己的工作文件夹
4. **调度协议** — 谁来派活、怎么派、怎么验收
5. **防循环机制** — Agent 之间互 @ 不陷入死循环

---

## 一、团队架构

```
腾哥（老板）
   │
小何（总监/调度/审核）
   ├── dev（全栈代码工程师，带基础美化能力）
   ├── me（UI美工设计师，精美化）
   └── op（短视频运营专员，继承小何原全部能力）
```

---

## 二、Profile 创建与隔离

### 创建 Profile

```bash
# 从 default 克隆（继承模型配置和 API key，记忆和 session 全新）
hermes profile create dev --clone
hermes profile create me --clone
hermes profile create op --clone
```

### 隔离层级

Hermes Profile 是**进程级隔离**：
- 每个 profile 有独立的 `config.yaml`、`.env`、`SOUL.md`
- 独立的 memory 和 sessions
- 独立的 gateway 进程（端口独立）
- **一个挂了下线，不影响其他**

### 端口配置陷阱

各 profile 的 gateway 端口在 `config.yaml` 中：
```yaml
platforms:
  api_server:
    extra:
      port: 8653        # dev 用 8653, me 用 8643, op 用 8654
      host: 127.0.0.1
      key: <api-key>
```

⚠️ **GatewayManager 会篡改端口**：Web UI 重启时可能调用 `resolvePort()` 重分配端口。手动启动 gateway 绕过：
```bash
HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace &
```

⚠️ **GatewayManager detectStatus 盲点**：即使 gateway 进程活着且在监听，如果实际端口 ≠ 配置端口（因 resolvePort 或 --replace 自主分配导致），Web UI 的健康检查会走错地址，显示「已停止」。诊断用 `ss -tlnp | grep hermes` 对比实际端口与配置端口，修复用改配置对齐实际端口（见 hermes-web-ui-deploy 技能 10c 节）。

### 全局 .env 跨 Profile 泄漏（高频坑）

**问题：** 全局 `~/.hermes/.env` 中的环境变量会被所有 profile 的 gateway 在启动时加载。即使某个 profile 的 `config.yaml` 中设置了 `weixin: enabled: false` 或 `dingtalk: enabled: false`，如果全局 `.env` 中有对应的 API 密钥（如 `WEIXIN_ACCOUNT_ID`、`WEIXIN_TOKEN` 等），gateway 仍会尝试连接。

**后果：** 多个 profile gateway 竞争同一个 bot token，导致「token 已被占用」错误和 gateway 反复崩溃。

**修复：**
```bash
# 检查全局 .env 中是否有跨 profile 泄漏的环境变量
grep -n "^WEIXIN_\|^DINGTALK_\|^WECOM_\|^TELEGRAM_\|^DISCORD_" ~/.hermes/.env

# 删除泄漏的行（保留 default profile 的配置在全局 env 中）
# 其他 profile 的配置应仅存在自己的 .env 文件中
sed -i '/^WEIXIN_/d' ~/.hermes/.env   # 示例：删除所有 WEIXIN 行
```

**最佳实践：**
- 全局 `~/.hermes/.env`：只放 default profile 需要的东西
- 每个 profile 的 `~/.hermes/profiles/<name>/.env`：放该 profile 专用的 API 密钥和平台配置
- 如果某个平台（如微信）只能由一个 profile 使用，确保其他 profile 的 `.env` 和 `config.yaml` 中都没有该平台的配置

---

## 三、灵魂设定（SOUL.md）

每个 profile 的 `SOUL.md` 必须包含：

### 模板结构

```markdown
# [角色名] 智能体人设

我名字叫 [角色名]，是腾哥团队的专业 [角色]。

## 身份定位

[一句话说明核心职责]

## 核心行为准则

[3-5条行为规则，用编号列表]

## 能力范围

[技术/业务能力清单]

## 协作规则

1. 接到小何（总监）的任务分配后直接开干
2. 接受小何的审核、质疑、退改
3. 交付后从小何的反馈中学习进化

## 知识库

我的知识库存放在 Obsidian 中：
```
Obsidian Vault/[角色名]/
├── soul.md    ← 我的人设（本文档）
├── ...        ← 分门别类的工作文件
```

## 对腾哥的称呼

叫「腾哥」。
```

### 角色边界设计

| 角色 | 能力边界 | 严禁越界 |
|------|---------|---------|
| dev | 全栈开发 + 基础UI美化 | ❌ 不做精细美化（交给me） |
| me | UI精美化、视觉设计 | ❌ 不修改功能逻辑 |
| op | 短视频运营全流程 | ❌ 不写代码、不做设计 |
| 小何 | 调度/审核/反馈，必要时顶替 | ❌ 不替他们干活 |

---

## 四、知识库分区（Obsidian）

### 推荐结构

```
Obsidian Vault/
├── 小何/           ← 总监工作记录、团队进度、反馈记录
├── dev/            ← 代码项目档案、技术方案
│   ├── soul.md
│   └── [项目文件夹]/
├── me/             ← 设计规范、配色方案、组件库
│   └── soul.md
└── op/             ← 自媒体运营全量素材
    ├── soul.md
    └── [运营文件夹]/
        ├── 01-成交体系/
        ├── 02-邀约话术/
        ├── 03-客户痛点/
        ├── 04-转化SOP/
        ├── 05-竞品分析/
        ├── 06-脚本库/
        └── ...
```

### 断线恢复机制

小何在 `小何/` 下记录每个智能体的工作进度。断线重连后：
1. 先读知识库恢复上下文
2. 查看各智能体工作记录
3. 继续调度

---

## 五、总监调度流程（小何）

### 严格工作流

```
腾哥下需求
   ↓
小何判断：谁来干？
   ↓
派遣给 dev / me / op
   ↓
跟踪进度 → 检测输出
   ↓
质疑 + 退改（如有问题）
   ↓
再次审核
   ↓
反馈给腾哥商量 → 合适 / 不合适
   ↓
无论合适与否，都要给智能体反馈，帮助其成长
```

### 核心原则

- **绝不替他们干活** — 小何是总监，不是代工
- **进度记录** — 在知识库里记录每个智能体的工作状态，防断线从头来
- **亲自上阵** — 仅当智能体死机/掉线/不可抗因素时
- **反馈闭环** — 无论结果是否采用，都要给反馈帮其进化
- **用知识库对齐风格** — 当智能体产出被否时，不只是给否定反馈。引导他去翻看知识库里腾哥亲写/亲改的示范文件，让他自己找感觉。路径通常是 `/mnt/d/Documents/Obsidian Vault/06-脚本库/` 或对应角色的知识库子目录。认知对齐比重复说教有效 10 倍。
- **op协同进化** — 在 op 的文案基础上开发「心灵感」，让 op 从中学习
- **多路思维（三策原则）** — 遇到技术障碍时，先自己列出至少 3 种完全不同的解决思路再找腾哥。不能说「这条路不通就停了」，要自己先想「能不能换条路」。比如 API 不记录会话 → 能不能直接写数据库？能不能通过 Web UI 新建一条会话往里注入？能不能换个有状态接口？列出可用选项后再汇报。

### ⚠️ 陷阱4：Bot 不在同一频道时的调度断点

**症状：** 腾哥让总监审核 op 的产出，但 op 在当前的聊天频道中不存在独立 bot（只有总监小何在线），也没有预先提交的成果文件。腾哥被迫转而要求总监「你发你整理好的」，直接绕过了「op 负责产出、总监只审核」的分工。

**根因：** 多智能体的「物理隔离」（每个 profile 独立进程+独立 bot 进群）尚未完全部署。当前真实状态是总监+op+dev+me 共用一个 Hermes 实例，不是4个独立 bot 在同群。

**总监的 fallback 处理流程：**

```mermaid
graph TD
    A[腾哥要求审核某智能体的产出] --> B{产出是否已提交}
    B -->|已提交| C[直接审核]
    B -->|未提交| D{该智能体在<br>当前频道是否存在}
    D -->|是独立bot| E[@ta 提交产出<br>等交付后审核]
    D -->|否/同一实例| F{知识库/归档中<br>是否有最近产出}
    F -->|有| G[调取过来给腾哥确认<br>→ 审核]
    F -->|没有| H[问腾哥：<br>「我还没收到op的提交，<br>你是说要我现在派活<br>还是之前有旧稿我翻一下？」]
```

**总监 fallback 话术模板：**

当腾哥要求审核某个智能体的产出但对方未提交时，用三段式澄清：

```
① 指出现状：腾哥，我这边没看到 [op/dev/me] 的提交
② 给出选择：
   a) 我记得 [之前的某次产出] → 是这个吗？
   b) 还是说你现在派活让我调度ta重新写？
   c) 还是你觉得我应该直接干？—— 那我提醒一下，我的角色是总监不代工
③ 等腾哥一句话，按他说的执行
```

注：以上流程仅适用于多智能体 bot 尚未全部部署到同一频道的过渡期。部署完成后（3个独立 bot 进群），恢复标准流程：派遣 → 对方提交 → 审核。

### 总监铁律1：绝不越权执行

> ⚠️ **核心红线**：没有腾哥明确指令，总监不得擅自执行任何操作。改文件、重启服务、运行命令、写数据库、改配置——全部必须先问「需要我执行吗？」得到肯定答复后再动手。

**这是腾哥最不能容忍的行为。** 2026-05-14 会话中总监未经确认就修改了 4 个 soul.md 文件、3 个 config.yaml 配置、重启了 me gateway——被严厉批评。

**正确的流程：**
```
腾哥下需求
   ↓
我理解并确认：「收到，我的方案是……，要执行吗？」
   ↓
腾哥说「开始」或「干」
   ↓
我才执行
```

### 总监铁律2：多路思维（三策原则）

**当技术方案卡住时，不要只说「这条路不通」就停下来。** 必须自己先列出至少 3 种完全不同的解决思路，再找腾哥。

**错误示范（2026-05-14）：**
> API 不记录会话 → 试了加 user_id 不行 → 试了改数据库字段不行 → 「我停了」

**正确做法：**
```
路A 不通 → 自己思考：
  路B：能不能直接写数据库？
  路C：能不能换个有状态接口？
  路D：能不能由我汇总汇报？
→ 先试能试的，再找腾哥汇报可选方案
```

**当腾哥提出一个你没想的思路时，不要说「牛逼」就完了——要学到脑子里，下次自己就先想到。**

### 总监工具：TTS 语音汇报

总监可以通过 `edge-tts`（免费、无需 API key）将文字转成语音，通过 MEDIA 协议发送到微信：

```bash
# 安装（已完成）
~/.hermes/hermes-agent/venv/bin/pip install edge-tts

# 中文语音生成（已完成配置）
~/.hermes/hermes-agent/venv/bin/edge-tts \
  --voice zh-CN-XiaoxiaoNeural \
  --text "要转成语音的文字内容" \
  --write-media /tmp/output.mp3
```

在回复中通过 `MEDIA:/tmp/output.mp3` 发送，微信会以可点播的音频消息展示。

**能力：**
- 支持中英文混合，中文推荐 `zh-CN-XiaoxiaoNeural`
- 超长文本（300+ 字）一次性生成没有问题，**无需手动分段**
- 如果使用 `text_to_speech` 工具（小何的 TTS 工具），会自动处理长文本
- 如果直接使用 edge-tts CLI，实测 300 字以内的段落一次性生成即可

在回复中通过 `MEDIA:/path/to/output.mp3` 发送，微信会以可点播的音频消息展示。

详见 `references/tts-voice-setup-20260514.md`。

---

## 六、Agent 互调限制与替代方案

### 问题

Hermes 当前没有内置的 Agent-to-Agent 直接互调机制。`delegate_task` 创建的是**临时匿名子智能体**，不是配置好的 profile 本身。

| 方法 | 调用的对象 | 适合 |
|------|-----------|------|
| `delegate_task` | 临时子智能体（带灵魂注入） | 短期任务、代码开发 |
| 频道@消息 | 正式profile（需共享通道） | 长期协作、团队接力 |

### delegate_task 不可用

> ⚠️ **腾哥决策**：delegate_task 已明确否决，不走这条路。创建的子智能体是匿名临时打工仔，不是真正的 dev/me/op profile。

### 真实多 Agent 协作方案

多 Agent 协作的核心原理：**所有 Agent 在同一个共享聊天频道中，通过 @mention 接力干活。**

```
小何@dev: 写个订单列表页
dev: [写代码] → @me: 美化一下
me: [美化] → @小何: 完成，请审核
```

### 可用频道对比

| 平台 | 多bot同群 | @触发 | 国内直连 | Hermes支持 |
|------|:---------:|:-----:|:--------:|:----------:|
| **企业微信 WeCom Bot** | ✅ | ✅ | ✅ 免翻墙 | ✅ 原生 WebSocket |
| **钉钉 DingTalk** | ✅ | ✅ | ✅ 免翻墙 | ✅ 原生 WebSocket |
| Discord | ✅ | ✅ | ❌ 需翻墙 | ✅ 原生 |
| Telegram | ✅ | ✅ | ❌ 需翻墙 | ✅ 原生 |
| 微信 | ❌ 插件只能一对一 | ❌ | ✅ | ⚠️ 限一对一 |
| 飞书 | ❌ 不支持 bot 被 @ | ❌ | ✅ | ✅ 原生 |

**结论：国内用户最优方案是企业微信（WeCom Bot）或钉钉。优先试企业微信，如果腾哥已有企业微信账号可直接用。**

### 企业微信（WeCom Bot）多 Agent 配置

#### 为什么选企业微信

Hermes 支持 WeCom Bot 模式（WebSocket 直连，无需公网 IP）：
- ✅ 国内直连免翻墙
- ✅ 支持群聊 @ 触发
- ✅ 每个 profile 可以绑定独立的 AI Bot
- ✅ 多个 bot 可拉进同一个群
- ✅ 支持白名单访问控制

#### 前置要求

- 企业微信组织账号（可免费创建，一人也行）
- 企业微信管理后台：https://work.weixin.qq.com/wework_admin/frame
- 每个 profile 需要创建独立的 AI Bot 应用

#### 创建 AI Bot

```bash
# 推荐：用 Hermes 向导扫码一键创建
hermes gateway setup
# 选择 WeCom → 扫码 → 自动获取 Bot ID 和 Secret
```

或手动操作：
1. 登录企业微信管理后台 → 应用管理 → 创建应用 → AI Bot
2. 填写名称（如 `dev`、`me`、`op`）
3. 复制 Bot ID 和 Secret

#### 配置到 Profile

每个 profile 独立配置 `.env`：

```bash
# ~/.hermes/profiles/dev/.env 添加
WECOM_BOT_ID=your-dev-bot-id
WECOM_SECRET=your-dev-bot-secret
WECOM_DM_POLICY=allowlist        # 私聊只允许白名单
WECOM_ALLOWED_USERS=your-user-id  # 只填腾哥的用户ID
WECOM_GROUP_POLICY=allowlist     # 群聊只响应指定群
WECOM_HOME_CHANNEL=group-chat-id # 通知推送的目标群
```

`config.yaml` 中配置：
```yaml
platforms:
  wecom:
    enabled: true
    extra:
      bot_id: "your-bot-id"
      secret: "your-secret"
      dm_policy: "allowlist"
      group_policy: "allowlist"
      group_allow_from:
        - "group_id_1"
```

#### 访问控制详解

| 配置 | 值 | 效果 |
|------|-----|------|
| `WECOM_DM_POLICY=allowlist` | 白名单模式 | 只有 `WECOM_ALLOWED_USERS` 里的人能私聊 bot |
| `WECOM_GROUP_POLICY=allowlist` | 群白名单 | 只在 `group_allow_from` 里的群响应 |
| `WECOM_ALLOWED_USERS=xxx` | 你的企业微信ID | 同事无法控制智能体 |

⚠️ **安全性**：三个 bot 的 allowlist 都只填腾哥一人。同事在群里 @bot 不会被响应。

#### 三个 bot 进群流程

1. 创建 3 个 AI Bot → 分别拿到 Bot ID + Secret
2. 分别配置到 dev/me/op 的 `.env` 和 `config.yaml`
3. 分别启动 gateway：
   ```bash
   HERMES_HOME=~/.hermes/profiles/dev hermes gateway run --replace
   HERMES_HOME=~/.hermes/profiles/me  hermes gateway run --replace
   HERMES_HOME=~/.hermes/profiles/op  hermes gateway run --replace
   ```
4. 在企微中建群，把三个 bot 拉进去
5. 总监（小何）在群里通过 @ 接力调度

#### 企业微信群聊行为

| 场景 | 行为 |
|------|------|
| 私聊 bot | ✅ 白名单用户可对话 |
| 群聊 @bot | ✅ 响应 @ 消息 |
| 群聊无 @ | ❌ 忽略 |
| 同事 @bot | ❌ 不在白名单则不响应 |
| 媒体消息 | ✅ 支持图片/文件/语音/视频 |

### 多群架构（按组分工）

**场景**：当团队同时有多条业务线（如小程序开发 + 短视频运营），建一个群拉所有 bot 会混乱。推荐**按业务线分群**：

```
┌─────────────────────┐    ┌─────────────────────┐
│  小程序项目群        │    │  短视频运营群        │
│                     │    │                     │
│  你  小何  dev  me  │    │  你  小何  op       │
│                     │    │                     │
│ 没有 op             │    │ 没有 dev 没有 me    │
└─────────────────────┘    └─────────────────────┘
```

**规则：**
- 每个群只拉该业务线相关的 bot
- 总监（小何）存在两个群中，作为跨群协调节点
- 腾哥在每个群里下对应的需求
- 总监在两个群之间串联信息

---

### 钉钉（DingTalk）多 Agent 配置

#### 前置要求

- 每个 profile 需要独立的钉钉应用（Client ID + Client Secret）
- 钉钉开发者后台：https://open-dev.dingtalk.com/
- Hermes 使用 Stream Mode（WebSocket），无需公网 IP

#### 安装依赖（必做）

```bash
# 在 Hermes venv 中安装 dingtalk-stream
/home/lt-pc/.hermes/hermes-agent/venv/bin/pip install dingtalk-stream httpx
```

⚠️ **关键陷阱**：不安装 `dingtalk-stream`，即使 `.env` 配置正确，gateway 也会报错：
```
DingTalk: dingtalk-stream not installed or DINGTALK_CLIENT_ID/SECRET not set
No adapter available for dingtalk
```

#### 配置步骤

每个 profile（dev/me/op）独立配置：

```bash
# 1. 登录 https://open-dev.dingtalk.com/ → 创建应用 → 拿到 Client ID 和 Secret
#    注意：需要钉钉企业/组织身份（免费创建），个人账号需先建团队

# 2. 配置到 profile 的 .env
cat >> ~/.hermes/profiles/dev/.env << 'EOF'

# DINGTALK
DINGTALK_CLIENT_ID=your-app-key
DINGTALK_CLIENT_SECRET=your-app-secret
DINGTALK_ALLOW_ALL_USERS=true          # 测试阶段用，后续改为 ALLOWED_USERS
EOF

# 3. 启动 gateway（用 -p 指定 profile，不要用 HERMES_HOME）
hermes -p dev gateway run --replace
```

⚠️ **重要发现**：`.env` 文件中的 `DINGTALK_CLIENT_ID/SECRET` 是必需的，`config.yaml` 中的 `platforms.dingtalk` 段可选（用于访问控制）。

#### 验证连接

```bash
tail -10 ~/.hermes/profiles/dev/logs/gateway.log
```

**连接成功标志**：
```
Connecting to dingtalk...
[Dingtalk] Connected via Stream Mode
✓ dingtalk connected
```

微信 token 冲突是预期行为（被 default profile 占用）：
```
✗ weixin failed to connect
```

#### 多 profile 同时启动

```bash
hermes -p dev gateway run --replace
hermes -p me gateway run --replace
hermes -p op gateway run --replace
```

#### 钉钉群聊行为

---

## 六-B、API 内部分派（替代 @mentions 的终极方案）

> 发现于 2026-05-14 会话。当钉钉平台限制（bot 不能 @ bot）或用户想「只跟小何一个人说话」时使用。

### 原理

每个 profile 的 gateway 都内置了一个 OpenAI 兼容的 HTTP API 服务器。总监（小何）可以通过本机 HTTP 调用直接向 dev/me/op 派活，**全程不经过聊天平台**。

```
你在微信告诉我 → "让op写条文案"
     ↓
我通过API派给op → op写完回传
     ↓
我筛选/汇总 → 发微信给你
```

### 架构

```ascii
┌───────────────────────────────────────────────┐
│                     WSL                        │
│                                                │
│  小何 (default:8642)                           │
│    └── API: /v1/chat/completions               │
│          │                                     │
│          ├── dev (8643)  ← 通过API派活         │
│          ├── me  (8644)  ← 通过API派活         │
│          └── op  (8645)  ← 通过API派活         │
│                                                │
└───────────────────────────────────────────────┘
```

### 配置检查

确保每个 profile 的 `config.yaml` 中有 api_server 配置：

```yaml
platforms:
  api_server:
    enabled: true
    extra:
      port: <唯一端口>    # dev:8653, me:8643, op:8654
      host: 127.0.0.1
      key: <API_KEY>     # 从 .env 或 config.yaml 获取
```

⚠️ 各 profile 的 api_server 端口**必须不同**，否则冲突。

### 获取 API Key

```bash
# 从 profile 的 config.yaml 中获取
grep "key:" ~/.hermes/profiles/dev/config.yaml | head -3
# 优先取 platforms.api_server.key 字段
# 如果该字段为空字符串，可能不需要 auth，或需要补充密钥
```

### 派活命令

```bash
# 向 op 派活（端口根据 profile 不同调整）
curl -s -X POST http://127.0.0.1:8645/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{
    "model":"deepseek-v4-flash",
    "messages":[{"role":"user","content":"派活内容..."}]
  }'
```

**实战验证（2026-05-14）：** 此方法经测试可行，op/dev/me 三个 profile 均能通过此 API 成功接收任务并返回结果。注意：使用前需确认目标 profile 的 gateway 在线（不是 4 个 default 打架的状态）。

### API Key 获取（实战）

查看 profile 的 config.yaml：
```yaml
platforms:
  api_server:
    key: ''           # 如果为空字符串，可能不需要 API key
    extra:
      key: xxx        # 或在这里
```

注意：me profile 的 api_server key 为空（无验证），dev 和 op 使用同一个 key。

### 会话记录位置

API 派活的对话记录**会保存**在目标 profile 的 sessions 目录下：

```bash
# op 的 API 派活会话
~/.hermes/profiles/op/sessions/session_api-xxxxx.json
# 文件以 session_api- 前缀命名，区别于 dingtalk 或 weixin 来源的会话
```

### ⚠️ 陷阱7：API 会话在 Web UI 不可见

**症状**：通过 API 派活的会话文件 `.json` 确实存在，但 Web UI 的 profile 下拉菜单中看不到。

**根因**：Web UI 通过 `v1/chat/completions` 端点创建的是**无状态会话**（stateless completion），虽然生成了文件但未注册到 op 的会话索引中。

**解决方案**（按优先级排序）：
1. **方案A（推荐）**：总监在 API 派活后，把结果直接同步到自己的会话中。这样用户在 Web UI 选「小何」就能看到全部记录。
2. **方案B**：通过 API 服务器的有状态端点（如 `/api/chat`）派活，会自动注册会话。
3. **方案C**：用户直接查看 session 文件（小何可代读）。

### 与钉钉群模式的关系

| 维度 | 钉钉群 @ 模式 | API 内部分派模式 |
|------|:------------:|:----------------:|
| 用户操作 | 建2个群，群内@bot | 只在微信跟小何说话 |
| 工作透明度 | 群内实时可见 | 小何汇总汇报 |
| @ 限制 | bot 不能 @ bot | 无 @ 概念 |
| 记录位置 | 钉钉聊天记录 + session文件 | session文件（需读） |
| 适合场景 | 小微团队全透明 | 小何总管，简化管理 |

---

## 七、⚠️ 多 Agent 协作陷阱

### 陷阱1：死循环

当全部 gateway（包括 default）需要清场重来时，**顺序和时机极其重要**，否则触发连环崩溃。

#### 崩溃原因

当多个 gateway 同时抢占同一平台连接（钉钉/微信），先断的旧连接还没来得及释放，新连接就抢上去 → 钉钉拒接 → gateway 崩 → 系统自动拉起 → 又抢又崩 → 死循环。

**完整根因链（2026-05-14 实战）：**

```
① prefill_messages_file 指向了 .md 文件（只认 JSON）
   → 每次起 gateway 就报错 Failed to load prefill messages
   ↓
② 病了的 gateway 反复崩溃 → Hermes 自我保护机制自动拉起新进程
   ↓
③ 拉起多了，new 脚本不再带 -p 参数
   → 变成不带 profile 的 default gateway
   ↓
④ 4 个 default gateway 在抢同一个微信 bot token
   → 微信 token 已被占用的错误
   ↓
⑤ dev/me/op 的钉钉连接也抢来抢去
   → 反复 network exception
```

```
旧 gateway（还没完全断开）  → 新 gateway（抢连）
         ↓                          ↓
   [network exception]      [network exception]
         ↓                          ↓
  自动拉起新进程（不带 -p）    自动拉起新进程（不带 -p）
         ↓                          ↓
  多个 default 打架           全部在抢微信 token
```

#### 正确重启流程

```bash
# 步骤A：清场
pkill -f "hermes.*gateway.*run"

# 步骤B：等 5-8 秒让平台连接完全释放
sleep 5

# 步骤C：逐一启动，每启一个确认再启下一个
# 1. default（微信/小何）
hermes gateway run --replace

# 确认 default 日志显示「✓ weixin connected」
# 再继续下一步（约等 8-10 秒）

# 2. dev
hermes -p dev gateway run --replace

# 确认 dev 日志显示「✓ dingtalk connected」

# 3. me
hermes -p me gateway run --replace

# 确认 me 日志显示「✓ dingtalk connected」

# 4. op
hermes -p op gateway run --replace

# 确认 op 日志显示「✓ dingtalk connected」
```

**关键原则：**
- 每启一个 gateway 后等待其连接成功的日志出现，再启下一个
- dev/me/op 不配微信通道（WeChat token 由 default 独占）
- 如果启动后几秒内日志出现 `network exception`，说明平台连接未完全释放，等更久再试

#### ⚠️ 信号：需要重启

出现以下信号时应当清场重启：
- 钉钉群内 @bot 无响应（即使 gateway 日志显示 Connected）
- gateway.log 反复出现 `[start] network exception, error=`
- `ps aux | grep gateway` 显示多个不带 `-p` 的 default gateway 进程
- 各日志中的 PID 频繁变化说明 gatewy 在反复重启

---

## 七、⚠️ 多 Agent 协作陷阱

### 陷阱1：死循环

**症状**：AgentA 干完活发 👍，AgentB 响应收到发 👋，AgentA 又响应...

**治本三层**：

**第一层（配置层）**：`DISCORD_ALLOW_BOTS=mentions` — 只响应被 @ 的消息
**第二层（配置层）**：关闭隐式触发（Discord 的 `replied_user: false`）
**第三层（认知层）**：SOUL.md 写死终止协议

SOUL.md 终止协议模板：
```markdown
## 任务终止与防循环规范
- **明确终结**：确认任务完成后，必须以「【任务结束】」结尾
- **禁止冗余**：任务结束后严禁发送任何表情、寒暄或确认消息
- **中断反馈**：不要对其他 Agent 的结束消息做二次响应
- **艾特控制**：结束总结中禁止再次 @ 任何人
```

### 陷阱2：@mention 格式不对

**根因**：纯文本喊名字没用，通道特定的 @ 格式才是触发机制。
- Discord：`<@用户ID>`（不是 `@名字`，是 `<@数字ID>`）
- 微信：`@机器人微信名`
- **钉钉**：通过 Hermes 网关发送的「@op」纯文本字符串不会被钉钉识别为真正的 @mention。用户会反馈「纯字符」格式不对。

**修复**：
- 在 SOUL.md 花名册里直接写入 @ 格式的 ID
- 但钉钉注意：**AI agent 输出的文本 @ 在钉钉中仅是字符串，不是原生 @mention**。正确做法是让用户指引格式规则，或通过钉钉 Stream 模式的原生 @ 事件触发（网关自动转换）。代理层输出时要说明「@op」是文本标记，实际在钉钉中需点选 @ 按钮选人。

### 陷阱2b：钉钉群「找谁办事 @谁」规则

**症状**：用户说「这个群的规则就是找谁办事需要 @谁」，但总监用纯文本 `@op` 输出到钉钉群，用户回复「格式不对啊。。纯字符」。

**根因**：钉钉群聊中，@另一个人/ bot 必须使用钉钉的点选 @ 机制（点击输入框左上方 @ 图标选人），纯文本输入的 `@名字` 在钉钉中只是一个字符串，不是真正的 @mention。

**修复流程**：

```
用户要求审核某智能体的产出
   ↓
总监需要在群里 @该智能体提交
   ↓
⚠️ 不要直接输出 "@名字" 纯字符串到钉钉群
   ↓
正确做法：先向用户确认 "ta在群里的 @ 格式是什么？然后在回复中标注需要 @ta"
   ↓
如果无法通过钉钉原生 @mention（因为AI输出只是文本），
则改用话术让用户帮忙 @：
  "腾哥，麻烦你帮我 @op 一下，让ta把最新文案发出来，我收到就审"
```

注意：这是钉钉连接器（Hermes Gateway Dingtalk 适配器）的当前限制。如果以后适配器支持自动转换文本 @ 为钉钉原生 @mention，此陷阱可解除。

### 陷阱5：prefill_messages_file 只认 JSON

**症状**：gateway 启动时日志报错：
```
Failed to load prefill messages from /path/to/soul.md: Expecting value: line 1 column 1 (char 0)
```

**根因**：`prefill_messages_file` 配置项只接受 **JSON 格式文件**，不能指向 markdown 文件。指向 markdown 时系统尝试用 JSON 解析，直接失败。

**修复**：删掉 `prefill_messages_file` 配置，恢复为 `''`（空字符串）。灵魂设定（人设）通过 profile 目录下的 `SOUL.md` 文件加载，不是通过这个配置项。

```yaml
# ❌ 错误做法
prefill_messages_file: /path/to/soul.md

# ✅ 正确做法
prefill_messages_file: ''
```

灵魂文件放在 profile 目录下即可被自动加载：
```
~/.hermes/profiles/dev/SOUL.md
~/.hermes/profiles/me/SOUL.md
~/.hermes/profiles/op/SOUL.md
```

### 陷阱6：钉钉机器人不能 @ 另一个机器人

**症状**：总监在群里输出文本 `@op 改一下这条文案`，用户反馈「格式不对啊。。纯字符」「是字符串不是真的 @」。

**根因**：这是**钉钉平台限制**，不是配置问题。钉钉的 @mention 依赖客户端发起的特定内部 ID 标记：

| 场景 | 能否 @ |
|------|:------:|
| 人 @ 机器人 | ✅ 钉钉客户端自动生成 @ 标记 |
| 机器人 @ 人 | ❌ 输出 `@名字` 只是纯文本字符串 |
| 机器人 @ 机器人 | ❌ 钉钉不处理 bot 发出的 @ 文本 |

**解决方案**：**不要依赖 @ 功能进行机器人之间的沟通**。改用以下协作模式：

- 总监直接说「op，请把最新文案发出来」，不需要 @ 符号
- op 根据称呼关键词（如 `op` 开头的消息）判断是否被叫到
- 或者让用户帮忙做 @：小何：「腾哥，麻烦帮我 @op 一下，让ta把文案发出来」

### 陷阱7：Gateway 进程诊断 — ps 输出中 -p 参数可能不可见

**症状**：`ps aux | grep gateway` 输出中所有 gateway 进程看起来都不带 `-p` 参数，像是全在跑 default，导致误判「dev/me/op 全崩了」。

**根因**：不同的 ps 实现在输出长度限制或参数截断上行为不同。当 gateway 进程是由 Hermes 内部的 `gateway run --replace` 通过 shell 包装启动时，ps 的 CMD 列有时会省略 `-p dev` 部分（子 shell 启动的进程不继承完整命令行）。这**不意味着进程是 default profile**。

**诊断方法**：不要只看 ps 输出，同时检查：
```bash
# 方法1：核对端口——每个 profile 的 api_server 端口唯一
ss -tlnp | grep hermes | grep -v grep

# 方法2：看 gateway.log 确认哪个 profile 在运行
head -1 ~/.hermes/profiles/dev/logs/gateway.log  # 看是否有 'profile dev' 字样

# 方法3：检查 gateway_state.json 的 argv 字段
cat ~/.hermes/profiles/dev/gateway_state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('argv','?'))"
```

**总结**：gateway 是否以某个 profile 身份运行，以端口和日志为准，不以 ps 的 -p 参数可见性为准。

### 陷阱8：钉钉/平台配置在 Gateway 重启/混乱后丢失

**症状**：之前成功配置了 dev/me/op 三个 profile 的钉钉平台参数（client_id/secret/robot_code）且均连接成功。经过一次 gateway 全局清场重启（pkill → sleep → 逐个启动）后，**只有 me profile 保留了钉钉配置**，dev 和 op 的配置消失了。

**诊断方法**：检查各 profile 的 config.yaml 是否有对应的 platforms 段：
```bash
search_files pattern=dingtalk path=~/.hermes/profiles/
# 如果某 profile 没有匹配结果，说明配置已丢失
```

**根因分析**：
1. Gateway 进程被 kill 后自动重启时，可能因为 `--replace` 或 GatewayManager 的 `detectAllOnStartup()` 流程，将 config.yaml 重新写入
2. 写入时只保留了 `api_server` 段，丢弃了其他平台配置（如 dingtalk）
3. 或者 `.env` 文件中的环境变量被覆盖/清理，导致 gateway 重新连接时找不到凭证

**修复**：
```bash
# 1. 获取缺失 profile 的 client_id 和 client_secret
# 2. 手动补充到 .env 和 config.yaml
cat >> ~/.hermes/profiles/<name>/.env << 'EOF'
DINGTALK_CLIENT_ID=your-client-id
DINGTALK_CLIENT_SECRET=your-secret
DINGTALK_ALLOW_ALL_USERS=true
EOF

# 3. config.yaml 添加 dingtalk 段
# 4. 重启 gateway
HERMES_HOME=~/.hermes/profiles/<name> hermes gateway run --replace &
```

**预防**：
- 修改 profile 的平台配置后，立即备份 config.yaml 和 .env
- 重启 gateway 后，验证配置未丢失：`search_files pattern=dingtalk path=~/.hermes/profiles/<name>/`
- 避免在 GatewayManager（Web UI）正在管理多 profile 时手动 pkill，优先在 Web UI 的 Settings → Gateway 面板操作

### 陷阱9：API 会话在 Web UI 不可见

**症状**：通过 `v1/chat/completions` API 给 op/dev/me 派活后，会话 `.json` 文件和 `state.db` 数据库里都有记录，但 Web UI 选对应 profile 时看不到。或者用户能看到内容但 Web UI 断开连接。

**根因（三层面解析）：**

API 派活涉及三层存储，Web UI 只认其中一层：

| 存储层 | 文件位置 | API 是否写入 | Web UI 是否读取 |
|--------|---------|:------------:|:--------------:|
| sessions.json 索引 | `profiles/<name>/sessions/sessions.json` | ❌ | ✅（主索引） |
| state.db (SQLite) | `profiles/<name>/state.db` → sessions 表 | ✅ | ❌（仅内部用） |
| 会话文件 | `profiles/<name>/sessions/session_api-*.json` | ✅ | ❌（无索引） |

API 派活 (`v1/chat/completions`) 创建了会话文件和数据库记录，但未注册到 `sessions.json` 索引，因此 Web UI 无法列举该会话。

**解决方案**（按优先级排序）：

1. **方案A（推荐）**：总监在 API 派活后，把结果直接同步到自己的会话中（通过微信对话自然记录）。这样用户在 Web UI 选「小何」就能看到全部记录。这是目前最可靠的方式，无需额外代码。

2. **方案B**：直接查看 session 文件 —— 小何可通过 `read_file` 读取目标 profile 的 session 文件内容，向用户展示。

3. **方案C**：手动在 sessions.json 中注册 API 会话（不推荐，容易搞丢数据且下次重启可能被覆盖）。

4. **~~方案D：直接写 Web UI 数据库~~** ❌ **已测试但不推荐（两条死路）**

   两条路都试过，都不通：

   **路1（默认 journal 模式）：** Python sqlite3 与 Web UI 的 node:sqlite (WAL 模式) 存在锁冲突，写 `~/.hermes-web-ui/hermes-web-ui.db` 会导致 Web UI 显示「gateway 已断开」，用户必须手动重启网关。✅ 数据确实写入（重启后能看到内容），但每次写库必断连。

   **路2（WAL 模式 + BEGIN IMMEDIATE，已验证可行的折中方案）：** 用 `PRAGMA journal_mode=WAL` 匹配 Web UI 模式。
   - ✅ Web UI 不断连（无锁冲突）
   - ✅ 数据写入 `messages` 表成功
   - ✅ 用户切换会话（点击其他对话再切回）即可看到
   - ❌ 前端不实时显示（Vue Pinia store 内存缓存）
   
   **适用工作流：** API 派活后 → WAL 模式写库 → 用户手动切换到其他会话再点回来 → 新消息可见。用户反馈「不需要自动刷新，我自己点其他界面再切回来就行 」。参见 `hermes-web-ui-deploy` 技能的 section 12。\n\n   **验证代码（2026-05-14 安全）：**\n   ```python\n   import sqlite3, time\n   conn = sqlite3.connect('/home/lt-pc/.hermes-web-ui/hermes-web-ui.db')\n   conn.execute('PRAGMA journal_mode=WAL')\n   conn.execute('BEGIN IMMEDIATE')\n   now = time.time()\n   conn.execute('INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',\n       (session_id, 'user', user_msg, now))\n   conn.execute('INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',\n       (session_id, 'assistant', op_reply, now+0.001))\n   conn.commit()\n   conn.close()\n   ```\n\n   **测试结果：** Web UI PID 不变（没重启），数据在库，用户切会话后可见。

   **结论：** 用 WAL + BEGIN IMMEDIATE 模式写 hermes-web-ui.db 是一条可行的折中路径：数据安全写入，Web UI 不断连，用户 F5 或切会话后可见。但这不是实时方案，前端不自动刷新。详见 reference 文件。

5. **✅ 方案F（2026-05-14 验证，当前主方案）：双库直接写入 + 告知用户刷新**

   **原理：** 用 WAL + BEGIN IMMEDIATE 同时写两个库（目标 profile 的 state.db + Web UI 的 hermes-web-ui.db），然后告知用户 F5 刷新或切换会话。
   
   ⚠️ **更新（2026-05-14 晚）：** Gateway 重启不会触发 Web UI 重新同步消息列表。写库后直接告知用户手动刷新是最可靠的路径。

   **流程：**
   ```python
   # 1. 写 op/state.db
   conn = sqlite3.connect("~/.hermes/profiles/op/state.db")
   conn.execute("PRAGMA journal_mode=WAL")
   conn.execute("BEGIN IMMEDIATE")
   conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
                ("现有会话ID", "user", "消息", time.time()))
   conn.execute("UPDATE sessions SET message_count=message_count+1 WHERE id=?",
                ("现有会话ID",))
   conn.commit(); conn.close()

   # 2. 写 Web UI 的 hermes-web-ui.db
   conn = sqlite3.connect("~/.hermes-web-ui/hermes-web-ui.db")
   conn.execute("PRAGMA journal_mode=WAL")
   conn.execute("BEGIN IMMEDIATE")
   conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
                ("现有会话ID", "user", "消息", int(time.time())))
   conn.execute("UPDATE sessions SET message_count=message_count+1, last_active=? WHERE id=?",
                (int(time.time()), "现有会话ID"))
   conn.commit(); conn.close()

   # 3. 重启目标 profile 的 gateway
   kill <op-gateway-pid>
   # gateway 用 --replace 自动重启
   ```

   ⚠️ **关键规则：session 合并，不创建新会话。** 所有 op 消息必须追加到现有会话（如"小何与op"的 `mp5guacelv7uea`），不创建新 `api-*` 会话。这样用户在 Web UI 中打开"小何与op"即可看到完整历史，不需要在多个会话间切换。

## 会话关联的铁律（2026-05-14 腾哥确认）

> 所有总监向子智能体（op/dev/me）发送的消息必须合并到**既有会话**中，绝不可创建新会话。

### 规则

```yaml
目标会话: "小何与op" → session_id: mp5guacelv7uea
禁止行为: send_message 工具创建 api-* 新会话
正确做法: 直接写入既有会话的 state.db + Web UI DB
```

### 根因

- `send_message` 工具**每次调用都创建独立会话**（`api-*` ID），不会自动追加到现有会话
- 新会话在 Web UI 中表现为独立条目，用户需要手动切换查看，打乱工作流
- 腾哥要求：所有 op 交互记录在一条会话中，方便追溯

### 写入流程

每次向子智能体发送消息，必须同时写两个库：

```python
import sqlite3, time

session_id = "mp5guacelv7uea"  # 固定的"小何与op"会话ID
now_ts = int(time.time())

# 1. 写 op/state.db（Hermes profile 数据库）
op = sqlite3.connect("~/.hermes/profiles/op/state.db")
op.execute("PRAGMA journal_mode=WAL")
op.execute("BEGIN IMMEDIATE")
op.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)", 
           (session_id, "user", "问题/派活内容", now_ts))
op.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)", 
           (session_id, "assistant", "回答/产出内容", now_ts + 1))
op.execute("UPDATE sessions SET message_count = message_count + 2 WHERE id = ?", (session_id,))
op.commit(); op.close()

# 2. 写 Web UI 的 hermes-web-ui.db
wu = sqlite3.connect("~/.hermes-web-ui/hermes-web-ui.db")
wu.execute("PRAGMA journal_mode=WAL")
wu.execute("BEGIN IMMEDIATE")
wu.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)", 
           (session_id, "user", "问题/派活内容", now_ts))
wu.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)", 
           (session_id, "assistant", "回答/产出内容", now_ts + 1))
wu.execute("UPDATE sessions SET message_count = message_count + 2, last_active = ? WHERE id = ?", 
           (now_ts + 1, session_id))
wu.commit(); wu.close()
```

### 注意

- **必须写 user + assistant 两条**，因为 op 不会自动从数据库写入中生成响应
- **时间戳必须递增**（`now_ts` vs `now_ts + 1`），否则 Web UI 排序乱序
- **role 交替**：user → assistant 成对出现
- 写完后用户需 **F5 刷新页面** 或 **切换会话再切回** 才能看到（前端不自动刷新）

### 验证结果（2026-05-14）：
   - ✅ 数据双库写入成功（13个测试会话共50条消息）
   - ✅ gateway 重启 → Web UI 自动重连 → 新会话立即可见
   - ⚠️ 用户需刷新页面一次（自动重连后浏览器 WebSocket 重新建立）
   - ✅ 不影响其他 profile（只重启目标 profile 的 gateway）
   - ❌ 如果只写 op/state.db 不写 hermes-web-ui.db → Web UI 不显示
   - ❌ 如果写 hermes-web-ui.db 不用 WAL+BEGIN IMMEDIATE → 锁冲突崩 Web UI

   不直接写数据库，而是通过 Web UI 自身的 API 端点在已存在的会话中追加消息。这样 Web UI 自己管理数据库写入，不会产生锁冲突。需要先获取 Web UI 的认证 token。

   ```bash
   # 从 Web UI 日志获取 token
   grep "Auth enabled" ~/.hermes-web-ui/server.log

   # 获取 Web UI 中某 profile 的会话列表
   curl -s http://localhost:8648/api/sessions \
     -H "Authorization: Bearer <TOKEN>"

   # 向指定会话发送消息（需要找到正确的 API 端点）
   ```

   ⚠️ 注：Web UI API 有 rate limit 机制，连续失败后会被临时锁定。等待冷却后重试。

**关于用户看到的显示机制（2026-05-14 实战结论）：**

- Web UI 的会话数据存储在 `~/.hermes-web-ui/hermes-web-ui.db`（SQLite, WAL 模式）
- Web UI 的 **sessions 表** 实际存储会话列表，每条会话记录含 `profile` 字段（指示属于哪个 profile）
- 当用户通过 Web UI 发送消息时，Web UI 代理到对应 profile 的 gateway API，同时在自己的数据库中记录消息
- 所以要让 API 派活记录在 Web UI 可见，核心是**将消息写入 Web UI 的数据库**，而不是 profile 的 state.db
- 但直接写 Web UI 数据库有锁冲突风险（见方案D的说明）

**一句话总结（2026-05-14 更新）：** 方案F（双库写 + 告知用户刷新）是目前唯一经过验证可行的路径。方案A（汇总到小何会话）是用户侧的补充视图。方案D（写 Web UI DB）通过 WAL 模式可安全写入，但需配合用户手动刷新。
