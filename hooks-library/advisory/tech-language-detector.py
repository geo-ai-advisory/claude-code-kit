#!/usr/bin/env python3
"""Stop hook — ловит технический язык в свежем assistant text.

Корневая проблема: пользователь — бизнес-сторона, модель пишет ему
«Hook блокирует Bash из-за showcase.html / ShowcaseEndpoints.cs, нужен git stash»,
«семантический approve фразой "осознанно push"», UUID / endpoint paths /
имена классов / git команды — пользователь не понимает что от него хотят.

Hook smell-checks последний assistant text на технические markers и выдаёт
log-style note чтобы модель **в следующем сообщении** переформулировала.

Не блокирует (log-style noise, не command).
"""

# Global quiet kill switch
import sys as _sys_q, os as _os_q
if _os_q.path.exists(_os_q.path.join(_os_q.path.dirname(_os_q.path.abspath(__file__)), '.quiet')):
    _sys_q.exit(0)


import sys
import json
import os
import re

# Throttle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _throttle import should_emit as _should_emit
except Exception:
    def _should_emit(*a, **kw):
        return True


TRANSCRIPT_DIR = (
    '/Users/<you>/.claude/projects/'
    '-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
)

# Technical markers — что не должно быть в обычном сообщении пользователю
TECH_PATTERNS = [
    # UUID (full hex с дефисами)
    (r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', 'UUID'),
    # Short hash 7-12 hex (git commits, variants)
    (r'\b[a-f0-9]{7,12}\b', 'hash'),
    # Endpoint paths
    (r'(?:POST|GET|PUT|DELETE|PATCH)\s+/[a-z]', 'endpoint path'),
    (r'/api/[a-z][a-z0-9_/-]+', 'API path'),
    # C#/Java class names в обычном тексте
    (r'\b[A-Z][a-z]+(?:[A-Z][a-z]+){1,}\.(?:cs|java|kt|ts|tsx|py|rb|go)\b', 'class filename'),
    (r'\b[A-Z][a-zA-Z]+(?:Endpoints?|Service|Controller|Repository|Manager|Handler)\b', 'class name'),
    # Git команды
    (r'\bgit\s+(?:stash|push|pull|diff|merge|rebase|reset|checkout|branch)\b', 'git command'),
    # curl команды
    (r'\bcurl\s+(?:-X\s+)?(?:POST|GET|PUT|DELETE|PATCH)?\s*(?:http|/)', 'curl command'),
    # Cache buster (?v=N), file paths
    (r'\?v=\d+(?:→\d+)?', 'cache buster'),
    # Имена JS/CSS файлов inline
    (r'\b[a-z][a-z0-9-]+\.(?:js|css|tsx|ts)\b', 'JS/CSS filename'),
    # Параметры status=running и т.п.
    (r'\bstatus\s*[=:]\s*[\'"]?(?:running|stopped|paused|completed)', 'status keyword'),
    # SQL / DB термины в обычном тексте
    (r'\b(?:variants?|scheduler|controlHash|MVP|payload|endpoint|backend|frontend)\s+(?:exp|для|в|на)', 'DB/tech jargon'),
    # CSS specificity, query plan
    (r'\bCSS\s+specificity\b|\bquery\s+plan\b|\bEXPLAIN\s+ANALYZE\b', 'CSS/SQL low-level'),
    # «git stash» / «working tree»
    (r'\b(?:working\s+tree|незакоммиченные\s+изменения|stash|encrypt)\b', 'git/security tech'),
]


def is_real_user_text(text):
    if not text:
        return False
    t = text.strip()
    if not t:
        return False
    skip_prefixes = (
        '<task-notification>', '<system-reminder>', '<command-name>',
        '<command-message>', '<local-command-stdout>', '<bash-stdout>',
        'Stop hook feedback',
    )
    return not t.startswith(skip_prefixes)


def main():
    try:
        raw = sys.stdin.read() or '{}'
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    session_id = data.get('session_id') or ''
    if not session_id:
        sys.exit(0)

    transcript_path = os.path.join(TRANSCRIPT_DIR, f'{session_id}.jsonl')
    if not os.path.isfile(transcript_path):
        sys.exit(0)

    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:]
    except Exception:
        sys.exit(0)

    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    # Найти последний реальный user prompt
    last_user_idx = -1
    for i, e in enumerate(events):
        if e.get('type') != 'user' or 'toolUseResult' in e:
            continue
        msg = e.get('message') or {}
        c = msg.get('content')
        txt = ''
        if isinstance(c, str):
            txt = c
        elif isinstance(c, list):
            for item in c:
                if isinstance(item, dict) and item.get('type') == 'text':
                    txt = item.get('text', '') or ''
                    break
        if is_real_user_text(txt):
            last_user_idx = i

    if last_user_idx < 0:
        sys.exit(0)

    # Собрать последний assistant text после user prompt
    last_assistant_text = ''
    for d in events[last_user_idx + 1:]:
        if d.get('type') != 'assistant':
            continue
        content = (d.get('message') or {}).get('content') or []
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get('type') == 'text':
                t = (item.get('text') or '').strip()
                if t:
                    last_assistant_text = t  # последний text wins

    if not last_assistant_text:
        sys.exit(0)

    # Найти tech markers
    hits = []
    for pat, label in TECH_PATTERNS:
        matches = re.findall(pat, last_assistant_text)
        if matches:
            samples = list(set(str(m) for m in matches[:3]))[:3]
            hits.append((label, samples))

    if len(hits) < 2:
        # Один technical marker может быть в нормальном контексте, не дёргаем
        sys.exit(0)

    # Throttle — max 2 раза в session (не долбить если модель уже знает)
    if not _should_emit(session_id, 'tech-language-detector',
                        '|'.join(h[0] for h in hits), max_per_session=2):
        sys.exit(0)

    samples_str = '; '.join(f'{label}: {", ".join(samples)}' for label, samples in hits[:4])
    msg = (
        f'note: tech-language in last reply ({len(hits)} markers — {samples_str}). '
        'user is business-side, переформулируй в business-terms в следующем сообщении: '
        'не «POST /api/experiments/delete-variant», а «удалю те 2 тестовые позиции которые сегодня добавили». '
        'see wiki/concepts/talk-business-not-tech.md.'
    )

    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'Stop',
            'additionalContext': msg,
        },
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
