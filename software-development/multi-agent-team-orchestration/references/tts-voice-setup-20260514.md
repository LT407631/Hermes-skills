# TTS 语音汇报设置（2026-05-14）

## 背景

腾哥在开车时想听文字转语音，要求免费、无需 API key 的方案。

## 方案：edge-tts

> 调用微软 Edge 浏览器的免费 TTS 服务，无需任何 API key，纯免费。

## 安装

```bash
# 装到 Hermes venv 中（已完成）
~/.hermes/hermes-agent/venv/bin/pip install edge-tts
```

系统默认 pip 被 PEP 668 保护，必须装到 Hermes venv 中。

## 使用

### 基本命令

```bash
# 中文语音（女声 Xiaoxiao）
~/.hermes/hermes-agent/venv/bin/edge-tts \
  --voice zh-CN-XiaoxiaoNeural \
  --text "你好，这是测试语音" \
  --write-media /tmp/output.mp3
```

### 可用中文语音

| 语音 | 性别 | 风格 |
|------|:----:|:----:|
| zh-CN-XiaoxiaoNeural | 女 | 标准 |
| zh-CN-YunxiNeural | 男 | 标准 |
| zh-CN-YunjianNeural | 男 | 新闻 |

### 发送到微信

在 agent 回复中通过 MEDIA 协议发送：
```
MEDIA:/tmp/output.mp3
```

微信会以可点播的音频消息展示（非原生语音气泡，但点击即可播放）。

## ⚠️ 注意事项

### 文本长度

单次 `--text` 文本长度可以很长，实测 300+ 字一次性生成没有问题。**无需手动分段**。如果使用 agent 的 `text_to_speech` 工具，会自动处理长文本生成。使用 CLI 时直接将整段文字传入即可。

### 速率限制

短时间内多次请求 Microsoft TTS 服务可能被限流。分段生成时每段间隔 1-2 秒。

## 与其他方案对比

| 方案 | 费用 | API Key | 质量 | 离线 |
|------|:----:|:-------:|:----:|:----:|
| edge-tts | 免费 | ❌ | ⭐⭐⭐ | ❌ |
| gTTS (Google) | 免费 | ❌ | ⭐⭐ | ❌ |
| Piper TTS | 免费 | ❌ | ⭐⭐ | ✅ |
| OpenAI TTS | 付费 | ✅ | ⭐⭐⭐⭐⭐ | ❌ |
| ElevenLabs | 付费 | ✅ | ⭐⭐⭐⭐⭐ | ❌ |
