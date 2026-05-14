#!/usr/bin/env python3
"""Stop hook — ловит когда модель перекладывает тестирование на пользователя.

Главный pattern который ловится:
  «Открой localhost:.../foo, нажми кнопку X, скажи работает или нет»
  «Проверь что Y работает»
  «Убедись что Z отрабатывает корректно»
  «Если что-то не так — скажи»

Это нарушение HARD-rule «Любая фича = автономный full-stack тест ДО готово».
Модель ОБЯЗАНА сама прокликать через browser_navigate + browser_click +
browser_evaluate (или preview_*), а не просить пользователя.

Throttle: только первый раз в сессии. После повтора — silent (агент уже
получил hint, дальше его дело).

Pass M / 2026-05-13.
"""

import sys
import json
import os
import re

# Throttle utility
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _throttle import should_emit as _should_emit
except Exception:
    def _should_emit(*a, **kw):
        return True


# Фразы которыми модель перекладывает тестирование
DELEGATION_PATTERNS = [
    # Прямые императивы пользователю
    r'\bоткрой\s+(localhost|http)',
    r'\bнажми\s+(на\s+)?(кнопк|button)',
    r'\bкликни\s+на\b',
    r'\bпроверь\s+(что|как|работает)',
    r'\bубедись\s+что\b',
    r'\bскажи\s+(работает|если)',
    r'\bпопробуй\s+(нажать|кликнуть|открыть)',
    r'\bтестируй\s+(сам|у себя)',
    # English equivalents
    r'\bopen\s+(localhost|http)',
    r'\bclick\s+(the\s+)?button',
    r'\bcheck\s+if\s+it\s+works',
    r'\btry\s+(clicking|opening)',
    r'\blet\s+me\s+know\s+if\b',
    # Условные «если что — скажи»
    r'если\s+что-то\s+(не\s+так|не\s+работает|кривое|сломано)',
    r'если\s+(где|что-то)\s+ещё\s+кривое',
    # Soft delegation
    r'дай\s+знать\s+(если|когда)',
    r'жду\s+(твоего\s+)?(ответа|подтверждения|проверки)',
]

DELEGATION_RE = re.compile('|'.join(DELEGATION_PATTERNS), re.IGNORECASE)

# НЕ срабатывает если модель сама уже тестировала (в transcript есть browser_*)
# Это значит — она проверила и **дополнительно** просит пользователя финальный sanity
SELF_TEST_TOOLS = (
    'mcp__playwright__browser_navigate',
    'mcp__playwright__browser_click',
    'mcp__playwright__browser_evaluate',
    'mcp__Claude_Preview__preview_start',
    'mcp__Claude_Preview__preview_click',
    'mcp__Claude_Preview__preview_eval',
    'browser_navigate', 'browser_click', 'browser_evaluate',
    'preview_start', 'preview_click', 'preview_eval',
)

TRANSCRIPT_DIR = (
    '/Users/<you>/.claude/projects/'
    '-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
)


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

    # Tail последних 100 events
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-150:]
    except Exception:
        sys.exit(0)

    # Найти последний реальный user prompt
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            continue

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
        if txt and not txt.startswith(('<task-notification>', '<system-reminder>',
                                       '<command-name>', '<local-command-stdout>',
                                       '<bash-stdout>')):
            last_user_idx = i

    if last_user_idx < 0:
        sys.exit(0)

    # Собираем после user prompt: assistant texts + tool calls
    assistant_text_combined = []
    browser_test_calls = 0
    for d in events[last_user_idx + 1:]:
        if d.get('type') != 'assistant':
            continue
        content = (d.get('message') or {}).get('content') or []
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            t = item.get('type')
            if t == 'text':
                txt = item.get('text') or ''
                if txt.strip():
                    assistant_text_combined.append(txt)
            elif t == 'tool_use':
                name = item.get('name', '') or ''
                if any(s in name for s in SELF_TEST_TOOLS):
                    browser_test_calls += 1

    if not assistant_text_combined:
        sys.exit(0)

    combined_text = '\n'.join(assistant_text_combined[-3:])  # последние 3 reply

    # Ищем delegation phrases
    matches = DELEGATION_RE.findall(combined_text)
    if not matches:
        sys.exit(0)

    # Если модель уже сделала >= 3 browser_test calls — она тестировала сама.
    # Тогда «попробуй ещё у себя» это OK, не delegation. Пропускаем.
    if browser_test_calls >= 3:
        sys.exit(0)

    # Throttle — выдадим только первые 2 раза в сессии
    if not _should_emit(session_id, 'delegation-to-user-detector',
                        'delegation-pattern', max_per_session=2):
        sys.exit(0)

    # Build hint
    snippet = combined_text[:300].replace('\n', ' ')
    examples = list(set(m if isinstance(m, str) else m[0] for m in matches[:5]))[:5]

    msg = (
        '🚨 DELEGATION TO USER DETECTED — ты перекладываешь тестирование на пользователя.\n\n'
        f'Найдены фразы: {", ".join(repr(e) for e in examples)}\n'
        f'Browser-test calls в этом turn: {browser_test_calls} (нужно ≥ 3 для PASS)\n\n'
        'НАРУШЕНИЕ HARD-rule «Любая фича = автономный full-stack тест ДО готово».\n\n'
        'ОБЯЗАН СЕЙЧАС:\n'
        '1. Сам прокликать через browser_navigate + browser_click на упомянутые селекторы\n'
        '2. browser_evaluate проверить что после клика state изменился как обещано\n'
        '3. browser_resize 1280/1600 проверить адаптив\n'
        '4. Если хоть что-то FAIL — сам починить + re-test\n'
        '5. Только потом сообщать «готово к деплою» с показом скриншота / результата\n\n'
        'Запрещённые фразы (НЕ писать пользователю):\n'
        '  • «открой localhost:.../, нажми кнопку, скажи работает или нет»\n'
        '  • «проверь что Y работает»\n'
        '  • «убедись что Z отрабатывает»\n'
        '  • «если что-то ещё кривое — скажи»\n'
        '  • «попробуй у себя»\n\n'
        'Это работа агента, не пользователя. Реакция пользователя на такие фразы: '
        '«мразище не тестирует нихуя».'
    )

    out = {
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'Stop',
            'additionalContext': msg,
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
