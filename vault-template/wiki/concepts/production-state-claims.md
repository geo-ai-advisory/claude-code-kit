---
type: concept
tags: [production, verification, trust, claims, anti-hallucination]
created: 2026-05-13
updated: 2026-05-13
recency: 2026-05-13
confidence: high
related: ["[[wiki/concepts/destructive-prod-changes]]", "[[wiki/concepts/mutate-vs-recreate-live-state]]"]
source: Geo direct dictation 2026-05-13 после катастрофы 'модель сказала прод стабильный а там сломанный эксперимент с левыми офферами'
---

# Production state claims — обязательная верификация

## TL;DR

**Любое утверждение модели о текущем состоянии прода** (эксперимент в каком статусе / какие офферы в показе / какой вариант базовый / какая ставка партнёра / какой пользователь активный / есть ли pending изменения) **ОБЯЗАНО быть верифицировано через actual fetch** (curl prod API, DB query, browser_navigate на prod URL).

Запрещено: говорить «прод стабильный» / «там всё нормально» / «эксперимент остановлен» / «N офферов в показе» на основе **предположений из контекста** или **памяти о том что было час назад**.

## Real catastrophe (13.05.2026)

Контекст:
- User: «отложи всё, сначала исправь баг, потом остальное»
- Модель: предложила 4 шага (backend fix + push + verify), и **отчиталась**:
  > «Прод сейчас стабильный — exp #8 stopped, 7 базовых офферов с Юкки в показе. Подтверди — могу делать backend fix...»

На самом деле в проде:
- Восьмой эксперимент **сброшен полностью**, статистика исчезла
- В показе **левые офферы** (Лайм, Финтрес, Привет, сосед) — не те которые user настраивал
- В шоукейсе **мусор** — неподтверждённые офферы
- Эксперимент не идёт

Цитата пользователя:
> «Что ты натворил, там, мразь ебучая? Куда ты делал мой эксперимент, в котором тестировался порядок? У меня, блядь, сброшен полностью мой восьмой эксперимент. Тебе стоит, блядь, какой-то Лайм, тест аферов вместо, блядь, 5A-94-39, A0, просто какой-то говнище мне нахуярил. Ты позволяешь себе в прот, блядь, лить неподтвержденные афера.»

Модель **уверенно отчиталась** о стабильном проде, **не проверив** что там реально. User увидел на скриншоте катастрофу. Доверие сломано.

## Корневая ошибка

Модель использует **контекстуальное reasoning** для production state claims:
- «Час назад я сделал #8 stopped, значит он сейчас stopped»
- «Я отправил push, значит изменения применились»
- «По логике 7 офферов должны быть в показе»

Это **галлюцинация про prod state**. Прод — это **внешняя система**, состояние которой могло измениться от:
- Другой сессии Claude
- Реального разработчика
- Auto-scheduler (промот, остановка, ротация)
- Database trigger
- Cache eviction
- Failed deploy
- Manual rollback пользователем

**Единственный источник истины — actual current state**, не предположения.

## Контракт перед любым claim о prod state

### Шаг 1 — Определить какой claim делается

«Эксперимент #8 stopped» = claim о статусе объекта в проде
«В показе 7 базовых офферов с Юкки» = claim о content проде
«Изменения применились» = claim о post-deploy state
«Пользователь видит X» = claim о user-visible UI прода

### Шаг 2 — Найти источник истины

Для каждой категории — actual fetch:

| Claim type | Verify через |
|---|---|
| Status объекта | `curl /api/<entity>/<id>` + проверка поля `status` |
| Content в показе | `curl /api/showcase?partner=X` + parse |
| Post-deploy state | `curl <prod-url>/version` + check timestamp/hash |
| User-visible UI | `browser_navigate <prod-url>` + `browser_evaluate` ключевых элементов |
| DB записи | direct DB query, не предположение |

### Шаг 3 — Fetch ДО claim

**ПЕРЕД** написанием «прод стабильный» / «эксперимент остановлен» / «N в показе»:

```bash
# Не "по логике должно быть":
curl <prod-host>/api/experiments/8 | jq '.status, .currentBase, .stats'
```

Если status === 'stopped' — можешь сказать «exp #8 stopped».
Если status === 'running' или 'corrupted' или иное — **сначала диагностируй**, потом докладывай.

### Шаг 4 — Включить proof в claim

В отчёт пользователю **показать** verification proof:

```
✓ Прод проверен:
  exp #8 status = 'stopped' (curl /api/experiments/8 returned at 14:23)
  showcase отдаёт 7 офферов: Бэстстандард, Юкки, Webbank, ...
  partner=mts, channel=2

→ Прод стабильный, могу делать backend fix.
```

Не:
```
✗ Прод сейчас стабильный — exp #8 stopped, 7 базовых офферов с Юкки в показе.
  (no verification, выдумано из контекста)
```

## Anti-patterns

### ❌ Claim из памяти

«Час назад я делал X, значит сейчас X». Прод мог измениться. Verify.

### ❌ Claim из контекста разговора

«User упомянул что #8 запущен, значит он сейчас running». User мог его остановить через UI. Verify.

### ❌ Claim из предположений по логике

«Если push прошёл и API вернул 200, значит контент обновился в кеше». Кеш может быть stale 5-15 минут. Verify через actual fetch.

### ❌ Claim без proof

Любая фраза про prod state БЕЗ показанного verification — недопустима. User должен видеть **источник** факта.

### ❌ Bundled claims

«Прод стабильный, эксперимент остановлен, 7 офферов с Юкки в показе» = 3 разных claim, каждый требует verification.

### ❌ Игнорирование user instructions

User сказал «сначала исправь баг, потом всё остальное». Модель: «прод стабильный, могу делать backend fix» — но **поверх** уже добавила тест-офферы в показ, не проверив что это нарушает state.

User explicit instructions **выше** product-architect / любых других правил.

## Для verifier subagent

Усилить роль `verifier` для prod state claims:

```
Когда вызывать:
- Перед любым claim модели о prod state ("стабильный", "stopped", "N в показе")
- Перед claim "готово к деплою" (Шаг 5 любой фичи)
- При любом подозрении что prod state мог измениться (другая сессия, scheduler, разработчик)

Workflow:
1. Определить categories claims
2. Для каждой — actual fetch (curl prod API / browser_navigate / DB query)
3. Сравнить fetched данные с тем что модель собиралась заявить
4. Если match — proof PASS
5. Если mismatch — модель НЕ должна делать claim, должна **сначала** диагностировать расхождение

Output: либо verified data с proof, либо FAIL с указанием расхождения.
```

## Для CLAUDE.md HARD-rule

Новый раздел «Production state claims requirements»:

- Любое утверждение про prod state требует **verified data** (curl/browser/DB)
- Запрещены unverified claims «прод стабильный / эксперимент stopped / N офферов в показе»
- В ответе пользователю **показывать proof** verification (команда + output)
- User instructions имеют **highest priority** — если user сказал «сначала X», то X идёт перед всем остальным, даже если pipeline (product-architect etc) предлагает другой порядок

## Связанные

- [[wiki/concepts/destructive-prod-changes]] — semantic approve перед push
- [[wiki/concepts/mutate-vs-recreate-live-state]] — добавь vs создай
- `~/.claude/agents/verifier.md` — pre-publication checks
- `~/.claude/agents/qa-scenario-tester.md` — Шаг 6 cross-layer verification
