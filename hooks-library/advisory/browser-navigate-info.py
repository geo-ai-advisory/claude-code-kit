#!/usr/bin/env python3
"""PreToolUse hook для browser_navigate — info-напоминание про большой snapshot."""

import sys
import json

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
url = tool_input.get('url') or ''
# напоминание в stderr, не блокирующее
sys.stderr.write(
    'INFO: browser_navigate возвращает snapshot страницы (~50-100K симв.). '
    'Если страница тяжёлая (поиск/дашборд) — сразу следом сделай browser_evaluate '
    'с компактным результатом и игнорируй большой snapshot. См. CLAUDE.md раздел 14.\n'
)
