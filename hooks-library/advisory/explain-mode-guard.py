#!/usr/bin/env python3
"""
explain-mode-guard.py - PreToolUse Edit|Write|Bash hook.

Блокирует Edit/Write/Bash если последний user prompt — это вопрос-объяснение
(«что / зачем / почему / о чём / какой смысл / что значит / что это / what /
why / wtf») И ассистент ещё НЕ ответил текстом ≥ 150 chars на этот вопрос.

Зачем: диагностика соседней сессии 64052142 показала что когда пользователь
спрашивает «зачем эта полоса, о чём она говорит» — модель в режиме coding
cycle сразу бежит чинить вместо ответа. Результат — ярость пользователя.

Pass H / 2026-05-12.
"""

import sys
import json
import os
import re

TRANSCRIPT_DIR = (
    '/Users/<you>/.claude/projects/'
    '-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
)

# Паттерны вопроса-объяснения в user prompt
EXPLAIN_PATTERNS = [
    r'\bзачем\b',
    r'\bпочему\b',
    r'\bо\s+чём\b',
    r'\bо\s+чем\b',
    r'\bкакой\s+смысл\b',
    r'\bв\s+чём\s+смысл\b',
    r'\bчто\s+это\s*\??',
    r'\bчто\s+(значит|означает)\b',
    r'\bчто\s+за\b',
    r'\bчто\s+тут\b',
    r'\bкак\s+это\s+(работает|устроено)\b',
    r'\brazyasni\b',  # на всякий
    r'\bразъясни\b',
    r'\bобъясни\b',
    r'\bпоясни\b',
    r'\bwhy\b',
    r'\bwhat\s+is\b',
    r'\bwhat\s+does\b',
    r'\bwtf\b',
    r'\bwhat\s+the\b',
    r'\bhow\s+does\b',
    r'\bexplain\b',
    # Возмущение-вопрос (capslock + ?)
    r'(\?{1,3})\s*$',  # заканчивается на ?
]

EXPLAIN_RE = re.compile('|'.join(EXPLAIN_PATTERNS), re.IGNORECASE)

# Action keywords которые ОТМЕНЯЮТ explain-mode (пользователь явно просит действие)
ACTION_OVERRIDE = re.compile(
    r'(сделай|\bделай\b|исправь|почини|fix|поправь|переделай|перепиши|удали|добавь|'
    r'апдейт|update|обнови|deploy|push|закоммить|закомить|закомитить|'
    r'поправь.*и.*объясни|fix.*and.*explain|сначала.*потом|'
    r'давай\s+(делай|правь|чини|пиши)|погнали|вперёд|вперед|поехали|'
    r'просто\s+сделай|без\s+вопросов|молча\s+делай|на\s+основе|'
    r'не\s+спрашива|не\s+задавай\s+вопрос)',
    re.IGNORECASE,
)

# Минимальная длина ответа ассистента чтобы считать что он ответил
MIN_ASSISTANT_REPLY_CHARS = 150


def is_real_user_text(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    if not t:
        return False
    skip_prefixes = (
        '<task-notification>',
        '<system-reminder>',
        '<command-name>',
        '<command-message>',
        '<local-command-stdout>',
        '<bash-stdout>',
        'Stop hook feedback',
        '🛑',
    )
    return not t.startswith(skip_prefixes)


def main() -> None:
    try:
        raw = sys.stdin.read() or '{}'
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = data.get('tool_name') or ''
    session_id = data.get('session_id') or ''
    if not session_id:
        sys.exit(0)

    transcript_path = os.path.join(TRANSCRIPT_DIR, f'{session_id}.jsonl')
    if not os.path.isfile(transcript_path):
        sys.exit(0)

    # Читаем tail последних ~120 events чтобы охватить последний user prompt
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-200:]
    except Exception:
        sys.exit(0)

    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    # Найти последний реальный user prompt (его текст + индекс)
    last_user_idx = -1
    last_user_text = ''
    for i, e in enumerate(events):
        if e.get('type') != 'user':
            continue
        if 'toolUseResult' in e:
            continue
        msg = e.get('message') or {}
        content = msg.get('content')
        text = ''
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    text = c.get('text', '') or ''
                    break
        if is_real_user_text(text):
            last_user_idx = i
            last_user_text = text

    if last_user_idx < 0 or not last_user_text:
        sys.exit(0)

    # Проверка: explain-pattern есть?
    if not EXPLAIN_RE.search(last_user_text):
        sys.exit(0)

    # Override: пользователь явно попросил действие (несмотря на ?)
    if ACTION_OVERRIDE.search(last_user_text):
        sys.exit(0)

    # Посчитать assistant text после user prompt — ответил ли уже текстом
    assistant_reply_chars = 0
    for d in events[last_user_idx + 1:]:
        if d.get('type') != 'assistant':
            continue
        msg = d.get('message') or {}
        content = msg.get('content') or []
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get('type') == 'text':
                t = (item.get('text') or '').strip()
                if t:
                    assistant_reply_chars += len(t)

    if assistant_reply_chars >= MIN_ASSISTANT_REPLY_CHARS:
        # Уже ответил, можно действовать
        sys.exit(0)

    # Pass L: hook больше НЕ блокирует. Только hint.
    snippet = last_user_text[:200].replace('\n', ' ')
    hint = (
        f"💡 RECOMMENDATION ({tool_name}): пользователь задал вопрос-объяснение, "
        f"но ты ещё не ответил текстом (< {MIN_ASSISTANT_REPLY_CHARS} chars).\n\n"
        f"Вопрос: «{snippet}…»\n\n"
        "Рекомендуется СНАЧАЛА ответить текстом «что это / зачем / почему», "
        "а потом действовать. Если уже понимаешь что нужно делать — продолжай. "
        "Это не блок, просто напоминание."
    )

    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'additionalContext': hint
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
