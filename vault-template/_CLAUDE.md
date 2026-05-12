# Vault Operating Manual

Этот файл — operating manual именно для wiki vault'а в `Projects/<your-vault>/`. Не дублирует корневой `CLAUDE.md` (поведение Claude) и не дублирует `Projects/<x>/CLAUDE.md` (узкие правила проектов).

## Структура

```
Projects/<your-vault>/
  _CLAUDE.md            <- этот файл
  _index.md             <- стартовая страница, граф
  CRITICAL_FACTS.md     <- грузится в каждую сессию
  log.md                <- append-only лог сессий
  raw/                  <- сырые материалы перед канонизацией
  wiki/
    projects/           <- по одному файлу на проект из Projects/
    partners/           <- <industry>, банки, ритейл, CPA-сети
    people/             <- сотрудники <YourCompany> + внешние контакты + сам Geo
    concepts/           <- продуктовые/доменные концепты
    decisions/          <- зафиксированные решения с датой
    questions/          <- открытые вопросы и недопонимание
    references/         <- внешние артефакты (Sheets, GitLab, github.io)
    daily/              <- дневники по дням
    reviews/            <- ретроспективы
    synthesis/          <- сводки и обобщения
```

## Старт сессии (ритуал)

Перед первым действием по vault:
1. Прочитать `CRITICAL_FACTS.md` (если ещё не в контексте).
2. Прочитать `_index.md` (entry-point/каталог).
3. Прочитать последние 20 строк `log.md` через `grep '^## \[' log.md | head -20`.
4. Если в запросе упомянут проект — открыть `wiki/projects/<slug>.md` и его `Projects/<slug>/CLAUDE.md`.
5. Если упомянут партнёр — `wiki/partners/<slug>.md`.
6. Если упомянут человек — `wiki/people/<slug>.md`.
7. Проверить `wiki/questions/` на `status: open` (висящие вопросы).
8. Не пересобирать контекст всего vault'а на каждом шаге.

## Операции

- **ingest**: новый сырой материал кладётся в `raw/`. Канонизация в wiki через subagent `ingest-worker` с frontmatter, recency и graph-навигацией.
- **query**: ответ на вопрос пользователя — сначала через граф (`get_graph_neighbors` из aaronsb MCP), потом по journals.
- **lint**: периодическая проверка — все ли страницы имеют валидный frontmatter, нет ли висящих related-ссылок, broken links.

## Two-Output Rule

Каждый содержательный ответ пользователю должен обновлять минимум одну страницу vault'а. Если ответ привнёс новый факт (партнёр сказал X, рынок ведёт себя Y, мы решили Z) — сразу зафиксировать в соответствующей wiki-странице или decisions/. Без фиксации факт теряется.

## Frontmatter convention

Базовый (для всех страниц):
```yaml
---
type: project | partner | person | concept | decision | question | reference | daily | review | synthesis | archived
tags: [tag1, tag2]
related: ["[[wiki/projects/report]]", "[[wiki/partners/loko-bank]]"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
recency: YYYY-MM-DD
confidence: high | medium | low
---
```

Для `decision`: + `status: proposed|accepted|superseded`, `decided`, `supersedes`.
Для `question`: + `status: open|answered|dropped`, `raised`, `answered_in`.
Для `reference`: + `url`, `last_checked`, `auth: <your-password>|public|memory`.
Для `partner`: + `partner_id`, `domain: mfo|bank|retail|cpa`, `status`.
Для `person`: + `role`, `chat_name`, `git_aliases[]`, `tracker`.

## Запрет на удаление без archive

Удалять страницу wiki напрямую нельзя. Если страница больше не актуальна:
1. Поменять frontmatter на `type: archived` и `archived_at: YYYY-MM-DD`.
2. Оставить на месте — граф и backlinks не ломаются.
3. `/sb-lint` ежемесячно предлагает что архивировать.

## Memory tiers (Pass F, 2026-05-12)

Адаптация 4-tier pattern из rohitg00/agentmemory:

| Tier | Где живёт | Когда пишется | Когда читается |
|---|---|---|---|
| Working | `CRITICAL_FACTS.md` | вручную при важном факте | каждая сессия (SessionStart hook) |
| Episodic | `log.md`, `journals/*/log.md` | `session-auto-summary.py` Stop hook | начало сессии (grep '^## \[') |
| Semantic | `wiki/concepts/*.md` | `memory-consolidator` subagent или вручную через vault-writer | по запросу через grep/obsidian search |
| Procedural | `~/.claude/agents/*.md`, `~/.claude/skills/*/` | при формализации паттерна | автоматически через PROACTIVELY description |

Transfer rules:
- Working → Episodic: автомат (auto-summary hook)
- Episodic → Semantic: `memory-consolidator` раз в 5-7 сессий
- Semantic → Procedural: вручную через создание subagent/skill

Priority:
- CRITICAL (never evict): бизнес-цели, ID партнёров, prod endpoints → CRITICAL_FACTS
- HIGH (reload on task start): архитектурные решения, feedback rules → memory/*.md
- MEDIUM (episodic, active project only): детали задач → log.md
- LOW (evict after session): raw observations → not saved unless explicit

Подробнее: `wiki/concepts/memory-tier-pattern.md`.

## Что в этот manual НЕ входит

- Поведение Claude глобально (`~/.claude/CLAUDE.md`).
- Правила репо <your-workspace> (`<your-workspace>/CLAUDE.md`).
- Узкие правила проектов (`Projects/<x>/CLAUDE.md`).
- Скриншоты-2000px, MCP-response size — это глобальное, не vault-specific.
