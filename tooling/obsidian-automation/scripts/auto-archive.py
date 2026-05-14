#!/usr/bin/env python3
"""
Hermes 会话自动归档到 Obsidian
对话结束后自动运行，将对话整理成 Markdown 存入 Obsidian 对应项目目录
触发方式：Gateway Hook agent:end 事件
"""

import os
import json
import sys
import datetime
import re

OBSIDIAN_RAW = "/mnt/d/Documents/Obsidian Vault/raw"
OBSIDIAN_PROJECTS = {
    "微信小程序项目": "/mnt/d/Documents/Obsidian Vault/dev/微信小程序项目/03-会话项目记录",
    "微信小程序": "/mnt/d/Documents/Obsidian Vault/dev/微信小程序项目/03-会话项目记录",
    "小程序": "/mnt/d/Documents/Obsidian Vault/dev/微信小程序项目/03-会话项目记录",
    "自媒体运营": "/mnt/d/Documents/Obsidian Vault/op/自媒体运营/08-日常记录",
    "短视频": "/mnt/d/Documents/Obsidian Vault/op/自媒体运营/08-日常记录",
    "运营": "/mnt/d/Documents/Obsidian Vault/op/自媒体运营/08-日常记录",
}
SESSION_DIR = "/home/lt-pc/.hermes/sessions"

def get_latest_session():
    """获取最新的 JSON 格式会话"""
    files = sorted([f for f in os.listdir(SESSION_DIR) if f.endswith('.json') and f != 'sessions.json'])
    if not files:
        return None
    return os.path.join(SESSION_DIR, files[-1])

def clean_content(text):
    """清理工具调用日志等噪音"""
    if not text:
        return ""
    if text.startswith('{') and '"exit_code"' in text and len(text) > 500:
        return "[工具输出过长，已省略]"
    return text

def generate_title(msgs, platform, model):
    """根据对话内容生成标题"""
    user_msgs = [m for m in msgs if m.get("role") == "user"]
    if user_msgs:
        first = user_msgs[0].get("content", "")[:60].strip()
        first = re.sub(r'[^\w\s\u4e00-\u9fff]', '', first)
        if first:
            return first[:40]
    return f"{platform}_{model}"[:50]

def generate_filename(title):
    """生成文件名"""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
    safe_title = safe_title[:40]
    return f"{date_str}_{safe_title}.md"

def generate_markdown(msgs, title, platform, model, session_id, base_url):
    """生成 Markdown 内容"""
    now = datetime.datetime.now()
    user_count = sum(1 for m in msgs if m.get("role") == "user")
    tool_count = sum(1 for m in msgs if m.get("role") == "tool")
    
    md = f"""# {title}

**时间:** {now.strftime("%Y-%m-%d %H:%M")}
**平台:** {platform}
**模型:** {model}
**会话ID:** {session_id}
**API地址:** {base_url}
**对话轮次:** {user_count} 轮
**工具调用:** {tool_count} 次

---

"""
    
    for m in msgs:
        role = m.get("role", "")
        content = clean_content(m.get("content", ""))
        name = m.get("name", "")
        if not content or len(content.strip()) < 3:
            continue
        if role == "tool" and len(content) > 500:
            continue
        if role == "user":
            md += f"## 【用户】\n\n{content.strip()}\n\n---\n\n"
        elif role == "assistant":
            md += f"## 【小何回复】\n\n{content.strip()}\n\n---\n\n"
        elif role == "tool":
            md += f"```\n[{name}] → {content.strip()[:300]}\n```\n\n"
    return md

def auto_archive():
    """自动归档最新对话"""
    session_file = get_latest_session()
    if not session_file:
        print("No session found")
        return False
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    msgs = data.get("messages", [])
    if not msgs:
        print("No messages in session")
        return False
    
    platform = data.get("platform", "unknown")
    model = data.get("model", "unknown")
    session_id = data.get("session_id", "unknown")
    base_url = data.get("base_url", "unknown")
    title = generate_title(msgs, platform, model)
    
    # 自动识别项目目录（根据关键词匹配）
    first_msg = next((m for m in msgs if m.get("role") == "user"), {}).get("content", "")
    target_dir = OBSIDIAN_RAW
    for project_name, project_path in OBSIDIAN_PROJECTS.items():
        if project_name in first_msg:
            target_dir = project_path
            break
    
    os.makedirs(target_dir, exist_ok=True)
    filename = generate_filename(title)
    filepath = os.path.join(target_dir, filename)
    md = generate_markdown(msgs, title, platform, model, session_id, base_url)
    
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"ARCHIVED: {target_dir}/{filename}")
        return True
    else:
        base = filename.replace(".md", "")
        counter = 1
        while True:
            new_filename = f"{base}_{counter}.md"
            new_filepath = os.path.join(target_dir, new_filename)
            if not os.path.exists(new_filepath):
                with open(new_filepath, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"ARCHIVED: {target_dir}/{new_filename}")
                return True
            counter += 1

if __name__ == "__main__":
    try:
        auto_archive()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
