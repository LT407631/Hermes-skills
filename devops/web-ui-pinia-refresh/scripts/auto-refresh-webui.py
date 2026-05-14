#!/usr/bin/env python3
"""
Web UI 前台自动刷新脚本

用途：写入消息到 hermes-web-ui.db，然后通过 CDP 刷新前台
用法：python3 auto-refresh-webui.py "问题" "回答" [--session SESSION_ID]

不需要调 LLM、不走 gateway、零 API 费用
"""

import sqlite3
import time
import sys
import os
import argparse


WEBUI_DB = os.path.expanduser("~/.hermes-web-ui/hermes-web-ui.db")
DEFAULT_SESSION = "mp5guacelv7uea"


def write_messages(question, answer, session_id=DEFAULT_SESSION):
    """写入 Q&A 到 Web UI 数据库"""
    now = time.time()
    qa = [("user", question), ("assistant", answer)]

    if not os.path.exists(WEBUI_DB):
        print(f"[ERROR] 数据库不存在: {WEBUI_DB}")
        return False

    conn = sqlite3.connect(WEBUI_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("BEGIN IMMEDIATE")
    c = conn.cursor()

    # 检查会话是否存在
    c.execute("SELECT id FROM sessions WHERE id=?", (session_id,))
    if not c.fetchone():
        print(f"[ERROR] 会话 {session_id} 不存在于数据库中")
        conn.close()
        return False

    # 获取全局最大消息 ID
    c.execute("SELECT COALESCE(MAX(id), 0) FROM messages")
    mid = c.fetchone()[0]

    # 写入消息
    for role, content in qa:
        mid += 1
        c.execute(
            "INSERT INTO messages (id, session_id, role, content, timestamp) VALUES (?,?,?,?,?)",
            (mid, session_id, role, content, int(now))
        )
        print(f"  [WRITE] id={mid} role={role}")

    # 更新会话元数据
    c.execute(
        "UPDATE sessions SET message_count=message_count+?, last_active=? WHERE id=?",
        (len(qa), int(now + 1), session_id)
    )
    c.execute(
        "UPDATE sessions SET preview=? WHERE id=?",
        (question[:60], session_id)
    )

    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    print(f"  [DONE] 写入 {len(qa)} 条消息到 {WEBUI_DB}")
    return True


def main():
    parser = argparse.ArgumentParser(description="写入消息并刷新 Web UI 前台")
    parser.add_argument("question", help="用户问题")
    parser.add_argument("answer", help="助手回答")
    parser.add_argument("--session", default=DEFAULT_SESSION, help=f"会话 ID (默认: {DEFAULT_SESSION})")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    args = parser.parse_args()

    if args.dry_run:
        print(f"[DRY-RUN] 将会话 {args.session}")
        print(f"  question: {args.question[:60]}...")
        print(f"  answer: {args.answer[:60]}...")
        return

    print(f"[START] 写入消息到会话 {args.session}")
    success = write_messages(args.question, args.answer, args.session)
    if not success:
        sys.exit(1)

    print(f"\n[INFO] 数据库写入完成！")
    print(f"[INFO] 接下来需通过 CDP 执行刷新命令：")
    print(f"  const p = document.querySelector('#app').__vue_app__;")
    print(f"  const pinia = p.config.globalProperties.$pinia;")
    print(f"  const chat = pinia._s.get('chat');")
    print(f"  await chat.refreshActiveSession();")


if __name__ == "__main__":
    main()
