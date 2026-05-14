#!/usr/bin/env python3

# Global quiet kill switch — touch ~/claude-hooks/.quiet to silence ALL advisory hooks
import sys as _sys_q, os as _os_q
if _os_q.path.exists(_os_q.path.join(_os_q.path.dirname(_os_q.path.abspath(__file__)), '.quiet')):
    _sys_q.exit(0)


# Throttle: silent if same hint repeats in session (anti hook-fatigue)
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from _throttle import should_emit as _should_emit
except Exception:
    def _should_emit(*a, **kw):
        return True

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
    if not _should_emit(data.get("session_id", "") if isinstance(data, dict) else "", "vault-frontmatter-check", msg[:300] if "msg" in dir() else str(locals().get("msg", ""))[:300]):
        _sys.exit(0)
    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'PostToolUse',
            'additionalContext': msg
        }
    }, ensure_ascii=False))
