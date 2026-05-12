#!/usr/bin/env python3
"""PostToolUse hook для Write|Edit — consistency-check для HTML/MD reports в <your-workspace>."""
import sys
import json
import re
import os
from collections import Counter

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    sys.exit(0)
ti = data.get('tool_input') or {}
path = ti.get('file_path') or ''
# Только для отчётов: HTML/MD в Projects/report или Projects/.../journals или Projects/.../articles или Projects/.../reports
if not re.search(r'\.(html|md)$', path, re.IGNORECASE):
    sys.exit(0)
# Узкая фильтрация: только <your-workspace> отчёты
in_scope = (
    '/Projects/<your-reports>/' in path
    or re.search(r'/Projects/[^/]+/articles/', path)
    or re.search(r'/Projects/[^/]+/reports/', path)
    or re.search(r'/Projects/[^/]+/journals/', path)
)
if not in_scope:
    sys.exit(0)
# Игнорировать тестовые/архивные
if any(s in path for s in ['/_archive/', '/draft/', '/.tmp/', '/node_modules/']):
    sys.exit(0)
try:
    content = open(path, encoding='utf-8').read()
except Exception:
    sys.exit(0)

issues = []

# 1. Wikilinks broken: проверка ссылок vault
wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
broken = []
vault_root = '/Users/<you>/Library/Mobile Documents/com~apple~CloudDocs/Cursor cloud/<your-workspace>/Projects/second-brain'
for link in wikilinks[:30]:
    target = link.split('|')[0].split('#')[0].strip()
    if not target:
        continue
    candidates = [
        f'{vault_root}/{target}.md',
        f'{vault_root}/{target}',
        f'{vault_root}/wiki/{target}.md',
        f'{vault_root}/wiki/{target}',
    ]
    if not any(os.path.exists(c) for c in candidates):
        broken.append(target)
if broken:
    sample = broken[:3]
    issues.append(f'BROKEN WIKILINKS: {len(broken)} ссылок на несуществующие vault-страницы (примеры: {sample})')

# 2. Числа упомянутые многократно (>=2) — потенциал рассинхрона при правке
nums = re.findall(r'\b\d{2,3}(?:[ \xa0,]\d{3})+(?:\.\d+)?\b', content)
counts = Counter(nums)
top_repeats = [n for n, c in counts.items() if 2 <= c <= 10]
if len(top_repeats) >= 3:
    issues.append(f'REPEATED NUMBERS: {len(top_repeats)} форматированных чисел упомянуты несколько раз — при правке проверь все вхождения (пример: {top_repeats[:3]})')

# 3. Сводка под таблицей: если "Итого" присутствует
if re.search(r'\b(итого|total|сумма)\s*[:=<]', content, re.IGNORECASE):
    issues.append('TABLE WITH ИТОГО detected — рекомендуется consistency-checker полный для проверки sum-detail')

# 4. Period в шапке vs дата в данных
header_period = re.search(r'(Отчёт|Report|Период)\s+за\s+(\w+)\s+(\d{4})', content, re.IGNORECASE)
if header_period:
    issues.append(f'HEADER PERIOD: "{header_period.group(0)}" - проверь что все даты в данных лежат в этом периоде')

# 5. Sluggable references (партнёры): один файл - одна форма
partner_aliases = {
    '<Partner A>': ['Локо', 'LOKO', 'loko'],
    '<Partner B>': ['ХИППО', 'HIPPO', 'hippo'],
    '<Partner C>': ['ПАМПАДУ', 'PAMPADU', 'pampadu'],
}
mismatch = []
for canon, variants in partner_aliases.items():
    if canon in content:
        for v in variants:
            if v in content and v != canon:
                mismatch.append(f'{canon} vs {v}')
if mismatch:
    issues.append(f'PARTNER FORMS: смешанные написания партнёров: {mismatch[:3]}')

if not issues:
    sys.exit(0)

msg = (
    f'AUTO CONSISTENCY-CHECK для {os.path.basename(path)}: найдено {len(issues)} потенциальных проблем(ы):\n'
    + '\n'.join(f'  - {x}' for x in issues)
    + '\n\nДЕЙСТВИЯ: 1) исправить wikilinks если broken; '
    '2) для проверки числовой консистентности (sum-detail, cross-section) - делегировать consistency-checker subagent. '
    'НЕ публиковать пока не разобрано.'
)
print(json.dumps({
    'systemMessage': msg,
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': msg
    }
}, ensure_ascii=False))
