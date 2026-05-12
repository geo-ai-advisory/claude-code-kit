---
type: concept
tags: [architecture, components, ui, discipline, dashboard]
related: ["[[wiki/concepts/ab-experiment-product-thinking]]", "[[wiki/concepts/ui-grid-discipline]]", "[[wiki/projects/report]]"]
created: 2026-05-12
updated: 2026-05-12
recency: 2026-05-12
confidence: high
source: Geo direct dictation 2026-05-12 14:40 после катастрофы соседней сессии 64052142
---

# Component reuse discipline — «One entity → one renderer»

## TL;DR

Если в проекте есть **сущность** (порядок офферов, партнёр, статус эксперимента, KPI карточка, селектор) — она ОБЯЗАНА визуализироваться **одним** компонентом везде где появляется. Никаких «звёздочка тут, полный порядок там, чипсы в третьем месте». Это HARD правило не только про дублирование функций (это `selector-duplication-detector.py` ловит), но и про **визуальное представление одной и той же entity**.

## Реальная катастрофа 2026-05-12

В сессии `64052142` ассистент сделал на одной странице эксперимента **три разных рендера** порядка офферов:
- В таблице лидерборда — полный визуальный порядок (`renderOrderCompact` с 7 чипсами офферов)
- В секции «накоплено по каждому порядку» — только звёздочка «★ базовый» без офферов
- В диалоге «зафиксировать вариант» — hash варианта `fe02145d5f90`, не порядок

Реакция пользователя:
> «я что экстрасенс и должен помнить базовый наизусть? + само отображение порядков тут отличается от такого же компонента в лидерборде, там удобнее, ты опять нарушаешь правило, в каждой странице одни и теже компоненты заного пилишь и поразному создаешь»

## Правило (HARD)

**Одна entity → один renderer-компонент → одно визуальное представление везде.**

Допустимые варианты компонента:
- **Размер** (sm / md / lg) — один компонент с prop `size`
- **Density** (compact / comfortable) — один компонент с prop `density`
- **Состояние** (active / disabled / hover) — один компонент со state classes

НЕ допустимо:
- Две разные функции рендера одной entity (например `renderOrderCompact` в одном файле и inline `<span>★ базовый</span>` в другом)
- Inline HTML для entity которая уже имеет компонент
- «Тут полная версия, тут сокращённая» — должно быть `renderOrder(offers, {size: 'sm'})`, а не два разных кода

## Каталог <your-workspace> entities (актуальный)

| Entity | Renderer | Файл | Где используется |
|---|---|---|---|
| Партнёр (свитчер) | `PartnerSwitcher` | `wwwroot/static/components/partner-switcher.js` | showcase, experiments, dashboard, cabinet |
| Порядок офферов | `renderOrderCompact` | `wwwroot/static/components/experiments-page.js` (нужно вынести в отдельный файл `order-renderer.js`) | лидерборд, накоплено-по-порядку, история базовых, диалоги |
| Статус эксперимента | `renderStatus` (TODO — создать) | `wwwroot/static/components/experiment-status.js` (нужно создать) | toolbar, история, лидерборд |
| KPI карточка | `renderKpiCard` (TODO) | `wwwroot/static/components/kpi-card.js` (нужно создать) | dashboard, отчёт, кабинет |
| Уверенность (probability bar) | inline сейчас — нужно вынести в `confidence-bar.js` | — | лидерборд, варианты, accumulated |

## Pipeline для product-architect / ui-design-architect (HARD)

Перед началом screen-spec ОБЯЗАТЕЛЬНО:

1. **Перечислить entities на новом экране** (что будет видеть пользователь)
2. **Для каждой entity — Grep по проекту**: ищем существующий renderer
   ```bash
   # Пример для «порядок офферов»
   grep -rn "renderOrder\|offer.*compact\|offers.map" Projects/<your-dashboard>/wwwroot/static/components/
   ```
3. **Если renderer есть** — ИСПОЛЬЗОВАТЬ его. Если визуально надо иначе — добавить prop / variant в существующий компонент, НЕ создавать новый
4. **Если renderer нет** — создать в `wwwroot/static/components/<entity>-renderer.js` и подключить на ВСЕХ страницах где entity появляется
5. В screen-spec явно перечислить: «entity X использует компонент Y из файла Z, prop=A»

## Hook `selector-duplication-detector.py` — расширение

Существующий hook ловит копипаст функций по имени. Pass J расширил его чтобы ловить **разные визуалы одной entity**:

Эвристика: на одной странице (одном HTML или паре .html + .js) встречаются два разных HTML pattern для одного data-attribute / className family (`*offer*`, `*partner*`, `*status*`). Если два разных pattern на одну entity → WARN с предложением вынести в компонент.

## Анти-паттерны (что НЕ делать)

- ❌ Inline HTML для entity которая уже имеет компонент в `components/`
- ❌ Две функции `renderOrderCompact` и `renderOrderFull` в разных файлах
- ❌ Дубликат селектора партнёра: `<select id="expPartnerSelect">` рядом с `<div id="epPartnerSwitcher">` — оба влияют на data, рассинхрон → видишь данные не того партнёра
- ❌ Show «★ базовый» без офферов в этом же контейнере — entity не определена визуально
- ❌ Status badge как `<span class="green">running</span>` в одном месте и `<div class="status-pill">running</div>` в другом

## Использование

- `ui-design-architect` ОБЯЗАН пройти этап «entity reuse audit» перед screen-spec
- `frontend-component-reviewer` ОБЯЗАН проверять при любом *.js > 500 строк нет ли inline renderer'ов entity которые уже есть в `components/`
- `selector-duplication-detector.py` после Pass J расширенно ловит разные визуалы одной entity

## Связанные

- [[wiki/concepts/ab-experiment-product-thinking]] — domain для А/Б (звезда без порядка офферов = anti-pattern)
- [[wiki/concepts/ui-grid-discipline]] — общая сетка
- [[wiki/concepts/html-report-design-system]] — design tokens
- `~/.claude/agents/ui-design-architect.md` — entity-reuse audit step
- `~/.claude/agents/frontend-component-reviewer.md` — inline-renderer check
- `/Users/<you>/claude-hooks/selector-duplication-detector.py` — extended in Pass J
