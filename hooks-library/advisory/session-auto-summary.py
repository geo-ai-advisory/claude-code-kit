#!/usr/bin/env python3
"""Stop hook: пишет компактный 3-5 строк summary в Projects/<your-vault>/log.md.

Идея из rohitg00/agentmemory — auto-summary на конце сессии чтобы знания не
терялись на fast-сессиях где пользователь не пишет журнал руками.

В отличие от существующего auto-log который пишет только метаданные —
этот hook извлекает СУТЬ работы: какие файлы тронуты, какие задачи решены,
какие открытые вопросы. Если ничего значимого — пропускает.
"""

# Global quiet kill switch — touch ~/claude-hooks/.quiet to silence ALL advisory hooks
import sys as _sys_q, os as _os_q
if _os_q.path.exists(_os_q.path.join(_os_q.path.dirname(_os_q.path.abspath(__file__)), '.quiet')):
    _sys_q.exit(0)

import sys, json, os, re, glob
from collections import Counter
from pathlib import Path

LOG = "/Users/<you>/Library/Mobile Documents/com~apple~CloudDocs/Cursor cloud/<your-workspace>/Projects/<your-vault>/log.md"
SESSIONS = "/Users/<you>/.claude/projects/-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>"

def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        sys.exit(0)
    session_id = data.get("session_id", "")
    if not session_id:
        sys.exit(0)
    
    transcript = f"{SESSIONS}/{session_id}.jsonl"
    if not os.path.exists(transcript):
        sys.exit(0)
    
    # Читаем последние ~150 events (хвост сессии)
    try:
        with open(transcript) as f:
            lines = f.readlines()[-150:]
    except Exception:
        sys.exit(0)
    
    # Собираем сигналы
    edited_files = Counter()
    tools_used = Counter()
    user_msgs = []
    
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        msg = ev.get("message", {}) or {}
        role = msg.get("role", "")
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                tname = c.get("name", "")
                tools_used[tname] += 1
                tinput = c.get("input", {})
                if tname in ("Edit", "Write"):
                    fp = tinput.get("file_path", "")
                    if fp:
                        # Сократить путь
                        if "/<your-workspace>/" in fp:
                            fp = fp.split("/<your-workspace>/", 1)[1]
                        edited_files[fp] += 1
            if c.get("type") == "text" and role == "user":
                txt = c.get("text", "")
                # Только первые 80 символов
                if len(txt) > 20 and len(txt) < 500:
                    user_msgs.append(txt[:80])
    
    # Считаем "значимая ли сессия"
    total_tools = sum(tools_used.values())
    if total_tools < 5:
        sys.exit(0)  # пустая, не пишем
    
    # Темы из top-3 edited files
    top_files = [f for f, _ in edited_files.most_common(3)]
    
    # Определить топик из путей
    topic = "разное"
    all_paths = " ".join(edited_files.keys())
    if "dashboard" in all_paths:
        topic = "dashboard"
    elif "usedesk" in all_paths.lower():
        topic = "usedesk"
    elif "hh" in all_paths:
        topic = "hh"
    elif "<your-advisory>" in all_paths:
        topic = "<your-advisory>"
    elif "second-brain/wiki" in all_paths:
        topic = "vault"
    elif "claude/agents" in all_paths or "claude/hooks" in all_paths or "claude-hooks" in all_paths:
        topic = "architecture"
    elif "report/dashboard" in all_paths or "/report/" in all_paths:
        topic = "report"
    
    # Топ-3 user msg (последние)
    last_user = user_msgs[-1] if user_msgs else ""
    
    # Сформировать summary
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    short_sid = session_id[:8]
    
    parts = [
        f"\n## [{date}] auto | session {short_sid} | {topic}",
    ]
    
    if last_user:
        parts.append(f"- **Запрос:** {last_user}")
    
    if top_files:
        parts.append(f"- **Файлы:** {', '.join(os.path.basename(f) for f in top_files[:3])}")
    
    # Top-3 tools (без TodoWrite/Read шума)
    skip_tools = {"TodoWrite", "Read", "Glob", "Grep"}
    main_tools = [(t, n) for t, n in tools_used.most_common(10) if t not in skip_tools][:3]
    if main_tools:
        parts.append(f"- **Действия:** {', '.join(f'{t}×{n}' for t, n in main_tools)}")
    
    parts.append(f"- **Total tools:** {total_tools}")
    
    summary = "\n".join(parts)
    
    # Append в log.md
    try:
        with open(LOG, "a") as f:
            f.write(summary + "\n")
    except Exception:
        pass
    
    sys.exit(0)

if __name__ == "__main__":
    main()
