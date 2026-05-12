---
name: check-ui
description: Проверить визуальное качество HTML/CSS файла через ui-quality-reviewer subagent. 6 категорий — типографика, spacing, цвет, состояния, адаптивность, анимация. Триггеры — `/check-ui <file>`, «проверь верстку», «UI ревью», «шрифты скачут», «отступы кривые», «не премиум».
user-invocable: true
---

# /check-ui

## Что делает
Делегирует проверку UI-качества файла к глобальному subagent `ui-quality-reviewer` (`~/.claude/agents/ui-quality-reviewer.md`).

Снижает порог входа для делегирования — одна строка вместо формулировки промпта вручную.

## Использование
```
/check-ui Projects/<your-dashboard>/wwwroot/static/compare.html
```

или просто `/check-ui` — спросить у пользователя путь к файлу.

## Workflow
1. Получить путь файла из аргумента или спросить пользователя одной строкой.
2. Вызвать subagent через Task tool с `subagent_type: "general-purpose"` и явным reference на роль ui-quality-reviewer.
3. Передать prompt:
   > Проверь UI качество файла `<file>` по протоколу `~/.claude/agents/ui-quality-reviewer.md`. Прогон 6 категорий — типографика, spacing, цвет, состояния, адаптивность, анимация. Открой файл локально, viewport 1440x900, выполни browser_evaluate для computed styles, browser_resize для адаптивности 1280/1600. По каждой категории — verdict PASS/FAIL и список нарушений. Полный отчёт записать в файл, в чат вернуть 5 строк по контракту делегирования.
4. Дождаться отчёта (5 строк summary + путь к файлу).
5. Вернуть пользователю summary + ссылку на полный отчёт.

## Категории проверки (см. ui-quality-reviewer)
- Типографика — Inter/системные fallback, line-height, размеры, ровная сетка.
- Spacing — отступы кратны 4/8 px, нет «прыжков» между секциями.
- Цвет — токены, контраст AA, нет случайных оттенков серого.
- Состояния — default/hover/active/focus у всех интерактивных элементов.
- Адаптивность — 1280/1440/1600, нет горизонтального скролла, ничего не наезжает.
- Анимация — transitions у hover, нет резких скачков.

## Связано
- Полная роль: `~/.claude/agents/ui-quality-reviewer.md`
- Связанные wiki: `Projects/<your-vault>/wiki/concepts/{html-report-design-system,design-balance,html-button-states,ui-grid-discipline}.md`
- Контракт делегирования: глобальный `~/.claude/CLAUDE.md`, раздел «Контракт делегирования».

## Когда НЕ использовать
- Файл ещё не существует — нечего проверять.
- Нужна только проверка чисел/логики данных — это `/check-consistency`.
- Нужен прогон UI-сценариев (multi-select, edge cases) — это `/check-scenarios`.
