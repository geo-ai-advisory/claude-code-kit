#!/usr/bin/env python3
"""PostToolUse hook для Write|Edit — проверяет frontmatter vault-страниц."""
import sys
import json
import os

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
path = tool_input.get('file_path') or ''
if '/second-brain/wiki/' not in path or not os.path.exists(path):
    sys.exit(0)
try:
    with open(path, 'r', encoding='utf-8') as f:
        head = ''.join([next(f, '') for _ in range(20)])
except Exception:
    sys.exit(0)
missing = []
if 'type:' not in head:
    missing.append('type')
if 'recency:' not in head:
    missing.append('recency')
if missing:
    msg = f'WARNING: vault page {os.path.basename(path)} без frontmatter: {", ".join(missing)}.'
    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'PostToolUse',
            'additionalContext': msg
        }
    }, ensure_ascii=False))
