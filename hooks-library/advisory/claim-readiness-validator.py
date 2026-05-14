#!/usr/bin/env python3
"""Stop hook — блокирует завершение сессии если модель пишет 'готово/работает/опубликовано'
без видимых тестовых кликов в transcript.

Логика:
  1. По session_id находит JSONL transcript.
  2. Находит последний реальный user message (не synthetic, не tool_result).
  3. Считает после него:
     - production-edits: Edit/Write на файлы в dashboard/wwwroot/HTML/JS/CSS
     - click-tests: browser_click / preview_click (любые варианты)
     - qa-agent invocations: Task с subagent_type qa-scenario-tester / ui-quality-reviewer
  4. Анализирует последний assistant text — содержит ли claim-фразу.

Условия блокирования:
  - edits >= 3 AND clicks == 0 AND qa == 0
  - ИЛИ claim-фраза в last assistant text AND clicks == 0 (даже при 1 edit'е)

Возвращает:
  - block decision JSON если нарушение
  - exit 0 в остальных случаях

Только Python stdlib. Быстрый — читает файл потоком, парсит JSONL построчно.
"""

# Global quiet kill switch — touch ~/claude-hooks/.quiet to silence ALL advisory hooks
import sys as _sys_q, os as _os_q
if _os_q.path.exists(_os_q.path.join(_os_q.path.dirname(_os_q.path.abspath(__file__)), '.quiet')):
    _sys_q.exit(0)

import sys
import json
import os
import re

# ---------- константы ----------

TRANSCRIPT_DIR = (
    '/Users/<you>/.claude/projects/'
    '-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
)

# Production-edit pattern: dashboard файлы, wwwroot, любые html/js/css
PROD_EDIT_PATTERNS = [
    re.compile(r'/Projects/<your-dashboard>/'),
    re.compile(r'/Projects/[^/]+/wwwroot/'),
    re.compile(r'/Projects/<your-tickets>/'),
    re.compile(r'\.html$'),
    re.compile(r'\.js$'),
    re.compile(r'\.css$'),
]

# Tool names считающиеся click-тестом
CLICK_TOOL_PATTERNS = [
    re.compile(r'^browser_click$'),
    re.compile(r'^preview_click$'),
    re.compile(r'^mcp__plugin_playwright_playwright__browser_click$'),
    re.compile(r'^mcp__playwright__browser_click$'),
    re.compile(r'^mcp__Claude_Preview__preview_click$'),
    # На всякий — любой *_click MCP tool (если появятся новые)
    re.compile(r'click$', re.IGNORECASE),
]

# QA subagent types
QA_SUBAGENTS = {'qa-scenario-tester', 'ui-quality-reviewer'}

# Claim-фразы в последнем assistant message (case-insensitive)
CLAIM_PATTERNS = [
    r'\bготово\b',
    r'\bработает\b',
    r'\bопубликовано\b',
    r'\bопубликована?\b',
    r'\bзадеплоен(?:о|а)?\b',
    r'\bпротестирован(?:о|а)?\b',
    r'\bвсё\s+ок\b',
    r'\bвсе\s+ок\b',
    r'\bвсё\s+на\s+месте\b',
    r'\bвсе\s+на\s+месте\b',
    r'\bвыкатил(?:а|и)?\b',
    r'\bвыкачено\b',
    r'\bзапушил(?:а|и)?\b',
    r'\bзапушено\b',
    r'\bpushed\b',
    r'\bdeployed\b',
    r'\bready\b',
    r'\bdone\b',
    r'\bпушнул(?:а|и)?\b',
]

CLAIM_RE = re.compile('|'.join(CLAIM_PATTERNS), re.IGNORECASE)


# ---------- helpers ----------

def is_real_user_text(text: str) -> bool:
    """Реальный user message vs synthetic-маркер."""
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


def matches_prod_edit(file_path: str) -> bool:
    if not file_path:
        return False
    for pat in PROD_EDIT_PATTERNS:
        if pat.search(file_path):
            return True
    return False


def matches_click(tool_name: str) -> bool:
    if not tool_name:
        return False
    # Чтобы не цеплять случайно `mcp__...something_click_thing` лишнее, проверяем
    # сначала точные имена, потом fallback на суффикс _click
    exact_names = {
        'browser_click',
        'preview_click',
        'mcp__plugin_playwright_playwright__browser_click',
        'mcp__playwright__browser_click',
        'mcp__Claude_Preview__preview_click',
        'mcp__Claude_in_Chrome__left_click',
        'mcp__computer-use__left_click',
        'mcp__computer-use__double_click',
        'mcp__computer-use__triple_click',
    }
    if tool_name in exact_names:
        return True
    # Любой *_click — считаем кликом
    if tool_name.endswith('_click') or tool_name.endswith('Click'):
        return True
    return False


def parse_transcript(transcript_path: str):
    """Стримом читает JSONL, возвращает список events (только нужные поля)."""
    events = []
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                events.append(d)
    except Exception:
        return []
    return events


def find_last_real_user_idx(events: list) -> int:
    """Индекс последнего реального user message. -1 если нет."""
    last = -1
    for i, d in enumerate(events):
        if d.get('type') != 'user':
            continue
        if 'toolUseResult' in d:
            continue
        if d.get('isSidechain'):
            continue
        msg = d.get('message') or {}
        content = msg.get('content')
        text = ''
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    parts.append(item.get('text') or '')
            text = '\n'.join(parts)
        if is_real_user_text(text):
            last = i
    return last


