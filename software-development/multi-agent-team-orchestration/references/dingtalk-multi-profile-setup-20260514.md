# DingTalk 多 Profile 钉钉通道配置记录

> 创建日期：2026-05-14
> 最后更新：2026-05-14
> 腾哥团队首次成功配置 3 个 Hermes profile 连接钉钉

## 背景

腾哥团队（小何总监 + dev代码 + me美工 + op运营）需要在一个共享频道内通过 @ 接力协作。微信插件只能一对一，Discord 需翻墙，最终选择钉钉。

## 凭证清单

| 角色 | Client ID | 状态 |
|------|-----------|:----:|
| 小何（总监） | dinggxtcwwo0bex7lr4u | ✅ |
| dev | dingowtbp5kpcreulsoa | ✅ |
| me | dingtvcvml41mbvj4n3d | ✅ |
| op | ding2wpi6rk1eq0brd93 | ✅ |

## 配置步骤

### 1. 安装依赖

必须在 Hermes 的 venv 中安装：

```bash
/home/lt-pc/.hermes/hermes-agent/venv/bin/pip install dingtalk-stream httpx
```

### 2. 配置 .env

```bash
cat >> ~/.hermes/profiles/dev/.env << 'EOF'
DINGTALK_CLIENT_ID=dingowtbp5kpcreulsoa
DINGTALK_CLIENT_SECRET=d2fpSzqyFt9yy7-GBXC7LrWhkmu7n61vHRqflClavRp8u8fo2g3nATQT5p9p0RGh
DINGTALK_ALLOW_ALL_USERS=true
EOF
```

### 3. 启动

```bash
hermes -p dev gateway run --replace
```

### 4. 验证

```bash
tail -20 ~/.hermes/profiles/dev/logs/gateway.log
# 应看到：✓ dingtalk connected
```

## ⚠️ 踩坑记录

### 坑1：prefill_messages_file 只认 JSON
指向 soul.md 会报 `Expecting value: line 1 column 1`。删掉设为 `''` 即可。

### 坑2：网关连环崩溃
带 -p 的 gateway 崩后，自动拉起不带 -p，变成多个 default 打架。清场后按序重启。

### 坑3：钉钉机器人不能 @ 机器人
平台限制。用称呼开头代替 @ 功能。

### 坑4：config.yaml 的 dd 段可选
.env 中的 DINGTALK_CLIENT_ID/SECRET 是关键，config.yaml 中的 platforms.dingtalk 只是访问控制。

## 群架构

| 群名 | 成员 | 用途 |
|------|------|------|
| 小程序项目群 | 腾哥、小何、dev、me | 小程序开发 |
| 短视频运营群 | 腾哥、小何、op | 短视频运营 |

## API 内部分派（2026-05-14 新增）

由于钉钉限制（bot 不能 @ bot），总监可通过内部 API 直接派活：

```bash
# 获取 API Key（从 config.yaml 的 platforms.api_server)
# op 端口 8645（根据实际配置调整）
curl -s -X POST http://127.0.0.1:8645/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"任务内容"}]}'
```

⚠️ API 派活记录会存到 session 文件但 Web UI 不可见。需总监转达结果或直接读文件。
