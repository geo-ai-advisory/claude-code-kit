#!/usr/bin/env python3
"""
brief-gate.py - PreToolUse Write|Edit hook.

Блокирует Edit/Write на UI файлах (dashboard, report, landing, vitrina,
experiments, showcase, wwwroot/static) если в текущей сессии нет
product brief'а (от product-architect subagent).

Зачем: иначе случается «правка на коленке вокруг неинформативных метрик» —
А/Б витрина потеряла часы из-за отсутствия brief'а.

Pass E.2 / 2026-05-12.
"""

# Global quiet kill switch — touch ~/claude-hooks/.quiet to silence ALL advisory hooks
import sys as _sys_q, os as _os_q
if _os_q.path.exists(_os_q.path.join(_os_q.path.dirname(_os_q.path.abspath(__file__)), '.quiet')):
    _sys_q.exit(0)


import sys
import json
import os
import re


UI_PATH_MARKERS = [
    '/dashboard/',
    '/report/wwwroot',
    '/landing',
    '/vitrina',
    '/experiments',
    '/showcase',
    '/wwwroot/static/',
    '/wwwroot/',
]

SKIP_PATH_MARKERS = [
    '/_archive/',
    '/node_modules/',
    '/dist/',
    '/.tmp/',
    '/build/',
    '/journals/',
    '/second-brain/wiki/',
    '/wiki/',
    '/.obsidian/',
]

# Расширения, считающиеся UI
UI_EXT_RE = re.compile(r'\.(html|css|scss|tsx|jsx|js)$', re.IGNORECASE)

# Расширения/имена, которые не считаем UI даже в UI-папках
NON_UI_FILES = [
    '.config.js',
    'package.json',
    'package-lock.json',
    'tsconfig.json',
    'data.json',
]


def is_non_ui_config(path: str) -> bool:
    """JSON и configs не считаются UI-новой работой."""
    if path.endswith('.json'):
        return True
    base = os.path.basename(path)
    for marker in NON_UI_FILES:
        if marker in base:
            return True
    return False


