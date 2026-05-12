---
name: sb-start
description: Vault entry-point ритуал — читает CRITICAL_FACTS, _index, последние 20 строк log.md, проверяет open questions в wiki/questions/. Триггер — `/sb-start` в начале сессии когда нужен контекст vault. Заменяет декларативное правило «прочитать vault на старте» которое не выполнялось.
user-invocable: true
---

# /sb-start

## Что делает
Запускает vault entry-point ритуал явно одной командой — вместо декларативного правила в `~/.claude/CLAUDE.md`, которое модель забывает в фоне нетривиальной сессии.

Низкий порог входа: одна строка вместо «не забудь прочитать vault». Результат — компактный summary активного состояния second-brain без раздувания контекста.

## Использование
```
/sb-start
```

Аргументов нет.

## Workflow
1. Read `Projects/<your-vault>/CRITICAL_FACTS.md` (~120 токенов критических фактов).
2. Read `Projects/<your-vault>/_index.md` (entry-point с каталогом проектов и страниц).
3. Bash: `grep '^## \[' Projects/<your-vault>/log.md | head -20` — последние 20 сессий.
4. Bash: `grep -rl '^status: open' Projects/<your-vault>/wiki/questions/ 2>/dev/null` — открытые вопросы.
5. Если есть открытые вопросы — Read первого из них (для контекста, не больше).
6. Возврат пользователю: компактный summary в формате:
   ```
   Vault loaded:
   - Активные проекты: <список из _index>
   - Последние сессии (20): <короткий перечень тем>
   - Открытых вопросов: N (<первый вопрос — заголовок>)
   - CRITICAL_FACTS: <2-3 ключевых факта>
   Готов к работе.
   ```

## Зачем это нужно
Глобальное правило «Vault entry-point ритуал» в `~/.claude/CLAUDE.md` — декларативное. Модель в нетривиальной сессии часто переходит сразу к запросу пользователя без чтения vault. Slash-команда фиксирует ритуал как явное действие пользователя — порог входа 1 строка.

## Связано
- Vault root: `Projects/<your-vault>/`
- Operating manual: `Projects/<your-vault>/_CLAUDE.md`
- Декларативное правило: `~/.claude/CLAUDE.md`, раздел «Vault entry-point ритуал».
- Связанные команды: `/sb-recap`, `/sb-question`, `/sb-log`, `/sb-daily` (все в навыке `second-brain`).

## Когда НЕ использовать
- Сессия короткая, операционная, fast-режим — vault не нужен.
- Контекст уже подгружен в этой же сессии — не пересобирать.
- Запрос явно вне <your-workspace> (общий код, посторонняя задача) — vault нерелевантен.
