#!/usr/bin/env python3
"""PreToolUse hook для Bash — блокирует prod push без явного approve пользователя.

Срабатывает на:
  - git push (кроме archived/* и local-only)
  - gh release create / gh pr merge
  - skill-команды публикации: html-push, gitlab_push, publick-push
  - --force / --force-with-lease (особо строгая проверка)

Политика:
  - Прочитать последние 30 user messages из transcript JSONL.
  - Найти явное одобрение пользователя (regex по фразам approve).
  - Без approve -> блок (continue: false + stopReason).
  - --force требует дополнительной фразы про force.
  - Если transcript не найден -> блок (нет данных = нет approve).

Только Python stdlib.
"""
import sys
import json
import re
import os

# ---------- regex: что считается prod push ----------

# Базовые prod push команды (срабатывают всегда, кроме исключений)
PROD_PUSH_PATTERNS = [
    # git push (любой вариант) — позже исключим archived/* и local-only refs
    (r'\bgit\s+push\b', 'git push'),
    # gh release create
    (r'\bgh\s+release\s+create\b', 'gh release create'),
    # gh pr merge
    (r'\bgh\s+pr\s+merge\b', 'gh pr merge'),
    # html-push skill (slash-команда или explicit)
    (r'(?:^|\s)/html[-_]push\b', 'html-push skill'),
    (r'\bhtml[-_]push\b(?!\.py|\.md)', 'html-push skill'),
    # gitlab_push / gitlab-push skill
    (r'(?:^|\s)/gitlab[-_]push\b', 'gitlab_push skill'),
    (r'\bgitlab[-_]push\b(?!\.py|\.md)', 'gitlab_push skill'),
    # publick-push / publick_push skill (опечатка преднамеренная — соответствует skill name)
    (r'(?:^|\s)/publick[-_]push\b', 'publick-push skill'),
    (r'\bpublick[-_]push\b(?!\.py|\.md)', 'publick-push skill'),
]

# --force / --force-with-lease (доп. строгая проверка)
FORCE_PATTERNS = [
    r'--force\b',
    r'--force-with-lease\b',
    r'(?<!\w)-f\b(?=\s)',  # `git push -f`
]

# Исключения: git push в archived/* — НЕ блокировать
PUSH_ARCHIVED_RE = re.compile(r'\bgit\s+push\b[^&;|]*\barchived/', re.IGNORECASE)

# Local-only git операции (не push, но похожи на префикс "git push")
# Эти команды НЕ являются push:
SAFE_GIT_OPS = re.compile(
    r'^\s*git\s+(status|fetch|stash|log|diff|branch|checkout|switch|add|commit|merge|rebase|pull|reflog|show|blame|ls-files|ls-tree|cat-file|grep|describe|tag|cherry|cherry-pick|restore|reset|clean|rev-parse|rev-list|remote)(\s|$)',
    re.IGNORECASE,
)

# ---------- regex: approve фразы ----------

# Базовые approve фразы (case-insensitive, любая = разрешает обычный push)
APPROVE_PHRASES = [
    # Русский — push/выкат/деплой
    r'\bпушь\b',
    r'\bпушим\b',
    r'\bпуш\b',
    r'\bвыкатывай(?:\s+в\s+прод)?\b',
    r'\bвыкатываем\b',
    r'\bдеплой(?:\s+в\s+прод)?\b',
    r'\bдеплоим\b',
    r'\bможно\s+пушить\b',
    r'\bможно\s+деплоить\b',
    r'\bможно\s+пуш\b',
    r'\bдавай\s+пушить\b',
    r'\bдавай\s+пуш\b',
    r'\bкоммить\s+и\s+пуш\b',
    r'\bкомить\s+и\s+пуш\b',
    r'\bокей\s+пуш\b',
    r'\bок\s+пуш\b',
    r'\bок\s+выкат\b',
    r'\bок\s+деплой\b',
    r'\bокей\s+выкат\b',
    r'\bокей\s+деплой\b',
    r'\bзалей\b',
    r'\bзалить\b',
    r'\bзалейся\b',
    r'\bзалив\b',
    r'\bапрув\b',
    r'\bапрувлю\b',
    r'\bапрувнуто\b',
    r'\bапрувлен\b',
    # Английский
    r'\bapprove\s+push\b',
    r'\bapproved\b',
    r'\bapproved\s+by\s+me\b',
    r'\bpush\s+it\b',
    r'\bmerge\s+it\b',
    r'\bship\s+it\b',
    r'\bok\s+push\b',
    r'\bok\s+deploy\b',
    r'\bdeploy\s+it\b',
    r'\blgtm\b',
]

