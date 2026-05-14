#!/usr/bin/env python3
"""PreToolUse hook для browser_take_screenshot — блокирует fullPage:true."""
import sys
import json

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
if tool_input.get('fullPage') is True:
    print(json.dumps({
        'continue': False,
        'stopReason': 'РЕКОМЕНДАЦИЯ: Playwright full-page скрин валит сессию ошибкой "An image in the conversation exceeds the dimension limit (2000px)". Использовать вместо этого: mcp__Claude_Preview__preview_snapshot (текст DOM), preview_screenshot (viewport, не full), preview_inspect (CSS-значения). Если всё же Playwright — fullPage:false и предварительно browser_resize 1400x900.'
    }, ensure_ascii=False))
