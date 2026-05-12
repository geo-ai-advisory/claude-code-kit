---
type: concept
slug: cursor-preview-self-contained
tags: ["html", "preview"]
related: ["[[wiki/concepts/html-report-design-system]]"]
created: 2026-04-29
updated: 2026-04-29
recency: 2026-04-29
confidence: high
---

# HTML для Cursor Preview — self-contained без внешних ресурсов

## Суть
- Картинки — inline base64 (JPEG до ~50 KB), не относительные пути и не data-URI > 100 KB.
- Шрифты — системный font-stack (`-apple-system, BlinkMacSystemFont, 'Inter', sans-serif`), без `@import` Google Fonts.
- Иконки — inline SVG. CSS / JS — только inline в `<style>` / `<script>`.
- `<link rel="stylesheet" href="styles.css">` НЕ работает в Cursor preview / `file://` — каждый HTML инлайнить копию `<style>`.
- Целевой размер итогового HTML — до ~100 KB.

## Сохранено из memory: feedback_html_preview_inline_images.md

Когда пользователь смотрит HTML через Cursor Preview panel — HTML должен быть полностью self-contained. Любой внешний ресурс = триггер повторного рендера / рефреша.

**Why:**
- **Картинки по относительным путям (`./foo.png`)** — Preview не резолвит их как обычный браузер. Появляется битая иконка.
- **`@import url('https://fonts.googleapis.com/...')`** — Preview делает сетевой запрос, шрифт грузится медленно или таймаутит, и превью уходит в цикл рефрешей.
- **ГЛАВНАЯ причина рефреш-цикла: огромный inline base64 в `<img src="data:image/png;base64,...">`**. Подтверждено тройным сравнением 2026-04-21:
  - pay2u-subscription-hunt.html (48 KB, без `<img>`) — не рефрешится.
  - landing-v5-claude.html (60 KB, `<img src="assets/hero-art-v1.png">` + `@import` Google Fonts) — **не рефрешится**. Относительные пути и @import работают нормально.
  - yandex-presentation.html 150 KB с `<img src="data:image/png;base64,...">` на 118 KB — постоянный рефреш.
  - yandex-presentation.html 36 KB с `<img src="./mts-dashboard-20d.png">` (картинка рядом в папке) — рефреш прекращается.
  - Значит: **огромный data-URI внутри HTML** (конкретно 100+ KB base64) — единственное что триггерит reload-цикл. Preview, видимо, заново парсит/декодирует его на каждом тике.
- **Относительные пути РАБОТАЮТ** если картинка реально лежит рядом. Раньше она не грузилась, потому что я писал в main-папку, а Preview смотрел в worktree (путь не резолвился). Когда PNG и HTML в одной папке worktree — относительный путь ок.
- **iCloud, `@import` Google Fonts, размер файла в целом — НЕ причины**. Не тратить время на пережатие картинки, удаление шрифтов или перенос из iCloud. Всё это — мимо.

**Практический рецепт для HTML в Cursor Preview — окончательный (проверено 2026-04-21 через playwright + http.server):**

- **Cursor Preview НЕ грузит картинки по относительным путям** ни `./foo.png`, ни `assets/foo.png`, хотя через http-сервер всё работает. Проверено: тот же файл через `python -m http.server` + playwright показывает картинку, через Cursor Preview — не показывает. Это специфика Cursor Preview.
- **Единственный надёжный способ — inline base64**, но:
  - Сжатый JPEG до ~30–50 KB (quality 70–80, resize до ≤1400 px по широкой стороне).
  - Не инлайнить оригинальные PNG на 100+ KB — это и триггерит рефреш-цикл.
- **Целевой размер итогового HTML — до ~100 KB.** AI-лендинг (landing-v5-claude.html, 60 KB с relative img) — не рефрешится, но у него preview работает через внешние пути (почему — хз, возможно более новая версия Cursor или другой контекст). Мой yandex-presentation 150 KB c base64 118 KB — рефрешился. Сжатый до 88 KB с base64 38 KB — не рефрешится, картинка видна.
- **Рецепт сжатия через Pillow в venv** (Pillow на macOS system Python не ставится из-за PEP 668):
  ```bash
  python3 -m venv /tmp/pilvenv && /tmp/pilvenv/bin/pip install --quiet Pillow
  /tmp/pilvenv/bin/python3 -c "
  from PIL import Image; import io, base64, pathlib, re
  img = Image.open('in.png').convert('RGB')
  if img.size[0] > 1400:
      img = img.resize((1400, int(img.size[1]*1400/img.size[0])), Image.LANCZOS)
  buf = io.BytesIO(); img.save(buf, format='JPEG', quality=75, optimize=True, progressive=True)
  b64 = base64.b64encode(buf.getvalue()).decode()
  # replace in HTML: src=\"data:image/jpeg;base64,{b64}\"
  "
  ```
- **sips (macOS native) не уменьшает размер** как ожидается — не использовать, только Pillow.
- **`@import` Google Fonts, iCloud, относительные пути сами по себе — НЕ причины рефреша**. Причина именно в гигантском data-URI внутри `<img src>`.
- **Inline SVG (`<svg>...</svg>`) — всегда ок**, это не data-URI.
- **Пользователь всегда работает через Preview panel**, так что исходить надо из ограничений превью, а не обычного браузера.

**How to apply:**
- **Картинки инлайнить как base64**: `<img src="data:image/png;base64,...">`. Рецепт: Python/Node читает PNG, `base64.b64encode`, replace в HTML. Не пытаться вставлять 100+KB строки через Edit-tool — использовать Python-скрипт.
- **Шрифты — только системный font-stack**: `font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;`. Inter часто уже установлен локально, а если нет — SF Pro / BlinkMacSystemFont выглядят не хуже для презентаций. НЕ использовать `@import` Google Fonts для превью-артефактов.
- **Иконки — inline SVG**, не внешние иконпаки.
- **CSS/JS — только inline в `<style>` и `<script>`**, никаких `<link rel="stylesheet" href="...">` (даже на ЛОКАЛЬНЫЙ relative `styles.css`!) и `<script src="...">` с внешними URL.

**ЖЁСТКОЕ ПРАВИЛО (нарушалось 2026-04-24, скриншот без стилей):** `<link rel="stylesheet" href="styles.css">` НЕ работает в Cursor preview / при открытии через `file://`, даже если файл реально лежит рядом. Подтверждено: пользователь открыл HTML, вёрстка плоская — стили не подхватились. Multi-page-документация с общим внешним CSS — всегда inlining: каждая страница получает копию `<style>` целиком в `<head>`. Делать через Python-скрипт (читает styles.css, делает `re.sub` на `<link rel="stylesheet">` → `<style>...</style>`). НЕ полагаться на симлинки, относительные пути, http-сервер — пользователь смотрит через Cursor preview / file://, и там это не работает. Каждый раз, когда правится общий CSS — пере-инлайнить во все HTML.
- PNG до ~1MB можно смело инлайнить — 1-страничная презентация не страдает.
- Для публикации через html-push self-contained HTML тоже удобнее — ничего дополнительно копировать не надо.
- Проверка: если в `<head>` есть строки `@import url(http...)`, `<link ... href="http...">`, `<script src="http...">`, `<img src="./...">`, `<img src="http...">` — всё переделать на inline/base64/системное.
