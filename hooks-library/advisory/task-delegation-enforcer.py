#!/usr/bin/env python3
"""
task-delegation-enforcer.py - PreToolUse Edit|Write hook.

Считает накопленные UI-edits после последнего user prompt. Если их много
БЕЗ Task(ui-quality-reviewer / qa-scenario-tester / accessibility-auditor /
ui-design-architect) — гарантирует что модель не игнорирует ревью.

Уровни:
  cumulative_ui_edits >= 5 AND ui_review_tasks == 0  → HARD NOTE (continue:false)
  cumulative_ui_edits >= 3 AND ui_review_tasks == 0  → loud hint (additionalContext)

Зачем: диагностика соседней сессии 64052142 показала 34 Edit'а на dashboard/wwwroot
без ни одного Task delegation. Модель видела hints, но игнорировала. Hard block
после 5 edit'ов гарантирует что после первого «всплеска» правок модель ОБЯЗАНА
вызвать subagent.

Pass G.3 / 2026-05-12.
"""

import sys
import json
import os
import re

TRANSCRIPT_DIR = (
    '/Users/<you>/.claude/projects/'
    '-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
)

# UI paths — те же что в brief-gate
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

UI_EXT_RE = re.compile(r'\.(html|css|scss|tsx|jsx|js)$', re.IGNORECASE)

# Subagent types которые считаются UI-ревью
UI_REVIEW_SUBAGENTS = {
    'ui-quality-reviewer',
    'qa-scenario-tester',
    'accessibility-auditor',
    'ui-design-architect',
    'product-architect',
    'frontend-component-reviewer',
}


def is_ui_path(path: str) -> bool:
    if not path:
        return False
    if not UI_EXT_RE.search(path):
        return False
    if any(s in path for s in SKIP_PATH_MARKERS):
        return False
    if not any(p in path for p in UI_PATH_MARKERS):
        return False
    # json и configs не считаем
    if path.endswith('.json'):
        return False
    return True


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
    )
    return not t.startswith(skip_prefixes)


def main() -> None:
    try:
        raw = sys.stdin.read() or '{}'
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_input = data.get('tool_input') or {}
    current_path = tool_input.get('file_path') or ''
    session_id = data.get('session_id') or ''

    # Только UI-files
    if not is_ui_path(current_path):
        sys.exit(0)

    if not session_id:
        sys.exit(0)

    transcript_path = os.path.join(TRANSCRIPT_DIR, f'{session_id}.jsonl')
    if not os.path.isfile(transcript_path):
        sys.exit(0)

    # Читаем tail — последние ~200 events чтобы поймать всю работу после user prompt
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-300:]
    except Exception:
        sys.exit(0)

    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    # Найти индекс последнего реального user prompt
    last_user_idx = -1
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

    if last_user_idx < 0:
        # Нет реального user prompt — это первая правка, пропускаем
        sys.exit(0)

    # Считаем после last_user_idx
    ui_edits = 0
    ui_review_tasks = 0
    edited_files_set = set()

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
            if item.get('type') != 'tool_use':
                continue
            name = item.get('name', '') or ''
            inp = item.get('input', {}) or {}
            if name in ('Edit', 'Write'):
                fp = inp.get('file_path') or ''
                if is_ui_path(fp):
                    ui_edits += 1
                    edited_files_set.add(fp)
            elif name == 'Task':
                sub = (inp.get('subagent_type') or '').lower()
                desc = (inp.get('description') or '').lower()
                prompt = (inp.get('prompt') or '')[:500].lower()
                if any(s in sub or s in desc or s in prompt
                       for s in UI_REVIEW_SUBAGENTS):
                    ui_review_tasks += 1
            elif name == 'Skill':
                sk = inp.get('skill') or ''
                if sk in ('check-scenarios', 'check-ui'):
                    ui_review_tasks += 1

    files_short = sorted(edited_files_set)[:5]
    files_str = '; '.join(os.path.basename(f) for f in files_short)

    # Pass K: user-override allowlist — пользователь явно даёт разрешение продолжать
    user_override_re = re.compile(
        r'(\bпродолжай\b|\bработай\b|\bделай\b|\bне\s+блокир|\bбез\s+(агентов|subagent|hooks?|хуков?|review)\b|'
        r'\bпрорывайся\b|\bпогнали\b|\bпоехали\b|\bпросто\s+делай\b|'
        r'\bне\s+спрашива|unblock|continue\s+as\s+is|фикс|hotfix|без\s+брифа)',
        re.IGNORECASE,
    )
    user_prompts_checked = 0
    user_override = False
    for line in lines[::-1]:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get('type') != 'user' or 'toolUseResult' in ev:
            continue
        msg = ev.get('message') or {}
        content = msg.get('content')
        text = ''
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get('type') == 'text':
                    text = c.get('text', '') or ''
                    break
        if not text or text.startswith(('<task-notification>', '<system-reminder>',
                                        '<command-name>', '<local-command-stdout>',
                                        '<bash-stdout>')):
            continue
        user_prompts_checked += 1
        if user_override_re.search(text):
            user_override = True
            break
        if user_prompts_checked >= 5:
            break

    # Pass K: strike-degrade — после 3 блоков переключаемся на hint
    block_strikes = sum(
        1 for line in lines
        if 'task-delegation-enforcer' in line and 'BLOCKED' in line
    )
    degraded = block_strikes >= 3

    # Pass L (2026-05-12): hook больше НЕ блокирует. Только hint после 5+ UI-edits.
    if ui_edits >= 5 and ui_review_tasks == 0:
        hint = (
            f"💡 RECOMMENDATION: {ui_edits} UI-Edit'ов без UI-review subagent.\n"
            f"Файлы: {files_str}\n\n"
            "Рекомендуется перед следующим крупным block правок вызвать:\n"
            "  Task(subagent_type='general-purpose', description='UI review', "
            f"prompt='ui-quality-reviewer для {files_str}')\n\n"
            "Это не блок — продолжай если уверен. Просто напоминание чтобы не пропустить ревью."
        )
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'additionalContext': hint
            }
        }, ensure_ascii=False))
        sys.exit(0)

    # Уровень 1: LOUD HINT после 3 UI-edits без UI-review
    if ui_edits >= 3 and ui_review_tasks == 0:
        hint = (
            f"⚠️ UI-REVIEW NEEDED: уже {ui_edits} UI-Edit'ов без subagent ревью.\n"
            f"Файлы: {files_str}\n"
            "Ещё 2 правки — и сработает soft hint.\n"
            "ВЫЗОВИ Task(ui-quality-reviewer) ИЛИ Task(qa-scenario-tester) СЕЙЧАС "
            "до следующего Edit. Не «прошёлся глазами», а реальный subagent через Task tool."
        )
        print(json.dumps({
            'systemMessage': hint,
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'additionalContext': hint
            }
        }, ensure_ascii=False))
        sys.exit(0)

    # Под порогом — тихо пропускаем
    sys.exit(0)


if __name__ == '__main__':
    main()
