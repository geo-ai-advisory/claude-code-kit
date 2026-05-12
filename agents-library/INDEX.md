# Agents Library — каталог

23 универсальных субагента, разбитые по категориям. Используются на step 02 установки (`installer/02-shortlist-agents.md`).

## Core (6 — нужны почти всем)

| Agent | Зачем |
|---|---|
| [`core/web-researcher.md`](core/web-researcher.md) | Структурированный research через WebSearch + WebFetch — пишет отчёт в файл, в чат возвращает 5 строк summary |
| [`core/verifier.md`](core/verifier.md) | Pre-publication checks — ls путей, curl URL, sanity-query цифр |
| [`core/vault-reader.md`](core/vault-reader.md) | Read-only обход Obsidian-vault через graph MCP |
| [`core/vault-writer.md`](core/vault-writer.md) | Surgical patch_section на wiki-страницах (не overwrite) |
| [`core/journals-explorer.md`](core/journals-explorer.md) | Поиск прецедентов в `journals/` глубже 5 файлов |
| [`core/code-explorer.md`](core/code-explorer.md) | Grep + Read с offset/limit когда поиск >5 файлов или файлы >2000 строк |

## UI (3 — для тех кто строит UI)

| Agent | Зачем |
|---|---|
| [`ui/product-architect.md`](ui/product-architect.md) | 7+4 продуктовых вопросов ДО первой строки кода UI-задачи |
| [`ui/ui-design-architect.md`](ui/ui-design-architect.md) | Design-thinking про композицию конкретного экрана (mental model, иерархия, layout, референсы) — между brief и Edit |
| [`ui/ui-quality-reviewer.md`](ui/ui-quality-reviewer.md) | После Write/Edit *.html/*.css — review 6 категорий (типографика/spacing/color/states/responsive/animation) |

## Engineering (3 — для backend/frontend dev)

| Agent | Зачем |
|---|---|
| [`engineering/backend-code-reviewer.md`](engineering/backend-code-reviewer.md) | Review endpoints — security/N+1/correctness/auth gaps |
| [`engineering/database-schema-reviewer.md`](engineering/database-schema-reviewer.md) | Schema changes — FK с индексом, partial/composite, zero-downtime migrations |
| [`engineering/frontend-component-reviewer.md`](engineering/frontend-component-reviewer.md) | *.js > 500 lines — vanilla JS architecture, component boundaries |

## QA (3 — для всех кто отдаёт работу users)

| Agent | Зачем |
|---|---|
| [`qa/qa-scenario-tester.md`](qa/qa-scenario-tester.md) | Прогон ВСЕХ сценариев (multi-select, edge cases, partner-switching) до 100% PASS |
| [`qa/accessibility-auditor.md`](qa/accessibility-auditor.md) | WCAG 2.2 AA для кабинетов / форм пользователей |
| [`qa/api-contract-tester.md`](qa/api-contract-tester.md) | HTTP shape + edge cases — что endpoint возвращает при null/0/empty/expired auth |

## Product (3 — для product managers / heads of growth)

| Agent | Зачем |
|---|---|
| [`product/sprint-prioritizer.md`](product/sprint-prioritizer.md) | RICE / Value-Effort / Kano — цифры, не интуиция, когда «A vs B что важнее» |
| [`product/feedback-synthesizer.md`](product/feedback-synthesizer.md) | Telegram + Tracker + Usedesk → top-3 боли партнёров (input для sprint-prioritizer) |
| [`product/consistency-checker.md`](product/consistency-checker.md) | Числа / sum-detail / cross-section / wikilinks — для отчётов и dashboards |

## Memory (1)

| Agent | Зачем |
|---|---|
| [`memory/memory-consolidator.md`](memory/memory-consolidator.md) | Раз в 5-7 сессий — episodic (log.md) → semantic (wiki/concepts/*.md) transfer |

## Integrations (4 — опциональные, под конкретные сервисы)

| Agent | Зачем |
|---|---|
| [`integrations/gitlab-explorer.md`](integrations/gitlab-explorer.md) | GitLab API через MCP — list/get без скачивания diff'ов |
| [`integrations/telegram-summarizer.md`](integrations/telegram-summarizer.md) | Daily summary / mentions / search через Telegram MCP — аггрегаты, не сырые сообщения |
| [`integrations/sheets-reader.md`](integrations/sheets-reader.md) | Google Sheets через gdrive MCP с лимитами — структура + точечный read |
| [`integrations/tracker-explorer.md`](integrations/tracker-explorer.md) | Yandex Tracker MCP — issues / worklogs / users / queues |

## Как выбирать (cheat sheet для installer/02)

| User stack | Минимальный набор |
|---|---|
| Только UI/lendings | core/{web-researcher, verifier} + ui/* + qa/qa-scenario-tester + product/consistency-checker |
| Full-stack (backend + frontend) | core/* + ui/* + engineering/* + qa/* |
| Backend only (API server) | core/{web-researcher, verifier} + engineering/{backend-code-reviewer, database-schema-reviewer} + qa/api-contract-tester |
| Reports / analytics | core/{web-researcher, verifier} + product/consistency-checker + (опционально qa/qa-scenario-tester для интерактивных дашбордов) |
| Mobile (iOS/Android) | core/* + qa/qa-scenario-tester + qa/accessibility-auditor |
| Product / strategy | core/{web-researcher, journals-explorer} + product/* + memory/memory-consolidator |
| Communication / management | core/{web-researcher, journals-explorer} + integrations/{telegram, sheets, tracker} + memory/memory-consolidator |
