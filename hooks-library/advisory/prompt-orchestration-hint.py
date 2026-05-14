#!/usr/bin/env python3
"""UserPromptSubmit hook — orchestration hints для делегирования subagent'ам."""

# Global quiet kill switch — touch ~/claude-hooks/.quiet to silence ALL advisory hooks
import sys as _sys_q, os as _os_q
if _os_q.path.exists(_os_q.path.join(_os_q.path.dirname(_os_q.path.abspath(__file__)), '.quiet')):
    _sys_q.exit(0)

import sys
import json
import re

raw = sys.stdin.read()
try:
    data = json.loads(raw or '{}')
except Exception:
    data = {}
prompt = data.get('user_prompt') or data.get('prompt') or data.get('text') or ''
if not prompt:
    sys.exit(0)
rules = [
    # Жалоба на качество UI/UX — HARD-ABSOLUTE триггер на ПОЛНЫЙ pipeline (не быстрый fix)
    (r'(ублюдск|как\s+из\s+жопы|отвратительн|неинформативн|кривой\s+UI|кривой\s+блок|кривое|сырое|сырой|снова\s+не\s+работает|опять\s+ты|не\s+тестил|не\s+прогонял|не\s+вызывал.*агент|всё\s+ещё\s+кривой|зачем\s+этот\s+блок|для\s+чего\s+нужен|выполни\s+регламент|позови\s+всех\s+агентов|комплексно)', 'product-architect+ui-design-architect+qa-scenario-tester (ПОЛНЫЙ pipeline на жалобу качества — НЕ быстрый fix)'),
    # Pre-flight продуктовый бриф (высокий уровень) — ПЕРВЫЙ
    (r'((дашборд|dashboard|витрин|vitrina|лендинг|landing|А.Б|A.B|эксперимент|experiment|новый.раздел|новая.фича|спроектируй|задизайн|интерфейс|отчёт|отчет))', 'product-architect (рекомендуется ПЕРВЫЙ - 7 вопросов до Edit)'),
    # Screen-spec композиция конкретного экрана — СРАЗУ ПОСЛЕ product-architect
    (r'(лидерборд|leaderboard|scoreboard|ranking|таблица|table\b|виджет|визуализац|график\b|chart|экран\b|screen|mockup|mock\b|wireframe|компонент|layout|сетка|сравнен|комбинац|рейтинг|топ\s*\d|top\s*\d)', 'ui-design-architect (screen-spec, mental model, references)'),
    # Финальная проверка UI вёрстки после правки
    (r'(\.html|\.css|\.scss|\.tsx|\bui\b|\bвёрст|\bверст|шрифт|\bотступ|премиум|пропорц|UX)', 'ui-quality-reviewer'),
    # Доступность WCAG
    (r'(a11y|wcag|accessibility|доступн|screen.?reader|keyboard.{0,3}nav|клавиатур.{0,10}навигац|tab.{0,5}навигац|aria-|alt.text)', 'accessibility-auditor'),
    # Backend code review
    (r'(endpoint|Endpoints/|Controller|\.cs\b|N\+1|SQL.injection|auth.gap|UserStore)', 'backend-code-reviewer'),
    # Database schema / миграции
    (r'(миграц|migration|schema|\bindex\b|\bиндекс\b|\bFK\b|ExperimentDb|EXPLAIN.ANALYZE|zero.downtime)', 'database-schema-reviewer'),
    # Frontend vanilla JS
    (r'(\.js\b.*\b500\b|wwwroot/static|app\.js|cabinet\.js|compare\.js|state.management|store\b|vanilla.js|component\b)', 'frontend-component-reviewer'),
    # API contract testing
    (r'(curl.*localhost|api.*shape|http.*contract|api.*edge|api.*test|edge.case)', 'api-contract-tester'),
    # Приоритезация бэклога
    (r'(приорит|rice\b|\bice\b|sprint|спринт|что.важнее|backlog|бэклог|roadmap|kano|value.effort)', 'sprint-prioritizer'),
    # Feedback кластеризация
    (r'(фидбэк|feedback|что.просят.партнёр|боли.партнёр|жалоб|top.3.бол|кластериз)', 'feedback-synthesizer'),
    # Memory consolidation
    (r'(memory.consolidat|закрепи.факт|прокачай.vault|консолидац.*vault|memory.tier)', 'memory-consolidator'),
    # Существующие
    (r'(спарси|парс|резюме|hh\.ru|/hh\b)', 'hh-resume-reader'),
    (r'(<your-db>|выдач|статус\s*305|/report-mfo|/mfo-)', 'mfo-db-researcher'),
    (r'(vault|wiki/|second-brain|обнови.*стран)', 'vault-writer/vault-reader'),
    (r'(/gitlab_|gitlab.*репо)', 'gitlab-explorer'),
    (r'(прочитай.*стат|websearch|best\s*practic)', 'web-researcher'),
    (r'(/sb-ingest|raw/)', 'ingest-worker'),
    (r'(трекер|tracker|/tracker_)', 'tracker-explorer'),
    (r'(telegram|/morning|/telegram_daily)', 'telegram-summarizer'),
    (r'(gmail|почт)', 'gmail-triage'),
    (r'(google\s*sheet|gsheets|/mfo-month)', 'sheets-reader'),
]
hints = []
for pat, name in rules:
    if re.search(pat, prompt, re.IGNORECASE):
        hints.append(name)
if hints:
    uniq = list(dict.fromkeys(hints))
    msg = '[orchestration hint] subagents: ' + ', '.join(uniq)
    print(json.dumps({
        'systemMessage': msg,
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': msg
        }
    }, ensure_ascii=False))
