# Weixin (WeChat) Platform Setup

> Connects Hermes Agent to personal WeChat accounts via Tencent's official **iLink Bot API** (`ilinkai.weixin.qq.com`).

## Architecture

- Source: `gateway/platforms/weixin.py` (built-in adapter)
- Long-poll `getupdates` drives inbound delivery
- Every outbound reply must echo the latest `context_token` for the peer
- Media files move through an AES-128-ECB encrypted CDN protocol
- QR login is exposed as a helper for the gateway setup wizard

## Prerequisites

```bash
pip install aiohttp          # Required — HTTP client for iLink API
pip install qrcode           # Optional — render QR code in terminal for login
pip install certifi          # Recommended — fixes SSL verification on macOS Homebrew Python
```

`cryptography` is also required (for AES-128-ECB media decryption) — already installed in most environments.

## QR Login Flow

The adapter has a built-in `qr_login()` function that handles the full iLink authentication:

1. Fetch QR code from `ilinkai.weixin.qq.com/ilink/bot/get_bot_qrcode`
2. Display QR in terminal (text URL + optional ASCII art QR code)
3. User scans with WeChat mobile app
4. Poll `get_qrcode_status` until confirmed or timeout (8 min default)
5. On confirmation, save credentials to `~/.hermes/weixin/accounts/<account_id>.json`
6. Returns `{account_id, token, base_url, user_id}`

The flow handles stale QR codes (auto-refresh up to 3 times) and redirect hosts (when Tencent's load balancer assigns a different API host).

## Configuration

### config.yaml

```yaml
platforms:
  weixin:
    account_id: "<ilink_bot_id>"
    token: "<bot_token>"
    base_url: "https://ilinkai.weixin.qq.com"   # default; may change after QR login
    extra:
      split_multiline_messages: false             # optional: true = legacy per-line split
```

### Environment Variables

- `WEIXIN_ACCOUNT_ID` — iLink bot account ID
- `WEIXIN_TOKEN` — bot auth token
- `WEIXIN_BASE_URL` — API base URL (default: `https://ilinkai.weixin.qq.com`)

### Credential Storage

Credentials persist in `~/.hermes/weixin/accounts/<account_id>.json`:

```json
{
  "token": "...",
  "base_url": "https://ilinkai.weixin.qq.com",
  "user_id": "...",
  "saved_at": "2026-05-08T..."
}
```

Permissions are set to `0600` on save.

Context tokens (per-peer sync buffers) are cached in
`~/.hermes/weixin/accounts/<account_id>.context-tokens.json`.

## Enable the Gateway

```bash
# Start gateway in foreground (for testing)
hermes gateway run

# Install as background service
hermes gateway install
hermes gateway start

# Check status
hermes gateway status
```

## Supported Message Types

| Type | Support | Notes |
|------|---------|-------|
| Text | ✅ | Markdown rendered; long messages split at 2000 chars |
| Image | ✅ | AES-128-ECB decrypted from CDN |
| Video | ✅ | |
| Voice | ✅ | |
| File | ✅ | |
| Group chats | ✅ | Auto-detected via `room_id` / `chat_room_id` |
| Typing indicator | ✅ | Via `getconfig` → typing ticket |

## Markdown Handling

The adapter rewrites Markdown for WeChat's limited renderer:
- `# Heading` → `【Heading】`
- `## Heading` → `**Heading**`
- Tables → key: value pairs
- Code blocks preserved as-is
- Lines > 120 chars wrapped for copy-friendliness

## Pitfalls

- **Session expiry**: iLink tokens expire. `errcode=-14` or `ret=-2`+`"unknown error"` signals a stale session — re-authenticate with QR login.
- **Rate limits**: iLink has frequency limits (`errcode=-2`). The adapter backs off 30s on rate limit errors.
- **Poll timeout**: Long-poll timeout is 35s. The adapter treats timeouts as empty polls (no error).
- **SSL on macOS**: Homebrew's OpenSSL may not trust Tencent's CA. Install `certifi` to fix.
- **Gateway must be running**: WeChat is a gateway-only platform — the adapter polls iLink continuously. The standalone CLI doesn't connect to WeChat.
- **No message editing**: WeChat doesn't support editing sent messages — streaming uses send-final-only (no cursor animation).
- **QR login timeout**: Default 8 minutes. If QR expires, the flow auto-refreshes up to 3 times.

## Troubleshooting

```bash
# Check gateway logs for WeChat errors
grep -i "weixin" ~/.hermes/logs/gateway.log | tail -20

# Verify dependencies
python3 -c "import aiohttp, cryptography; print('OK')"

# Re-authenticate (if token expired)
# Re-run QR login flow
```
