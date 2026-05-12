---
name: check-scenarios
description: Прогнать ВСЕ UI-сценарии файла через qa-scenario-tester subagent. Multi-select, edge cases, console errors, network failures. Без 100% PASS — не отдаёт работу. Триггеры — `/check-scenarios <file>`, `/qa-test`, «прогон сценариев», «протестируй UI», «всё ли работает».
user-invocable: true
---

# /check-scenarios

## Что делает
Делегирует QA-прогон файла к глобальному subagent `qa-scenario-tester` (`~/.claude/agents/qa-scenario-tester.md`).

Используется как часть pipeline разработки dashboard и сложных UI: после реализации — обязательный прогон scenarios перед «готово».

## Использование
```
/check-scenarios Projects/<your-dashboard>/wwwroot/compare.html
```

или просто `/check-scenarios` — спросить у пользователя путь к файлу или URL.

## Workflow
1. Получить путь к файлу или URL.
2. Если файл — запустить локально (через preview_start или существующий dashboard на `localhost:5000`).
3. Вызвать subagent qa-scenario-tester через Task tool:
   > Прогон ВСЕХ scenarios для `<file_or_url>` по протоколу `~/.claude/agents/qa-scenario-tester.md`. Workflow 7 этапов — discovery, multi-select scenarios, edge cases, console/network sanity, регресс по основному happy-path, agg verdict. Без 100% PASS — итоговый verdict FAIL. Полный отчёт в файл, в чат — 5 строк по контракту делегирования с scenarios PASS/TOTAL и списком багов P0/P1/P2.
4. Дождаться отчёта.
5. Вернуть пользователю scenarios PASS/TOTAL + список багов по приоритетам.

## Что проверяет qa-scenario-tester
- Discovery — что вообще есть в UI (кнопки, фильтры, табы).
- Happy path — основной сценарий пользователя.
- Multi-select — все комбинации выбора, фильтров, сортировок.
- Edge cases — пустые состояния, очень длинные тексты, missing data.
- Console errors — нет красных ошибок в DevTools.
- Network failures — graceful обработка таймаутов и 5xx.
- Регресс — старый функционал не сломался.

## Связано
- Полная роль: `~/.claude/agents/qa-scenario-tester.md`
- Используется в pipeline `UI/dashboard agent` (см. roles в `~/.claude/agents/`).
- Контракт делегирования: глобальный `~/.claude/CLAUDE.md`.

## Когда НЕ использовать
- Простая HTML-страница без интерактива — достаточно `/check-ui`.
- Нужна только проверка чисел/данных — это `/check-consistency`.
- Файл ещё не запущен и нет URL — сначала запустить, потом прогнать.