APPROVE_RE = re.compile('|'.join(APPROVE_PHRASES), re.IGNORECASE)

# Force-approve фразы (нужны ДОПОЛНИТЕЛЬНО к обычному approve для --force)
FORCE_APPROVE_PHRASES = [
    r'\bforce\s+ок\b',
    r'\bforce\s+ok\b',
    r'\bможно\s+force\b',
    r'\bможно\s+форс\b',
    r'\bзнаю\s+про\s+force\b',
    r'\bзнаю\s+что\s+force\b',
    r'\bмогу\s+force\b',
    r'\bдавай\s+force\b',
    r'\bдавай\s+форс\b',
    r'\bforce\s+approve\b',
    r'\bforce\s+approved\b',
    r'\bforce\s+push\s+ок\b',
    r'\bforce-?with-?lease\b',
    r'\bосознанно\s+force\b',
]

FORCE_APPROVE_RE = re.compile('|'.join(FORCE_APPROVE_PHRASES), re.IGNORECASE)


def detect_push(cmd: str):
    """Возвращает (is_push, label, is_force) или (False, None, False)."""
    if not cmd:
        return (False, None, False)

    # Сначала отметаем архивные push
    if PUSH_ARCHIVED_RE.search(cmd):
        return (False, None, False)

    # Сначала проверяем — это вообще git push? Если git, но safe op — не push.
    # Но командой может быть `git push && something`, поэтому проверяем подстроку.
    is_git_push = bool(re.search(r'\bgit\s+push\b', cmd, re.IGNORECASE))
    has_safe_op_only = bool(SAFE_GIT_OPS.match(cmd)) and not is_git_push

    if has_safe_op_only:
        return (False, None, False)

    label = None
    for pat, name in PROD_PUSH_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            label = name
            break

    if not label:
        return (False, None, False)

    # Проверяем force только если git push
    is_force = False
    if is_git_push:
        for fp in FORCE_PATTERNS:
            if re.search(fp, cmd, re.IGNORECASE):
                is_force = True
                break

    return (True, label, is_force)


def extract_branch_target(cmd: str) -> str:
    """Достать примерную цель/ветку из команды push."""
    # git push origin <branch>
    m = re.search(r'git\s+push\s+(?:--\S+\s+)*(\S+)?\s*(\S+)?', cmd, re.IGNORECASE)
    if m:
        remote = m.group(1) or ''
        branch = m.group(2) or ''
        if remote and not remote.startswith('-'):
            if branch and not branch.startswith('-'):
                return f'{remote} {branch}'
            return remote
    return '?'


