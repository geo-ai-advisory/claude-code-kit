#!/usr/bin/env python3
"""PreToolUse hook для preview_screenshot — блокирует fullPage."""
import sys
import json

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
if tool_input.get('fullPage') is True or tool_input.get('full_page') is True:
    print(json.dumps({
        'continue': False,
        'stopReason': 'РЕКОМЕНДАЦИЯ: preview_screenshot с fullPage:true валит сессию ошибкой "An image in the conversation exceeds the dimension limit (2000px)". Только viewport (без fullPage). Если нужен конкретный участок — preview_inspect (CSS), preview_snapshot (DOM-текст) или selector-based screenshot. Запрещено снимать всю длинную страницу одним кадром.'
    }, ensure_ascii=False))
