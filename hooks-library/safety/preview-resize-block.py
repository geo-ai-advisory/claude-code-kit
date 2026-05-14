#!/usr/bin/env python3
"""PreToolUse hook для preview_resize — блокирует размеры >1600px."""
import sys
import json

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
w = tool_input.get('width') or 0
h = tool_input.get('height') or 0
if (isinstance(w, int) and w > 1600) or (isinstance(h, int) and h > 1600):
    print(json.dumps({
        'continue': False,
        'stopReason': f'note: preview viewport {w}x{h} слишком большой — после скрина сессия упадёт на >2000px. Использовать <= 1400x900.'
    }, ensure_ascii=False))
