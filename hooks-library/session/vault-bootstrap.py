#!/usr/bin/env python3
"""SessionStart + PostCompact hook — инжектит CRITICAL_FACTS + _index + log tail в контекст модели."""
import sys, json, os, subprocess

VAULT = "/Users/via/Library/Mobile Documents/com~apple~CloudDocs/Cursor cloud/B-project/Projects/second-brain"

# Только в B-project запускаем
try:
    raw = sys.stdin.read()
    data = json.loads(raw or "{}")
except Exception:
    data = {}

cwd = data.get("cwd") or os.getcwd()
if "B-project" not in cwd:
    sys.exit(0)

parts = []

# 1. CRITICAL_FACTS
fp = os.path.join(VAULT, "CRITICAL_FACTS.md")
if os.path.exists(fp):
    with open(fp) as f:
        parts.append("## CRITICAL FACTS (всегда в контексте)\n" + f.read())

# 2. _index (только заголовки секций — короче)
fp = os.path.join(VAULT, "_index.md")
if os.path.exists(fp):
    with open(fp) as f:
        idx = f.read()
    if len(idx) > 3000:
        # Только секции
        lines = [l for l in idx.split("\n") if l.startswith("#") or l.startswith("-")][:60]
        idx = "\n".join(lines)
    parts.append("## VAULT INDEX\n" + idx)

# 3. log.md tail 15
fp = os.path.join(VAULT, "log.md")
if os.path.exists(fp):
    try:
        out = subprocess.check_output(["tail", "-50", fp], text=True)
        # Только entries (## [date])
        log_lines = [l for l in out.split("\n") if l.startswith("## [")][:15]
        if log_lines:
            parts.append("## LAST SESSIONS LOG (15 most recent)\n" + "\n".join(log_lines))
    except Exception:
        pass

# 4. Open questions
qd = os.path.join(VAULT, "wiki/questions")
if os.path.isdir(qd):
    open_qs = []
    for f in os.listdir(qd):
        if not f.endswith(".md"):
            continue
        try:
            with open(os.path.join(qd, f)) as fh:
                head = fh.read(500)
            if "status: open" in head:
                first_line = next((l for l in head.split("\n") if l.startswith("#")), f)
                open_qs.append(f"- {first_line.lstrip('#').strip()} ({f})")
        except Exception:
            pass
    if open_qs:
        parts.append("## OPEN QUESTIONS (status: open)\n" + "\n".join(open_qs[:10]))

if not parts:
    sys.exit(0)

context = "\n\n".join(parts)
event = "SessionStart"  # default; для PostCompact то же самое
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": event,
        "additionalContext": (
            "🧠 VAULT AUTO-BOOTSTRAP (Projects/second-brain/) — vault entry-point ритуал выполнен автоматически:\n\n"
            + context
            + "\n\nЕсли упомянут партнёр/проект/человек — Read соответствующую wiki/<category>/<slug>.md."
        )
    }
}, ensure_ascii=False))
