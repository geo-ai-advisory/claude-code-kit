---
type: concept
tags: [product, state-management, live-processes, ab-testing, destructive-operations]
created: 2026-05-13
updated: 2026-05-13
recency: 2026-05-13
confidence: high
related: ["[[wiki/concepts/stateful-ui-lifecycle]]", "[[wiki/concepts/destructive-prod-changes]]", "[[wiki/concepts/ab-experiment-product-thinking]]"]
source: Geo direct dictation 2026-05-13 после катастрофы 'попросил добавить тест-позиции, она создала новый тест и сломала live'
---

# Mutate vs Recreate live state — фундаментальный pattern

## TL;DR

Когда пользователь говорит **«добавь / измени / убери»** в контексте **уже работающего процесса** (live эксперимент, открытая сессия, активный заказ, текущий отчёт) — это **mutation существующего объекта**, не создание нового. Создание нового убивает накопленные данные и текущий state.

## Real catastrophe (13.05.2026)

Цитата пользователя:
> «После всех этих ёбаных апдейтов, вся статистика слетела, все планы пишут мало данных, порядка лидеров нет, нет соответственно следующего что будет на смену, какие-то стоят 100% трафика. То есть пиздец, у меня до этого был тест номер 8 запущенный, а сейчас 9. Какого хуя 9? Мне должен был, блядь, тест номер 8, сучара-то тупая, и он должен был работать, и там все было настроено, и там собирались данные.»
>
> «Я не просил, нахуй, менять номер теста, я просил просто добавить в существующий тест тест позиции.»
>
> «У меня не должен, сука, новый тест запускаться, у меня должен оставаться предыдущий, если я не нажимал кнопку новый эксперимент.»

Что произошло:
- Тест #8 был **running**, накопил данных, был лидерборд, готовился следующий вариант
- User: «добавь тест-позиции X, Y в этот тест»
- Модель: **создала тест #9** (новый объект) с тест-позициями X, Y
- Тест #8 → лишился traffic (стоит 100% но не выполняется)
- Тест #9 → стартовал с нулевых данных, всё «мало данных»
- **Накопленная статистика старого теста потеряна для решения**

## Принцип

### Mutation (правильно)

User глагол выражает изменение **существующего** объекта:
- «добавь оффер X в тест»
- «убери юки из ротации»
- «измени порядок офферов в тесте»
- «увеличь долю трафика на вариант B»
- «приостанови этот тест»

→ **Изменить in-place** существующий объект с тем же ID, продолжить state, не создавать новый.

### Recreation (требует explicit confirmation)

User глагол выражает **новое целое**:
- «запусти новый тест»
- «создай новый эксперимент»
- «начни заново»
- «обнули и начни новый»

→ Только в этих случаях создавать новый объект. И **в этих случаях** обязательно спросить про судьбу старого: «остановить старый тест #8 как inconclusive / завершить с текущими данными как winner?»

## Чек-лист для модели перед изменением live state

### Шаг 1 — Найти существующий live state

```bash
# Например для эксперимента
curl /api/experiments/list?status=running

# Есть ли уже running с тем же scope (партнёр / контекст)?
```

Если есть → продолжаем с Шагом 2 (mutation).
Если нет → создаём новый.

### Шаг 2 — Сматчить user request с операцией

User words → operation:

| User words | Operation | API call |
|---|---|---|
| «добавь / включи / поставь» | PATCH existing | `PATCH /experiments/<id>/variants` |
| «убери / отключи / исключи» | PATCH existing | `PATCH /experiments/<id>/variants` |
| «измени / поменяй / смени» | PATCH existing | `PATCH /experiments/<id>` |
| «начни новый / создай / запусти» | POST new | `POST /experiments` |
| «останови / заверши / останови» | PATCH status | `PATCH /experiments/<id>/status` |

### Шаг 3 — Confirm if ambiguous

Если user request **семантически неоднозначен** ("добавь" может значить «в существующий» или «новым тестом»):
- НЕ догадываться
- Показать: «У тебя сейчас running тест #8 со статистикой N кликов. Добавить позиции в него (mutation), или создать новый тест #9 и оставить #8 как paused?»
- Ждать выбор

### Шаг 4 — После операции — сохранить контекст

Если mutation — accumulated state сохранён, продолжаем.
Если recreation — обновить UI «новый тест #9 запущен, старый #8 в статусе X».

## Anti-patterns

### ❌ «Это безопаснее создать новый»

Не безопаснее — это разрушение накопленной статистики. User потерял часы / дни traffic и решений.

### ❌ «Старый тест я не трогал, он остался»

Технически осталось, но **по семантике мёртв** — traffic не идёт, данные не растут. Это equivalent к удалению с точки зрения пользователя.

### ❌ «Запросы 'добавь' и 'создай новый' это синонимы»

Нет. «Добавь оффер X в тест» = mutation. «Создай новый тест с оффером X» = recreation. Слова **разные**, не путать.

### ❌ Создавать новый объект чтобы избежать миграции

Если "добавить вариант в running test" сложно технически (бэкенд не умеет hot-add) — это **бэкенд-проблема**, не product solution. Сказать пользователю: «Бэкенд не поддерживает добавление в running. Варианты: A) остановить тест #8, скопировать settings + добавить X, запустить #9. B) Подождать когда бэкенд сделает hot-add. Что выбираешь?»

НЕ принимать decision молча.

### ❌ Молчать про последствия

Если recreation неизбежна — **обязательно** показать что теряется: «Тест #8 будет paused с накопленными N кликов. Эти данные останутся в history, но decision-making начинается с нуля. ОК?»

## Для product-architect (Q13)

Добавить в 7+4 вопросов:

**Q13 — Mutate or Recreate?**

Если задача меняет **уже-существующий** live state (running experiment, open ticket, active campaign):
- User request — это **mutation** существующего или **recreation** нового?
- Глаголы «добавь / измени / убери» → mutation (PATCH)
- Глаголы «создай / запусти новый» → recreation (POST)
- Если ambiguous — **спросить пользователя** до начала work

Anti-pattern: «безопаснее создать новый» убивает накопленные данные.

## Для qa-scenario-tester

В Pre-flight INPUT добавить:

**Если изменение касается live state объекта:**
- Перед началом тестирования — снять snapshot существующего state
- После изменения — сравнить ID объекта
- **FAIL если** объект имеет новый ID (recreation) когда user просил mutation
- **FAIL если** объект имеет старый ID но потерял accumulated data

```js
// Псевдокод
const before = curl('/api/experiments/list?status=running');
const beforeId = before.experiments[0].id;  // e.g. 8
const beforeStats = before.experiments[0].stats;  // {clicks: 1500, ...}

applyChange();

const after = curl('/api/experiments/list?status=running');
const afterId = after.experiments[0].id;  // expecting 8 if mutation
const afterStats = after.experiments[0].stats;

// User слово было "добавь"
if (user_request_intent === 'mutate') {
  assert(afterId === beforeId, `User wanted mutation, but got new object: ${beforeId} → ${afterId}`);
  assert(afterStats.clicks >= beforeStats.clicks, 'Accumulated data lost');
}
```

## Связанные

- [[wiki/concepts/stateful-ui-lifecycle]] — какое UI показывает в каком state
- [[wiki/concepts/destructive-prod-changes]] — semantic approve перед push
- [[wiki/concepts/ab-experiment-product-thinking]] — domain knowledge А/Б
