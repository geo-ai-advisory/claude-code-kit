# Installer step 02 — Shortlist agents

Цель: на основе scan-журнала (step 01) выбрать из `agents-library/` только те агенты которые реально нужны этому пользователю.

## Принципы отбора

1. **Соответствие стеку** — если нет backend C#/Python → нет смысла в `backend-code-reviewer`
2. **Соответствие типу задач** — если делает в основном bugfix а не новые фичи → `product-architect` не первый приоритет
3. **Соответствие болевым точкам** — если жаловался «делает не то что просил» → нужен `product-architect` + `ui-design-architect`
4. **Не больше 8-10 за раз** — больше создаёт шум в orchestration hints

## Маппинг стек → агенты

### Backend (любой)
- `agents-library/engineering/backend-code-reviewer.md` — security + N+1 + correctness review при правке endpoints
- `agents-library/qa/api-contract-tester.md` — HTTP shape testing для endpoints

### Backend + database
- `agents-library/engineering/database-schema-reviewer.md` — index safety, zero-downtime migrations

### Frontend (любой)
- `agents-library/ui/ui-quality-reviewer.md` — типографика/spacing/color review после Edit
- `agents-library/qa/qa-scenario-tester.md` — прогон всех сценариев перед отдачей

### Frontend vanilla JS / no framework
- `agents-library/engineering/frontend-component-reviewer.md` — component boundaries, state, copy-paste prevention

### UI/UX задачи (новые экраны, dashboards, лендинги, отчёты)
- `agents-library/ui/product-architect.md` — 7+4 продуктовых вопросов перед началом
- `agents-library/ui/ui-design-architect.md` — design-thinking про композицию конкретного экрана

### Партнёры / клиенты / multi-tenant
- `agents-library/qa/qa-scenario-tester.md` обязателен (для partner-switching test)

### Кабинеты / accessibility-критичные приложения
- `agents-library/qa/accessibility-auditor.md` — WCAG 2.2 AA для пользовательских кабинетов

### Reports / отчёты с цифрами
- `agents-library/product/consistency-checker.md` — sum-detail, cross-section проверки

### Product management / приоритезация
- `agents-library/product/sprint-prioritizer.md` — RICE/Value-Effort/Kano
- `agents-library/product/feedback-synthesizer.md` — кластеризация фидбэка партнёров → top-3 боли

### Любой workflow (всем рекомендуется)
- `agents-library/core/web-researcher.md` — заменяет голый WebSearch+WebFetch на структурированный отчёт
- `agents-library/core/vault-reader.md` + `vault-writer.md` — работа с Obsidian-vault
- `agents-library/core/verifier.md` — pre-publication checks
- `agents-library/memory/memory-consolidator.md` — episodic→semantic transfer раз в неделю

### Опциональные (под integrations пользователя)
- `agents-library/integrations/gitlab-explorer.md` — если GitLab
- `agents-library/integrations/telegram-summarizer.md` — если рабочие чаты в Telegram
- `agents-library/integrations/sheets-reader.md` — если Google Sheets workflow
- `agents-library/integrations/tracker-explorer.md` — если Yandex Tracker

## Процесс отбора

1. **Прочитай scan-журнал из step 01** — `~/claude-install-journal/<date>-scan.md`
2. **Сматчи стек с маппингом выше** — получишь первичный shortlist
3. **Покажи пользователю** — формат:

```markdown
На основе твоего стека (C# backend + vanilla JS frontend + Postgres + А/Б эксперименты) предлагаю установить 9 агентов:

### Engineering
- ✓ backend-code-reviewer — review C# endpoints
- ✓ database-schema-reviewer — Postgres миграции
- ✓ frontend-component-reviewer — vanilla JS архитектура

### UI/UX
- ✓ product-architect — 7 вопросов перед UI-задачами
- ✓ ui-design-architect — screen-spec для конкретных экранов
- ✓ ui-quality-reviewer — финальный review вёрстки

### QA
- ✓ qa-scenario-tester — все сценарии перед "готово"

### Core
- ✓ web-researcher — структурированный research
- ✓ memory-consolidator — еженедельная консолидация памяти

### НЕ предлагаю (не подходит твоему стеку):
- accessibility-auditor — нет user-facing кабинетов
- sprint-prioritizer — твоя команда small, бэклог простой
- feedback-synthesizer — нет внешних партнёров

Согласен? Или добавить/убрать?
```

4. **Дождись подтверждения**. Не ставь сам без `ок` пользователя.

## Установка

После подтверждения:

```bash
mkdir -p ~/.claude/agents
KIT_DIR="$(pwd)"  # папка claude-code-kit
for cat in core ui engineering qa product memory integrations; do
    for agent in <список подтверждённых пользователем>; do
        src="$KIT_DIR/agents-library/$cat/$agent.md"
        if [ -f "$src" ]; then
            cp "$src" ~/.claude/agents/
            echo "✓ installed: $agent"
        fi
    done
done
ls -la ~/.claude/agents/ | head
```

## Запиши в журнал

```bash
cat >> ~/claude-install-journal/<date>-scan.md <<EOF

## Installed agents (step 02)
<список 8-10 агентов с категориями>

## Отказались от:
<список с причинами>
EOF
```

После завершения — переходи к **step 03 — custom agents**.