def main():
    try:
        raw = sys.stdin.read() or "{}"
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    session_id = data.get("session_id") or ""

    if not path:
        sys.exit(0)

    # 1. Расширение
    if not UI_EXT_RE.search(path):
        sys.exit(0)

    # 2. UI-папка
    if not any(p in path for p in UI_PATH_MARKERS):
        sys.exit(0)

    # 3. Skip archives/tmp/dist/journals/wiki
    if any(s in path for s in SKIP_PATH_MARKERS):
        sys.exit(0)

    # 4. JSON/configs не считаем
    if is_non_ui_config(path):
        sys.exit(0)

    # 5. Без session_id нечего проверять
    if not session_id:
        sys.exit(0)

    transcript_path = (
        f"/Users/<you>/.claude/projects/"
        f"-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>/"
        f"{session_id}.jsonl"
    )
    if not os.path.exists(transcript_path):
        # Новая сессия только что началась, transcript ещё не записан
        sys.exit(0)

    # 6. Читаем последние 80 events
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-80:]
    except Exception:
        sys.exit(0)

    file_edited_before = False
    brief_signals = 0
    screen_spec_signals = 0  # Pass I: ui-design-architect output

    brief_markers = [
        'product brief',
        'бриф записан',
        '# product brief',
        '## 1. что делаем',
        'ок брифу',
        'согласен бриф',
        'бриф ок',
        'brief approved',
        'утверждаю бриф',
    ]

    screen_spec_markers = [
        'screen-spec',
        'screen spec',
        'ок спеку',
        'утверждаю спек',
        'spec approved',
        '# screen-spec',
        'mental model',
        'layout grid',
    ]

    for line in lines:
        try:
            event = json.loads(line)
        except Exception:
            continue

        msg = event.get('message') or {}
        content = msg.get('content') or []
        if not isinstance(content, list):
            continue

        for c in content:
            if not isinstance(c, dict):
                continue

            ctype = c.get('type')

            # tool_use events
            if ctype == 'tool_use':
                tname = c.get('name', '') or ''
                tinput = c.get('input', {}) or {}
                if not isinstance(tinput, dict):
                    tinput = {}

                # Тот же файл уже редактировался в этой сессии — это продолжение
                if tname in ('Write', 'Edit'):
                    if tinput.get('file_path') == path:
                        file_edited_before = True

                # Task subagent с product-architect или ui-design-architect
                if tname == 'Task':
                    sub = (tinput.get('subagent_type', '') or '').lower()
                    desc = (tinput.get('description', '') or '').lower()
                    prompt = (tinput.get('prompt', '') or '')[:400].lower()
                    combo = sub + ' ' + desc + ' ' + prompt
                    if 'product-architect' in combo:
                        brief_signals += 1
                    if 'ui-design-architect' in combo:
                        screen_spec_signals += 1

                # Brief / screen-spec файл создан
                if tname in ('Write', 'Edit'):
                    fp = tinput.get('file_path', '') or ''
                    base = os.path.basename(fp)
                    if re.search(r'/journals/.*/brief-\d+\.md$', fp):
                        brief_signals += 1
                    elif 'brief-' in base and fp.endswith('.md'):
                        brief_signals += 1
                    if re.search(r'/journals/.*/screen-spec[-_]\w*\.md$', fp):
                        screen_spec_signals += 1
                    elif 'screen-spec' in base and fp.endswith('.md'):
                        screen_spec_signals += 1

            # Текстовые сообщения (assistant text / user message)
            if ctype == 'text':
                txt = (c.get('text', '') or '').lower()
                for marker in brief_markers:
                    if marker in txt:
                        brief_signals += 1
                        break
                for marker in screen_spec_markers:
                    if marker in txt:
                        screen_spec_signals += 1
                        break

            # User message может приходить как content без type=text
            if ctype is None:
                continue

    if file_edited_before:
        # Продолжение работы — не блокируем
        sys.exit(0)

    # Pass I: и brief И screen-spec нужны.
    if brief_signals > 0 and screen_spec_signals > 0:
        sys.exit(0)

    # Pass G+K (2026-05-12): fix-mode allowlist + strike degrade.
    # Расширенный regex чтобы пользователь мог снять блок естественными фразами,
    # не только «фикс». Соседняя сессия 64052142 встала на partner-picker.js на 10:37
    # потому что allowlist не покрывал «продолжай», «работай» etc.
    fix_mode_re = re.compile(
        r'(фикс|hotfix|small\s*fix|маленьк\w+\s*(fix|правк|hot)?|поправ|починк|небольш\w+\s*правк|'
        r'1\s*стро[ак]|2\s*стро[ак]|одну\s*строк|только\s*цвет|только\s*отступ|'
        r'fix\s*the|just\s*fix|fix\s*without\s*brief|без\s*брифа,?\s*ок|'
        r'\bпродолжай\b|\bработай\b|\bделай\b|\bделай\s+дальше\b|\bне\s+блокир|'
        r'\bбез\s+(брифа|спека|агентов|subagent|hooks?|хуков?)\b|'
        r'\bпрорывайся\b|\bпогнали\b|\bвперёд\b|\bвперед\b|\bпоехали\b|'
        r'\bпросто\s+(делай|сделай|правь|чини|пиши)\b|\bне\s+спрашива|'
        r'unblock|continue\s+as\s+is)',
        re.IGNORECASE,
    )

    fix_mode = False
    user_prompts_count = 0
    for line in lines[::-1]:  # с конца назад — последние user prompts
        try:
            event = json.loads(line)
        except Exception:
            continue
        if event.get('type') != 'user':
            continue
        if 'toolUseResult' in event:
            continue
        msg_e = event.get('message') or {}
        content = msg_e.get('content')
        text = ''
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    text = c.get('text', '') or ''
                    break
        # пропускаем synthetic
        if not text or text.startswith(('<task-notification>', '<system-reminder>',
                                        '<command-name>', '<local-command-stdout>',
                                        '<bash-stdout>')):
            continue
        user_prompts_count += 1
        if fix_mode_re.search(text):
            fix_mode = True
            break
        if user_prompts_count >= 5:
            # проверили 5 реальных prompts — fix-mode не объявлен
            break

    fname = os.path.basename(path)

    if fix_mode:
        # Мелкая правка — hint, не блок
        hint = (
            f"FIX-MODE для {fname}: пользователь объявил мелкую правку. "
            "Brief не требуется. Продолжай Edit, но СТРОГО держи scope — не делай "
            "рефакторинг соседнего кода (см. minimal-change-engineer pattern)."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": hint
            }
        }, ensure_ascii=False))
        sys.exit(0)

    # Pass K (2026-05-12): strike-degrade — если hook уже блокировал
    # 3+ раза в этой сессии (по tail transcript), переключаемся на hint
    # чтобы работа не вставала навсегда.
    block_strikes = 0
    for line in lines:
        if 'РЕКОМЕНДАЦИЯ: Edit на UI-файле' in line or 'BRIEF NEEDED' in line:
            block_strikes += 1
    degraded = block_strikes >= 3

    # Не fix-mode — HARD NOTE (или DEGRADED HINT после 3 strikes).
    # Pass I: проверяет brief И screen-spec отдельно.
    missing = []
    if brief_signals == 0:
        missing.append('BRIEF (product-architect output)')
    if screen_spec_signals == 0:
        missing.append('SCREEN-SPEC (ui-design-architect output)')
    missing_str = ' + '.join(missing)

    next_steps = []
    if brief_signals == 0:
        next_steps.append(
            "1. Task(subagent_type='general-purpose', description='product brief', "
            "prompt='следуй ~/.claude/agents/product-architect.md для текущей задачи')"
        )
    if screen_spec_signals == 0:
        idx = 2 if brief_signals == 0 else 1
        next_steps.append(
            f"{idx}. Task(subagent_type='general-purpose', description='UI screen-spec', "
            "prompt='следуй ~/.claude/agents/ui-design-architect.md — 7 design-thinking "
            "вопросов, WebFetch 2-3 референса из wiki/concepts/reference-platforms.md, "
            "screen-spec файл')"
        )
    next_idx = len(next_steps) + 1
    next_steps.append(f"{next_idx}. Отправить пользователю на approve")
    next_steps.append(f"{next_idx + 1}. После approve — продолжить Edit")
    next_steps_str = '\n'.join(next_steps)

    # Pass L (2026-05-12): hooks НЕ блокируют. Только hint.
    # Пользователь явно сказал «полный беспредел так работать нельзя» —
    # soft hints мешают работе. brief/screen-spec теперь рекомендация, не запрет.
    hint = (
        f"💡 RECOMMENDATION для UI-файла {fname}: рекомендуется brief + screen-spec.\n"
        f"Не хватает: {missing_str}\n\n"
        "Если новая фича / новый экран — лучше сначала:\n"
        f"{next_steps_str}\n\n"
        "Если мелкая правка / fix / продолжение работы — просто продолжай Edit, "
        "это не блок, просто напоминание."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": hint
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
