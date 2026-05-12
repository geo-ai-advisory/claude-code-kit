# Memory tiers — 4-tier pattern из agentmemory

Адаптировано из [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) под Claude Code на macOS.

## Проблема

Claude Code сам не помнит ничего между сессиями. Каждый раз ты заново объясняешь контекст: кто ты, какие проекты, кто партнёры, какие конвенции. Это медленно и хрупко.

## Решение

4 уровня памяти с разным временем жизни и способом доступа:

| Tier | Аналогия | Где | Когда читается | Как пишется |
|---|---|---|---|---|
| **Working** | Кратковременная (RAM) | `CRITICAL_FACTS.md` | Каждая сессия — SessionStart hook | Вручную при появлении важного факта |
| **Episodic** | Хронология «что произошло когда» | `log.md`, `journals/*/log.md` | По требованию — `grep '^## \['` | Auto через `session-auto-summary.py` Stop hook |
| **Semantic** | Знание «что я знаю» | `wiki/concepts/*.md` | По требованию — Obsidian search / grep | Через `memory-consolidator` agent или vault-writer |
| **Procedural** | Навыки «как делать» | `~/.claude/agents/*.md`, `~/.claude/skills/*/` | Автоматически через `Use PROACTIVELY when...` | Вручную при формализации паттерна |

## Transfer rules — как факт переходит между уровнями

```
[Сессия началась]
    ↓
Working tier (CRITICAL_FACTS) — Claude видит в system context
    ↓ (работа идёт)
Активная сессия — раскапывает / создаёт факты
    ↓
[Stop hook]
    ↓
session-auto-summary.py пишет 3-5 строк в log.md   ← Working → Episodic
    ↓
[Дни проходят, повторяющиеся темы]
    ↓
memory-consolidator agent (запускается раз в 5-7 сессий вручную):
  • Tail log.md (последние 30 сессий)
  • Grep keyword по сессиям
  • Если факт упоминался в ≥2 сессий → создать/update wiki/concepts/<topic>.md
                                                     ↑
                                          Episodic → Semantic
    ↓
[Когда concept стабилизировался]
    ↓
Если паттерн повторяется как инструкция → оформить как ~/.claude/agents/<name>.md
                                                                ↑
                                                  Semantic → Procedural
```

## Priority и eviction

| Tier | Priority | Eviction |
|---|---|---|
| Working (CRITICAL_FACTS) | CRITICAL — never evict | Не удаляется автоматически, только вручную |
| Episodic (log.md) | MEDIUM | log.md растёт неограниченно; tail используется (последние ~30 сессий). Старые можно архивировать в `journals/old/log-archive-<YYYY-MM>.md` |
| Semantic (wiki/concepts) | HIGH | Не evict. Stale концепты помечаются `status: archived` в frontmatter, остаются на месте |
| Procedural (agents) | HIGH | Не evict. Старые агенты — `~/.claude/agents/_archive/` |

## Что писать в CRITICAL_FACTS.md (working tier)

**Размер: < 2000 токенов.** Иначе SessionStart hook не сможет всё инжектить в system context.

**Что обязательно:**
1. **Кто ты** — имя, роль, компания, главная цель работы
2. **Активные проекты** — список с 1 строкой описания каждого
3. **Ключевые партнёры / клиенты / системы** — с ID/UUID/URL
4. **Команда** (если работаешь с людьми) — кто за что отвечает
5. **Технические инварианты** — константы которые забывать нельзя (status code = N, ProductTypeId=X)
6. **Ключевые документы** — Google Doc ID, важные репозитории
7. **Стиль** — язык, длина параграфов, формат отчётов

**Что НЕ писать в CRITICAL_FACTS:**
- Длинные объяснения концепций — это в `wiki/concepts/`
- Историю решений — это в `wiki/decisions/`
- Per-task детали — это в `journals/`
- Полные wiki-страницы — только пути к ним

## Что писать в wiki/concepts (semantic tier)

**Концепт = одна тема, которую ты раскрыл / понял / задокументировал.** Стабильное знание.

Структура (template):

```markdown
---
type: concept
tags: [<тема>, <ещё>]
created: YYYY-MM-DD
updated: YYYY-MM-DD
recency: YYYY-MM-DD
confidence: high/medium/low
related: ["[[wiki/concepts/<related>]]"]
---

# <Название>

## TL;DR
<1-2 параграфа основной мысли>

## Контекст / откуда взялся

<История появления концепта — что произошло, почему понял>

## Главные тезисы

- <Тезис 1 с объяснением>
- <Тезис 2>
- ...

## Применение

<Где и как использовать>

## Анти-паттерны

- ❌ <Что НЕ делать>

## Связанное

- [[wiki/concepts/<related>]]
- [[wiki/decisions/<date>-<decision>]]
```

Примеры готовых концептов в kit:
- `wiki/concepts/reference-platforms.md` — каталог reference платформ для product-architect / ui-design-architect
- `wiki/concepts/ab-experiment-product-thinking.md` — domain про А/Б тесты
- `wiki/concepts/component-reuse-discipline.md` — one entity → one renderer
- `wiki/concepts/memory-tier-pattern.md` — этот документ в vault-форме

## memory-consolidator workflow (Episodic → Semantic)

Запускается раз в 5-7 сессий вручную или через `/sb-recap`.

1. Read tail `log.md` (последние 30 сессий)
2. Grep keywords по сессиям — найти темы упоминавшиеся в ≥2 разных датах
3. Для каждой темы:
   - Проверить есть ли `wiki/concepts/<slug>.md`
   - Если нет — создать с frontmatter и базовой структурой
   - Если есть — `obsidian_patch_section` для добавления упоминаний / обновления
4. Создать журнал миграции в `wiki/decisions/<date>-memory-consolidation.md`

Детали — `agents-library/memory/memory-consolidator.md`.

## Что отличает этот pattern от обычного use Claude Code

| Без 4-tier | С 4-tier |
|---|---|
| Claude помнит только текущую сессию | CRITICAL_FACTS в каждой сессии |
| Контекст бизнеса каждый раз заново | Один раз заполнил, работает годами |
| Факты теряются между сессиями | log.md → wiki/concepts → wiki/decisions |
| Паттерны решений не формализованы | Agents/skills отражают procedural memory |

## Альтернативы которые мы рассматривали и отбросили

- **SQLite + vector embeddings** (как в оригинале agentmemory) — преждевременная оптимизация при < 200 wiki-страниц. Filesystem + grep работает быстрее
- **BM25 + RRF hybrid search** — overkill для одиночной работы. Obsidian search достаточен
- **Automatic LLM compression** — добавляет hallucination в semantic tier. Лучше явная консолидация через memory-consolidator
