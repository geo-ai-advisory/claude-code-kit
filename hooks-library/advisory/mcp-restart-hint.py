#!/usr/bin/env python3
"""PostToolUse hook для Bash — напоминает о рестарте Claude Desktop после `claude mcp add`."""
import sys
import json
import re

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    sys.exit(0)
ti = data.get('tool_input') or {}
cmd = ti.get('command') or ''
if not cmd:
    sys.exit(0)
# Сматчить claude mcp add (с любыми пред-pipes)
if not re.search(r'\bclaude\s+mcp\s+add\b', cmd):
    sys.exit(0)
# Извлечь имя MCP server из команды (после `add` идёт name)
m = re.search(r'claude\s+mcp\s+add\s+(?:--\S+\s+\S+\s+)*([\w-]+)', cmd)
mcp_name = m.group(1) if m else 'NEW_MCP'
msg = (
    f'⚠️ MCP-сервер `{mcp_name}` добавлен в конфиг, но tools `mcp__{mcp_name}__*` '
    f'НЕ загружены в текущей сессии Claude Code. '
    f'Нужен **рестарт Claude Desktop** чтобы новые tools стали доступны. '
    f'До рестарта используй curl/CLI обёртки если нужно работать с этим сервисом сейчас.'
)
print(json.dumps({
    'systemMessage': msg,
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': msg
    }
}, ensure_ascii=False))
