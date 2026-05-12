#!/usr/bin/env python3
"""PreToolUse hook для browser_evaluate — предупреждает про большие массивы без обрезки."""
import sys
import json
import re

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
tool_input = data.get('tool_input') or {}
fn = tool_input.get('function') or ''
# Эвристика: возврат больших структур без сжатия
danger_patterns = [
    r'return\s+window\.__hh\w+\s*[;}]',  # return window.__hhAll
    r'return\s+(json|data|items|results|all|resumes|experience|candidates)\s*[;}]',
    r'return\s+\{\s*\w+\s*:\s*(json|data|items|results|all|resumes|experience|candidates)\s*\}',
    r'return\s+\[\.{3}',
]
for p in danger_patterns:
    if re.search(p, fn, re.IGNORECASE):
        sys.stderr.write(
            f'WARN: browser_evaluate function похож на возврат большого массива без обрезки '
            f'(pattern: {p}). Может уронить сессию. Проверь: возвращай только summary в чат, '
            f'большие данные пиши в clipboard/файл. См. CLAUDE.md раздел 14.\n'
        )
        break
