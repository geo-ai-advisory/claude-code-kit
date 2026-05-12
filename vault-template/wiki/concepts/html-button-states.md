---
type: concept
slug: html-button-states
tags: ["html", "ui"]
related: ["[[wiki/concepts/html-report-design-system]]"]
created: 2026-04-29
updated: 2026-04-29
recency: 2026-04-29
confidence: high
---

# HTML — состояния кнопок: default / hover / active

## Суть
- У всех кнопок, CTA, nav-pills, tabs — минимум 3 визуально различимых состояния.
- `cursor: pointer`, `transition`, заметный `hover` (фон / border / shadow / lift), отличный от него `active`.
- Перед отдачей HTML визуально проверять именно интерактивность, а не только layout.

## Сохранено из memory: feedback_html_buttons_states.md

Во всех HTML-артефактах кнопки и кликабельные controls должны иметь минимум 3 визуально различимых состояния: **default / hover / active (pressed)**. По элементу должно быть сразу понятно, что это кнопка.

**Why:** Пользователь резко реагирует на «мертвые» кнопки без наведения и без pressed-state — это выглядит как сломанный UI и ломает доверие к артефакту.

**How to apply:**
1. Для всех кнопок, CTA, nav-pills, tabs и secondary actions задавать `cursor: pointer`, `transition` и минимум 3 состояния.
2. `hover` должен быть заметным: фон / border / text / shadow / lift должны меняться.
3. `active` должен отличаться от `hover` и `default`.
4. Перед отдачей HTML визуально проверять именно интерактивность, а не только layout.
5. Если есть меню или pills, считать их такими же controls, как обычные кнопки.
