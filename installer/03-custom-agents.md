# Installer step 03 — Custom agents

Цель: помочь пользователю описать **его собственных** агентов под его конкретный domain. Эти агенты часто важнее моих готовых — они знают про его клиентов, его бизнес-правила, его форматы данных.

## Принцип

Мои агенты в `agents-library/` — **универсальные шаблоны**. Custom-агенты в `~/.claude/agents/` — **специфичные под пользователя**. Например:

| User domain | Custom agent |
|---|---|
| Финтех, кредитование | `<your-company>-db-researcher` — знает таблицы, статусы, специфические индексы (статус 305 = выдан, 190 = выбран и т.д.) |
| E-commerce | `<store>-order-flow-tester` — знает шаги от cart до confirmation |
| SaaS / B2B | `<product>-tenant-data-auditor` — знает структуру multi-tenant и риски data leak |
| Reports / analytics | `<company>-report-builder` — знает шаблоны отчётов клиентам, design-system, метрики |
| Mobile app | `<app>-ios-uitester` — знает navigation flow, deep links |

## Что спросить у пользователя

После step 01-02 у тебя уже есть scan-журнал. Уточни 5 вещей:

1. **«Есть ли у тебя повторяющийся workflow который Claude каждый раз заново разбирает?»**
   - Например: «каждую неделю отчёт партнёру X», «каждый день проверка прода», «при добавлении партнёра 5 шагов в БД»
   - Это кандидат на skill (slash-команду) или custom-agent

2. **«Какие термины/ID/коды тебе приходится повторять Claude'у каждую сессию?»**
   - Тип: PartnerId UUID, статусы numeric, эндпоинты, метрики
   - Это уйдёт в `CRITICAL_FACTS.md` (step 04 — vault)

3. **«Есть ли у тебя свой стиль ответов / отчётов / документов которого надо придерживаться?»**
   - Шрифты, цвета, тон, длина параграфов
   - Это уйдёт в `wiki/concepts/<your>-design-system.md`

4. **«В каких задачах ты не доверяешь Claude и хочешь чтобы что-то проверяло за ним?»**
   - Бизнес-цифры в отчётах? Cross-reference между секциями? Согласованность сумм?
   - Это кандидат на специальный verifier-agent

5. **«Что в твоей работе делать НЕЛЬЗЯ под угрозой больших последствий?»**
   - Push в prod без approve? Удаление продакшен-данных? Отправка писем без re-read?
   - Это уйдёт в hard-rules (CLAUDE.md) и hooks (step 05)

## Создание custom-агента

Базовый шаблон:

```markdown
---
name: <slug-name>
description: Use when <триггер действия пользователя>. <Когда обязателен, когда нет>. Триггеры — "<фраза1>", "<фраза2>".
model: sonnet
tools: Read, Grep, Glob, Bash, <специфичные MCP>
---

# <name>

## Зачем

<1-2 параграфа: какую боль решает, какой gap покрывает>

## Когда вызывать

- <Trigger 1>
- <Trigger 2>
- НЕ вызывать когда: <antitriggers>

## Workflow

1. <Step 1>
2. <Step 2>
3. ...

## Output контракт

В чат — РОВНО N строк:
```
<формат>
```

Подробности в файле: `<path-template>`

## Связанные

- `wiki/concepts/<concept>.md`
- `~/.claude/agents/<related-agent>.md`
```

## Примеры запросов к пользователю с шаблонами ответов

### Пример A — финтех, поиск выдач

User: «Хочу чтобы Claude умел сразу выгружать выдачи <industry> за период без миллиона уточнений»

Ты создаёшь `~/.claude/agents/<your-domain>-data-researcher.md`:
```markdown
---
name: <your-domain>-data-researcher
description: Use when user asks for <industry> выдач за период. Знает что CreditIssued=305 (не 42), ProductTypeId=5, ChannelTypeId=2, фильтр через CAST(Created AS DATE) для datetimeoffset +03:00.
model: sonnet
tools: Read, Bash, mcp__company-db__query
---

# <your-domain>-data-researcher

[... детали ...]
```

### Пример B — e-commerce, проверка чекаута

User: «У меня иногда падает финальный шаг checkout — хочу чтобы Claude автотестил его при любом изменении checkout flow»

Ты создаёшь `~/.claude/agents/checkout-flow-tester.md`:
```markdown
---
name: checkout-flow-tester
description: Use PROACTIVELY after Edit/Write на checkout/*.tsx или /api/checkout/*.ts. Тестирует cart→shipping→payment→confirmation, edge cases (отменённая карта, no inventory, expired session).
...
```

## Создавать сразу или потом?

- **Создать сразу** если пользователь уже знает свой workflow и просит это сейчас
- **Отложить** если он не уверен — лучше через 1-2 недели увидит куда нужно

Если откладываешь — запиши «open question» в `wiki/questions/` (это будет в step 04 после установки vault). Пользователь сможет вернуться позже.

## Запиши в журнал

```bash
cat >> ~/claude-install-journal/<date>-scan.md <<EOF

## Custom agents (step 03)
<список созданных custom-агентов>

## Deferred (для будущих сессий)
<список идей которые отложили>
EOF
```

## После завершения

Если пользователь установил кастомов или отложил — переходи к **step 04 — vault setup**.
