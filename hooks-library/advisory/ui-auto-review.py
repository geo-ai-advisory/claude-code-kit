#!/usr/bin/env python3

# Throttle: silent if same hint repeats in session (anti hook-fatigue)
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from _throttle import should_emit as _should_emit
except Exception:
    def _should_emit(*a, **kw):
        return True

"""PostToolUse hook для Write|Edit — auto UI-review для HTML/CSS/SCSS/TSX/JSX."""
import sys
import json
import re
import os

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    sys.exit(0)
ti = data.get('tool_input') or {}
tr = data.get('tool_response') or {}
path = ti.get('file_path') or tr.get('filePath') or ''
if not path or not re.search(r'\.(html|css|scss|tsx|jsx)$', path, re.IGNORECASE):
    sys.exit(0)
if any(s in path for s in ['/_archive/', '/node_modules/', '/dist/', '/build/', '/.tmp/', '/test-results/']):
    sys.exit(0)
try:
    content = open(path, encoding='utf-8').read()
except Exception:
    sys.exit(0)
issues = []
fs = set(re.findall(r'font-size\s*:\s*([0-9.]+(?:px|rem|em))', content))
if len(fs) > 8:
    issues.append(f'TYPOGRAPHY: {len(fs)} разных font-size (premium <=6, scale 12/14/16/20/24/32). Используй design tokens.')
spacings = re.findall(r'(?:margin|padding|gap)\s*:\s*([^;]+);', content)
non_scale = []
scale = {'0', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20', '22', '24', '28', '32', '36', '40', '48', '56', '64', '80', '96', '128', 'auto', 'inherit', 'initial', '0px', '0rem'}
for s in spacings:
    for v in re.findall(r'([0-9.]+)(?:px|rem|em)?', s):
        if v and v.replace('.', '').isdigit() and v not in scale and float(v) > 0:
            non_scale.append(v)
if len(set(non_scale)) > 5:
    issues.append(f'SPACING: значения вне 4/8 scale: {sorted(set(non_scale))[:8]}. Используй 4/8/12/16/24/32/48px.')
if re.search(r'\.(btn|button|cta|link)\b', content) or '<button' in content:
    if not re.search(r':hover\s*\{', content):
        issues.append('STATES: button/link без :hover - добавь hover-состояние.')
    if not re.search(r':focus(-visible)?\s*\{', content):
        issues.append('STATES: нет :focus / :focus-visible - accessibility и keyboard-nav сломаны.')
if (':hover' in content or ':active' in content) and 'transition' not in content:
    issues.append('MOTION: есть :hover/:active, но НЕТ transition - резкое переключение цветов.')
inline_styles = len(re.findall(r'style\s*=\s*"[^"]{30,}"', content))
if inline_styles > 5:
    issues.append(f'INLINE-STYLES: {inline_styles} длинных inline-style. Вынеси в классы.')
if not issues:
    sys.exit(0)
msg = (
    f'AUTO UI-REVIEW для {os.path.basename(path)}: найдено {len(issues)} проблем(ы):\n'
    + '\n'.join(f'  - {x}' for x in issues)
    + '\n\nДЕЙСТВИЯ: 1) исправь перечисленное прямо сейчас; '
    'или 2) если задача сложнее - делегируй ui-quality-reviewer subagent для полной проверки 6 категорий и фиксов. '
    'не торопись отправлять пользователю "готово" пока не исправлено.'
)
if not _should_emit(data.get("session_id", "") if isinstance(data, dict) else "", "ui-auto-review", msg[:300] if "msg" in dir() else str(locals().get("msg", ""))[:300]):
    _sys.exit(0)
print(json.dumps({
    'systemMessage': msg,
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': msg
    }
}, ensure_ascii=False))