def analyse_after(events: list, start_idx: int):
    """Считает edits/clicks/qa в events после start_idx. Также возвращает last assistant text."""
    edits = 0
    clicks = 0
    qa = 0
    last_assistant_text = ''
    edited_files = []
    for d in events[start_idx + 1:]:
        if d.get('type') != 'assistant':
            continue
        msg = d.get('message') or {}
        content = msg.get('content') or []
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            t = item.get('type')
            if t == 'tool_use':
                name = item.get('name') or ''
                inp = item.get('input') or {}
                if name in ('Edit', 'Write'):
                    fp = inp.get('file_path') or inp.get('path') or ''
                    if matches_prod_edit(fp):
                        edits += 1
                        if len(edited_files) < 5:
                            edited_files.append(fp)
                elif matches_click(name):
                    clicks += 1
                elif name == 'Task':
                    sub = inp.get('subagent_type') or ''
                    if sub in QA_SUBAGENTS:
                        qa += 1
                elif name == 'Skill':
                    sk = inp.get('skill') or ''
                    if sk in ('check-scenarios', 'check-ui'):
                        qa += 1
            elif t == 'text':
                txt = item.get('text') or ''
                if txt.strip():
                    last_assistant_text = txt
    return edits, clicks, qa, last_assistant_text, edited_files


def build_block_reason(edits: int, clicks: int, qa: int, claim_phrase: str, edited_files: list) -> str:
    head = (
        '\U0001F6D1 РЕКОМЕНДАЦИЯ: claim '
        + (f"'{claim_phrase}' " if claim_phrase else '')
        + 'без видимых тестовых кликов в transcript. '
        f'Production edits: {edits}. Click tests: {clicks}. QA agent invocations: {qa}.'
    )
    body = (
        ' рекомендуется провести интеграционный тест: '
        '(1) browser_navigate на изменённую страницу, '
        '(2) browser_click на изменённый селектор, '
        '(3) browser_evaluate проверка нового state, '
        '(4) browser_resize 1280/1600 проверка адаптива. '
        'Альтернативно: вызвать qa-scenario-tester subagent. '
        'Только после теста заявлять что готово.'
    )
    if edited_files:
        body += ' Edited files (top 5): ' + '; '.join(edited_files)
    return head + body


# ---------- main ----------

def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or '{}')
    except Exception:
        data = {}

    session_id = data.get('session_id') or ''
    if not session_id:
        sys.exit(0)

    transcript_path = os.path.join(TRANSCRIPT_DIR, f'{session_id}.jsonl')
    if not os.path.isfile(transcript_path):
        sys.exit(0)

    events = parse_transcript(transcript_path)
    if not events:
        sys.exit(0)

    # Ограничиваем последними ~80 events чтобы не парсить мегабайты целиком —
    # но last user обычно близко к концу, так что окно с запасом
    if len(events) > 250:
        events = events[-250:]

    last_user_idx = find_last_real_user_idx(events)
    if last_user_idx < 0:
        sys.exit(0)

    edits, clicks, qa, last_text, edited_files = analyse_after(events, last_user_idx)

    # Условия блокирования (Pass G — усилены после диагностики соседней сессии 64052142:
    # 34 dashboard edits + 9 clicks (модель сама кликала) + 0 Task(qa-/ui-) = провал)
    block_reason = None

    # Условие 0 (E.4): ЛЮБОЙ Edit на dashboard/wwwroot/ без click = блок
    dashboard_edits = sum(
        1 for f in edited_files
        if any(p in f for p in ['/dashboard/wwwroot/', '/report/wwwroot/',
                                 '/landing', '/vitrina', '/experiments',
                                 '/showcase', '/wwwroot/static/'])
    )
    if dashboard_edits >= 1 and clicks == 0 and qa == 0:
        block_reason = build_block_reason(edits, clicks, qa,
                                          f'DASHBOARD EDIT ({dashboard_edits} files)',
                                          edited_files)

    # Условие 1 (старое): много edit'ов HTML/JS без клика и без QA
    elif edits >= 3 and clicks == 0 and qa == 0:
        block_reason = build_block_reason(edits, clicks, qa, '', edited_files)

    # Условие 2: claim-фраза + Edit без клика
    claim_match = CLAIM_RE.search(last_text or '')
    if claim_match and clicks == 0 and edits >= 1:
        block_reason = build_block_reason(edits, clicks, qa, claim_match.group(0), edited_files)

    # Условие 3 (Pass G, НОВОЕ): масштабная UI-работа без qa-subagent.
    # Соседняя сессия делала 34 edit'а с 9 кликами но 0 Task — модель «сама себе QA».
    # Если dashboard_edits >= 5 (масштаб) И qa == 0 (нет реального subagent) → block.
    # Игнорируем clicks потому что модель кликала сама без сценария.
    if block_reason is None and dashboard_edits >= 5 and qa == 0:
        block_reason = build_block_reason(
            edits, clicks, qa,
            f'MASS UI EDIT без qa-subagent ({dashboard_edits} dashboard files)',
            edited_files,
        )

    # Условие 4 (Pass G, НОВОЕ): claim-фраза + Edit на UI + 0 qa-subagent.
    # Самый явный сигнал «модель называет себя ui-quality-reviewer без вызова subagent».
    if (block_reason is None and claim_match
            and dashboard_edits >= 1 and qa == 0):
        block_reason = build_block_reason(
            edits, clicks, qa,
            f"{claim_match.group(0)} + DASHBOARD EDIT БЕЗ qa-subagent",
            edited_files,
        )

    if block_reason is None:
        sys.exit(0)

    # Pass L (2026-05-12): hook больше НЕ блокирует Stop.
    # Вместо decision:block — systemMessage + additionalContext (advisory).
    # Пользователь явно сказал «полный беспредел» — work не должна стоять.
    out = {
        'systemMessage': '💡 ' + block_reason,
        'hookSpecificOutput': {
            'hookEventName': 'Stop',
            'additionalContext': '💡 ' + block_reason,
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


if __name__ == '__main__':
    main()
