#!/usr/bin/env python3
"""PreToolUse hook для browser_snapshot — блокирует вызов без filename."""
import sys
import json

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
filename = tool_input.get('filename')
if not filename:
    print(json.dumps({
        'continue': False,
        'stopReason': 'BLOCKED: browser_snapshot без filename возвращает 50-100K токенов DOM в чат и валит сессию ("session stopped responding"). Варианты: (1) добавить filename для записи в файл; (2) предпочтительно: использовать browser_evaluate с компактным селектор-извлечением (Object.keys, длина, обрезанный sample). См. ~/.claude/CLAUDE.md раздел 14.'
    }, ensure_ascii=False))
