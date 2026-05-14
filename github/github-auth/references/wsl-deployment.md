# WSL Environment Deployment Notes

## Environment Baseline

Recorded from a fresh WSL Ubuntu setup (lt-pc@WSL2):

| Component | State |
|-----------|-------|
| `git` | ✅ v2.43.0 |
| `gh` CLI | ❌ Not installed (no sudo) |
| Git identity | ❌ Not configured |
| SSH keys | ❌ None |
| Credential store | ❌ Empty |

## Setup Sequence That Worked

### Step 1: Configure Git Identity
```bash
git config --global user.name "LT407631"
git config --global user.email "407631@qq.com"
```

### Step 2: Generate SSH Key (no passphrase for automation)
```bash
ssh-keygen -t ed25519 -C "407631@qq.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

### Step 3: Accept GitHub Host Key
```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
```

### Step 4: Verify SSH Connection
```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

### Step 5: User Adds SSH Key on GitHub
1. Go to https://github.com/settings/keys
2. Click "New SSH key"
3. Paste the public key from Step 2
4. Save

### Step 6: Create Repository (Manual, No Token)
Since `gh` is not installed and no API token is available:
1. User goes to https://github.com/new
2. Creates blank repo (no README, no .gitignore)
3. Agent pushes via SSH:
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin git@github.com:<user>/<repo>.git
git push -u origin main
```

## GitHub Rate-Limit Recovery

If user enters wrong password too many times:

| Symptom | Fix |
|---------|-----|
| "Incorrect password" repeated | Switch to SSH auth immediately (no password needed) |
| Account locked (15min-1hr) | Check email for GitHub unlock link; or wait |
| API rate limit (429) | Wait 30-60 seconds, or check `~/.hermes-web-ui/.login-lock.json` |

## Key Differences from Skill Defaults

- **No `gh` CLI** — all GitHub API operations require token or manual web UI
- **SSH preferred** — avoids password/token prompt issues on headless WSL
- **No sudo** — can't install `gh` via apt; if needed later, use npm: `npm install -g gh`
