#!/usr/bin/env python3
"""PreToolUse hook для <your-db> SELECT — предупреждает об отсутствии LIMIT."""
import sys
import json
import re

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
sql = tool_input.get('sql') or tool_input.get('query') or ''
if not sql or not re.search(r'\bselect\b', sql, re.IGNORECASE):
    sys.exit(0)
limit_match = re.search(r'\blimit\s+(\d+)', sql, re.IGNORECASE)
has_agg = bool(re.search(r'\b(count|sum|avg|max|min)\s*\(', sql, re.IGNORECASE))
msg = None
if not limit_match and not has_agg:
    msg = 'WARNING: <your-db> SELECT без LIMIT и без агрегата. Делегируй mfo-db-researcher.'
elif limit_match and int(limit_match.group(1)) > 500:
    msg = f'WARNING: <your-db> LIMIT {limit_match.group(1)} >500. Используй mfo-db-researcher с Write в файл.'
if msg:
    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'additionalContext': msg
        }
    }, ensure_ascii=False))
