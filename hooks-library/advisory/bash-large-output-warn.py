#!/usr/bin/env python3
"""PreToolUse hook для Bash — предупреждает о потенциально больших stdout."""

import sys
import json
import re

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
cmd = tool_input.get('command') or ''
if not cmd:
    sys.exit(0)
# Если команда содержит heredoc (cat > file <<EOF) или редирект записи (cat > file, cat >> file) — это запись, не чтение, не стрелять
is_write = bool(re.search(r'cat\s*>>?\s*\S+', cmd)) or bool(re.search(r'<<[\'"]?\w', cmd))

patterns = [
    (r'\bfind\s+(/(?!tmp|usr/local|Users)|\.)\s', 'find без узкого пути'),
    (r'\bgit\s+log(?!.*(-n\s+\d|--oneline.*head|-1|-5|-10|-20))', 'git log без лимита'),
    (r'\bgrep\s+-r\b(?!.*--include)(?!.*head)', 'grep -r без --include'),
]
# cat большого .json — только если это чтение (нет редиректа на запись)
if not is_write:
    patterns.append((r'\bcat\s+[^|>]+\.json(?!\s*\|)', 'cat большого .json'))
    patterns.append((r'\bls\s+-laR\b', 'ls -laR рекурсивно'))
hit = None
for pat, why in patterns:
    if re.search(pat, cmd, re.IGNORECASE):
        hit = why
        break
if hit:
    msg = f'WARN: Bash может вернуть >10 KB stdout ({hit}). Запиши в файл и читай через Read offset/limit.'
    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'additionalContext': msg
        }
    }, ensure_ascii=False))
