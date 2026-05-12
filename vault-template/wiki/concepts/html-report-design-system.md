---
type: concept
slug: html-report-design-system
tags: ["html", "design", "report"]
related: ["[[wiki/concepts/design-balance]]", "[[wiki/projects/product-team]]"]
created: 2026-04-29
updated: 2026-04-29
recency: 2026-04-29
confidence: high
---

# Дизайн-система HTML-отчётов

## Суть
- Reference: `Projects/product-team/docs/delivery-skills.html`.
- Шрифт Inter через `@import` внутри `<style>`. Для зашифрованных страниц после `document.replaceChild()` инжектить `<link>` отдельно.
- Контейнер max-width 1040px, не шире.
- Хедер: градиент 135deg (#7c3aed → #a78bfa) + цветная полоска 4px снизу.
- Sticky nav, нумерованные секции (бейдж 28px), карточки с тенью + accent border-left, тёмные `<th>` (#1f2937 + white).
- Светлая тема всегда. Чего не делать: max-width >1040, плоский хедер, светло-серые `<th>`, `<link>` на шрифты вместо `@import`.

## Сохранено из memory: feedback_html_report_design.md

Все HTML-отчёты должны использовать дизайн-систему из `Projects/product-team/docs/delivery-skills.html`. Не изобретать новые стили — копировать эту базу.

**Why:** Пользователь дважды ругался на уродливые шрифты и растянутый layout. Отчёт delivery-skills.html — эталон, который он одобрил.

**How to apply:** При создании любого HTML-отчёта использовать CSS ниже как базу. Не отклоняться.

**Pipeline:** сначала взять approved reference из проекта, затем собрать локальный visual-doc, затем обязательно проверить в браузере, и только потом публиковать через `html-push`. HTML-отчёт должен быть визуальным документом, а не текстовым summary в HTML-обёртке.

## Обязательные элементы

### 1. Шрифт — Inter через @import (внутри `<style>`)
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
body { font-family: 'Inter', -apple-system, sans-serif; font-size: 15px; line-height: 1.6; }
```
`@import` внутри `<style>` для локального просмотра. **Для зашифрованных страниц** скрипт расшифровки ОБЯЗАН инжектить `<link>` на Google Fonts после `document.replaceChild()` — `@import` не срабатывает при динамической вставке HTML.

### 2. Контейнер — 1040px, не шире
```css
.container { max-width: 1040px; margin: 0 auto; padding: 0 24px; }
```

### 3. Хедер — градиент с цветной полоской снизу
```css
.header {
  background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 50%, #a78bfa 100%);
  color: white; padding: 48px 0 56px; position: relative; overflow: hidden;
}
.header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #f59e0b, #f97316, #f59e0b); }
.header h1 { font-size: 32px; font-weight: 800; letter-spacing: -0.5px; }
.header .subtitle { font-size: 16px; opacity: 0.85; }
.header .meta { margin-top: 20px; font-size: 13px; opacity: 0.7; }
```
Цвет градиента можно менять под тему отчёта (синий, зелёный и т.д.), но формат тот же.

### 4. Навигация — sticky, белая, тонкий шрифт
```css
.nav { background: white; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; z-index: 100; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.nav a { padding: 12px 10px; color: #6b7280; font-size: 11px; font-weight: 500; white-space: nowrap; border-bottom: 2px solid transparent; }
.nav a:hover { color: #8b5cf6; }
```

### 5. Секции — с нумерованными бейджами
```css
section { padding: 40px 0; border-bottom: 1px solid #e5e7eb; scroll-margin-top: 52px; }
h2 { font-size: 22px; font-weight: 700; }
h2 .num { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: #8b5cf6; color: white; border-radius: 7px; font-size: 13px; font-weight: 700; margin-right: 8px; }
.section-desc { color: #6b7280; font-size: 14px; margin-bottom: 24px; }
```

### 6. Карточки — белые с тенью и accent border
```css
.card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06); margin-bottom: 14px; border: 1px solid #f3f4f6; }
.card-accent { border-left: 4px solid #8b5cf6; }
```

### 7. Таблицы — ТЁМНЫЙ заголовок (gray-800), белый текст
```css
.ref-table th { background: #1f2937; color: white; padding: 10px 14px; font-size: 12px; font-weight: 600; }
.ref-table td { padding: 10px 14px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
.ref-table tr:nth-child(even) td { background: #f9fafb; }
```

### 8. Цветовая палитра (CSS variables)
```css
:root {
  --primary: #2563eb;
  --primary-light: #dbeafe;
  --accent: #f59e0b;
  --success: #10b981;
  --danger: #ef4444;
  --purple: #8b5cf6;
  --teal: #14b8a6;
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-500: #6b7280;
  --gray-700: #374151;
  --gray-800: #1f2937;
  --gray-900: #111827;
  --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --radius: 12px;
}
```

### 9. Бейджи/теги
```css
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
```
Варианты: badge-blue, badge-green, badge-yellow, badge-red, badge-purple.

### 10. Светлая тема ВСЕГДА
Фон: `#f9fafb`. Карточки: `white`. Текст: `#1f2937`. Никогда тёмную тему.

## Чего НЕ делать
- max-width > 1040px (было 1200px — растянуто, ужасно)
- Плоский белый хедер без градиента
- Светло-серые заголовки таблиц (нечитаемо)
- `<link>` теги для шрифтов вместо `@import` (ломается в зашифрованных страницах)
- Секции без номеров — теряется структура
- font-size body > 15px
