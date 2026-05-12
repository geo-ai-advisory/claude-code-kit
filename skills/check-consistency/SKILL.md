---
name: check-consistency
description: Проверить логическую целостность данных в файле через consistency-checker subagent. 6 проверок — числа, sum-detail, даты-период, cross-section, wikilinks, sluggable references. Триггеры — `/check-consistency <file>`, «сверь цифры», «проверь логику данных», «все числа совпадают?», «итог корректный?».
user-invocable: true
---

# /check-consistency

## Что делает
Делегирует проверку data-консистентности файла к глобальному subagent `consistency-checker` (`~/.claude/agents/consistency-checker.md`).

Один вызов вместо ручного промпта — снижает overhead делегирования для коротких задач.

## Использование
```
/check-consistency Projects/<your-reports>/journals/2026-04-30-loko/report.html
```

или просто `/check-consistency` — спросить у пользователя путь к файлу.

## Workflow
1. Получить путь файла из аргумента или спросить.
2. Вызвать subagent через Task tool с reference на роль consistency-checker.
3. Передать prompt:
   > Проверь data-консистентность файла `<file>` по 6 проверкам из `~/.claude/agents/consistency-checker.md`. Полный отчёт в файл, в чат — 5 строк по контракту делегирования с verdict PASS/FAIL по каждой проверке и списком несостыковок.
4. Дождаться отчёта (5 строк + путь к файлу).
5. Вернуть пользователю verdict по каждой проверке + список несостыковок.

## 6 проверок (см. consistency-checker)
- Числа — одно и то же число одинаково во всех местах файла (header, секции, выводы).
- Sum-detail — итог = сумма деталей (offset проценты, выдачи по партнёрам, cost breakdown).
- Даты и период — все даты в указанном периоде, нет «висячих» или вне диапазона.
- Cross-section — упомянутый в одной секции факт не противоречит другой секции.
- Wikilinks — все `[[...]]` ссылаются на существующие заметки vault.
- Sluggable references — все referenced slugs/IDs (партнёр, кампания, slug в URL) существуют.

## Связано
- Полная роль: `~/.claude/agents/consistency-checker.md`
- Контракт делегирования: глобальный `~/.claude/CLAUDE.md`.

## Когда НЕ использовать
- Файл ещё не сгенерирован — проверять нечего.
- Нужна визуальная проверка вёрстки — это `/check-ui`.
- Нужен прогон UI-сценариев — это `/check-scenarios`.