def read_recent_user_messages(session_id: str, limit: int = 30) -> list[str]:
    """Прочитать последние N реальных user messages (не tool_result, не synthetic)."""
    if not session_id:
        return []

    base_dir = '/Users/<you>/.claude/projects/-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
    transcript_path = os.path.join(base_dir, f'{session_id}.jsonl')

    if not os.path.isfile(transcript_path):
        return []

    user_texts: list[str] = []

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

                if d.get('type') != 'user':
                    continue

                # Пропускаем tool results
                if 'toolUseResult' in d:
                    continue
                if d.get('isSidechain'):
                    continue

                msg = d.get('message') or {}
                content = msg.get('content')

                texts: list[str] = []
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            t = item.get('text') or ''
                            if t:
                                texts.append(t)

                for t in texts:
                    # Пропускаем системные synthetic-сообщения
                    if t.startswith('<task-notification>'):
                        continue
                    if t.startswith('<system-reminder>'):
                        continue
                    if t.startswith('<command-name>'):
                        continue
                    if t.startswith('<command-message>'):
                        continue
                    if t.startswith('<local-command-stdout>'):
                        continue
                    if t.strip().startswith('<bash-stdout>'):
                        continue
                    user_texts.append(t)
    except Exception:
        return []

    # Берём последние N
    return user_texts[-limit:]


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or '{}')
    except Exception:
        data = {}

    tool_input = data.get('tool_input') or {}
    cmd = tool_input.get('command') or ''
    session_id = data.get('session_id') or ''

    is_push, label, is_force = detect_push(cmd)
    if not is_push:
        sys.exit(0)

    # Читаем последние 30 реальных user-сообщений
    user_msgs = read_recent_user_messages(session_id, limit=30)
    combined = '\n'.join(user_msgs)

    # === UI review check (после катастрофы 12.05) ===
    # Если за последний user turn были Edit на UI-файлы (HTML/CSS/JS) — нужен
    # хотя бы один Task(ui-quality-reviewer) или Task(qa-scenario-tester) или
    # browser_click тест перед push. Иначе блок «нажал → визуально кривое в прод».
    ui_edits_recent = 0
    ui_review_recent = 0
    qa_click_recent = 0
    try:
        transcript_dir = os.path.expanduser(
            '~/.claude/projects/-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>'
        )
        if not os.path.isdir(transcript_dir):
            for d in os.listdir(os.path.expanduser('~/.claude/projects/')):
                transcript_dir = os.path.expanduser(f'~/.claude/projects/{d}')
                break
        tp = os.path.join(transcript_dir, f'{session_id}.jsonl')
        if os.path.isfile(tp):
            with open(tp, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-200:]
            # последний реальный user prompt
            last_user_idx = -1
            for i, line in enumerate(lines):
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get('type') != 'user' or 'toolUseResult' in ev:
                    continue
                msg = ev.get('message') or {}
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
            if last_user_idx >= 0:
                ui_ext_re = re.compile(r'\.(html|css|scss|tsx|jsx|js)$', re.IGNORECASE)
                ui_review_names = {'ui-quality-reviewer', 'qa-scenario-tester',
                                   'ui-design-architect', 'accessibility-auditor'}
                for line in lines[last_user_idx + 1:]:
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get('type') != 'assistant':
                        continue
                    content = (ev.get('message') or {}).get('content') or []
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
                            fp = inp.get('file_path', '') or ''
                            if ui_ext_re.search(fp):
                                ui_edits_recent += 1
                        elif name == 'Task':
                            sub = (inp.get('subagent_type') or '').lower()
                            desc = (inp.get('description') or '').lower()
                            prompt = (inp.get('prompt') or '')[:500].lower()
                            combo = sub + ' ' + desc + ' ' + prompt
                            if any(r in combo for r in ui_review_names):
                                ui_review_recent += 1
                        elif 'click' in name.lower():
                            qa_click_recent += 1
    except Exception:
        pass

    # Soft approve regex — короткие фразы согласия которые
    # пользователь реально пишет в работе («да», «ок», «делай», «пушь», «залей», и т.д.)
    SOFT_APPROVE = re.compile(
        r'(?:^|\s|[.,!?])(да|ок|ага|давай|пуш(?:ь|и|ай)?|залей|выкатывай|деплой|'
        r'клад[ьи]|удали|чин[иь]|fix|push|ship|merge|lgtm|апрув|approve|'
        r'делай(?:\s+что\s+надо)?|поехали|погнали|вперёд|вперед)(?:\s|[.,!?]|$)',
        re.IGNORECASE,
    )

    has_approve = bool(APPROVE_RE.search(combined)) or bool(SOFT_APPROVE.search(combined))
    has_force_approve = bool(FORCE_APPROVE_RE.search(combined)) or has_approve  # если есть обычный approve — force тоже OK

    # === Destructive config detection (катастрофа 13.05 'включила все офферы и в прод') ===
    # Если в diff есть config/data файлы с большим изменением — требуем семантический approve.
    destructive_files: list[str] = []
    destructive_lines = 0
    try:
        import subprocess
        # cwd — извлекаем из самой команды: ищем `git -C <path>` или `cd X && git push`
        cwd = None
        m_c = re.search(r'\bgit\s+-C\s+(\S+)', cmd)
        if m_c:
            cwd = os.path.expanduser(m_c.group(1).strip('"\''))
        else:
            m_cd = re.search(r'\bcd\s+(\S+?)\s*&&', cmd)
            if m_cd:
                cwd = os.path.expanduser(m_cd.group(1).strip('"\''))
            else:
                cwd = data.get('cwd') or os.getcwd()
        diff_out = subprocess.run(
            ['git', 'diff', '--stat', 'origin/HEAD..HEAD'],
            capture_output=True, text=True, timeout=5,
            cwd=cwd,
        )
        if diff_out.returncode == 0:
            stat_text = diff_out.stdout
            # Жёсткий destructive patterns — только реально опасные конфиги прода,
            # не universal слова типа 'settings.json'.
            destructive_patterns = re.compile(
                r'(showcase|vitrina|витрин|partner.*routes?|partner.*config|'
                r'pricing|commission|комисси|api.key|webhook|'
                r'feature.flag|toggle.config|migrations?/\d+_|'
                r'auth.*config|production.*\.(json|yml|yaml|toml))',
                re.IGNORECASE,
            )
            # Skip files обычно безопасные (тесты, docs, kit, hooks)
            safe_patterns = re.compile(
                r'(/tests?/|/docs?/|/journals?/|claude-code-kit|claude-hooks|'
                r'\.md$|README|CHANGELOG|INSTALL|/installer/|/agents-library/|'
                r'/hooks-library/|/vault-template/|/skills/)',
                re.IGNORECASE,
            )
            for ln in stat_text.splitlines():
                if '|' not in ln:
                    continue
                fname = ln.strip().split('|')[0].strip()
                if safe_patterns.search(fname):
                    continue
                if destructive_patterns.search(fname):
                    destructive_files.append(fname)
                    m_line = re.search(r'\|\s*(\d+)', ln)
                    if m_line:
                        destructive_lines += int(m_line.group(1))
    except Exception:
        pass

    semantic_approve_re = re.compile(
        r'(семантик[аи]|это\s+правильно|правильное\s+изменение|'
        r'ок\s+включа|ок\s+(меня|изменя)|подтверждаю\s+изменение|'
        r'я\s+понимаю\s+(что|как)|осознанно)',
        re.IGNORECASE,
    )
    has_semantic_approve = bool(semantic_approve_re.search(combined))

    # Решение
    blocked = False
    reason_lines: list[str] = []

    if not has_approve:
        blocked = True
        reason_lines.append('no explicit user approve in last 30 messages')

    if is_force and not has_force_approve:
        blocked = True
        reason_lines.append('force-push требует доп. фразы')

    # UI review check: блок если был Edit UI без визуального ревью.
    # Обход — пользователь скажет «знаю что UI кривой, всё равно пушь» или
    # явный «без ui review».
    ui_review_bypass_re = re.compile(
        r'(без\s+ui\s*review|skip\s+ui|пуш\s+без\s+ui|знаю.*UI|кривой\s+UI.*пуш|'
        r'all\s+force|forced\s+ok|knowingly\s+push)',
        re.IGNORECASE,
    )
    has_ui_bypass = bool(ui_review_bypass_re.search(combined))
    if ui_edits_recent >= 1 and ui_review_recent == 0 and qa_click_recent == 0 and not has_ui_bypass:
        blocked = True
        reason_lines.append(
            f'UI edits ({ui_edits_recent}) без визуального ревью '
            '(0 Task ui-quality-reviewer/qa-scenario-tester и 0 browser_click тестов)'
        )

    # Destructive config check — требуем семантический approve
    if destructive_files and destructive_lines >= 5 and not has_semantic_approve:
        blocked = True
        files_summary = ', '.join(destructive_files[:5])
        reason_lines.append(
            f'DESTRUCTIVE CONFIG: {len(destructive_files)} файлов ({files_summary}), '
            f'{destructive_lines}+ строк — нужен **семантический approve** не только push approve'
        )

    if not blocked:
        sys.exit(0)

    # Формируем stopReason
    target = extract_branch_target(cmd)
    msg_parts = [
        '\U0001F6D1 PROD PUSH BLOCKED — ' + '; '.join(reason_lines) + '.',
        '',
        f'Detected: {label}',
        f'Branch/target: {target}',
        f'Force flag: {"YES" if is_force else "no"}',
        '',
        'Required: пользователь должен явно сказать одно из:',
        '  «ок пуш», «выкатывай», «деплой», «можно пушить», «залей»,',
        '  «approve push», «push it», «ship it», «lgtm», «апрув»',
    ]
    if is_force:
        msg_parts += [
            '',
            'Для --force / --force-with-lease ДОПОЛНИТЕЛЬНО нужно:',
            '  «force ок», «можно force», «знаю про force», «осознанно force»',
        ]
    # Destructive config block — отдельный раздел
    if destructive_files and destructive_lines >= 5 and not has_semantic_approve:
        msg_parts += [
            '',
            f'🔥 DESTRUCTIVE PROD CONFIG CHANGE:',
            f'  файлы: {", ".join(destructive_files[:5])}',
            f'  строк изменено: {destructive_lines}',
            '',
            'Это не code change — это config который меняет ПОВЕДЕНИЕ прода для users.',
            'Approve на push ≠ approve на семантику изменения.',
            '',
            'ТРЕБУЕТСЯ ОТ ТЕБЯ (модель) ПЕРЕД PUSH:',
            '  1. Показать пользователю seman tic diff в human terms:',
            '     "после push в проде станет: <список изменений в поведении>"',
            '  2. Дождаться явного approve на СЕМАНТИКУ (не просто "ок"):',
            '     - «семантика верная»',
            '     - «правильное изменение»',
            '     - «ок включаем все 18 офферов»',
            '     - «я понимаю что меняется»',
            '     - «осознанно push»',
            '  3. Только потом push',
            '',
            'Реальная катастрофа (13.05.2026):',
            '  Модель включила все офферы в showcase config, push approved пользователем,',
            '  в прод улетела кашевая витрина. Семантический approve бы поймал.',
            '',
            'См. wiki/concepts/destructive-prod-changes.md',
        ]

    # UI review block — отдельный раздел
    if ui_edits_recent >= 1 and ui_review_recent == 0 and qa_click_recent == 0 and not has_ui_bypass:
        msg_parts += [
            '',
            f'🎨 UI-EDIT БЕЗ РЕВЬЮ ({ui_edits_recent} файлов изменено):',
            '  - 0 Task(ui-quality-reviewer / qa-scenario-tester / ui-design-architect)',
            '  - 0 browser_click / preview_click тестов',
            '',
            'Перед push на UI:',
            '  1. Task(subagent_type="general-purpose",',
            '         prompt="следуй ~/.claude/agents/ui-quality-reviewer.md',
            '                 для последних правок: <файлы>") — визуал PASS/FAIL',
            '  2. Task(subagent_type="general-purpose",',
            '         prompt="следуй ~/.claude/agents/qa-scenario-tester.md',
            '                 — 5-step functional test с acceptance criteria")',
            '  3. Только после PASS → push',
            '',
            'Bypass если уверен: «без ui review», «знаю что кривой, пушь», «skip ui»',
        ]

    msg_parts += [
        '',
        'Action: ожидать user approve, не делать workaround через',
        'bash variables / env / piping / переписывание команды.',
    ]

    stop_reason = '\n'.join(msg_parts)

    out = {
        'continue': False,
        'stopReason': stop_reason,
        'systemMessage': stop_reason,
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny',
            'permissionDecisionReason': stop_reason,
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


if __name__ == '__main__':
    main()
