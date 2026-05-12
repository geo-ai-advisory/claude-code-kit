# Installer step 01 — Scan projects

Цель: понять что у пользователя есть, чтобы потом подобрать релевантных агентов.

## Где искать

Стандартные места проектов на Mac:
- `~/Projects/` — самое частое
- `~/Documents/` — иногда
- `~/Developer/` — Xcode-проекты
- `~/code/`, `~/src/`, `~/dev/` — альтернативные конвенции
- `~/Desktop/` — иногда тут лежат текущие

Спроси пользователя — где у него код. Если он говорит «в Projects» — иди туда. Не сканируй весь `~/` подряд (там много мусора).

## Что собирать (за 1-2 минуты)

```bash
# 1. Список папок проектов
ls -la ~/Projects/ 2>/dev/null | head -30

# 2. Языки и frameworks — самые распространённые расширения
find ~/Projects -maxdepth 3 -type f \( \
    -name "*.cs" -o -name "*.csproj" -o -name "package.json" \
    -o -name "Cargo.toml" -o -name "pyproject.toml" -o -name "requirements.txt" \
    -o -name "Gemfile" -o -name "go.mod" -o -name "pom.xml" \
    -o -name "build.gradle*" -o -name "Package.swift" -o -name "*.xcodeproj" \
    -o -name "Dockerfile" -o -name "docker-compose*" \
    \) 2>/dev/null | head -30

# 3. Frontend frameworks — package.json deps
for pkg in $(find ~/Projects -maxdepth 3 -name "package.json" 2>/dev/null | head -10); do
    echo "=== $pkg"
    grep -E "react|vue|svelte|next|nuxt|angular|astro|solid" "$pkg" 2>/dev/null | head -3
done

# 4. Базы данных — какие миграции / схемы есть
find ~/Projects -maxdepth 3 \( -name "schema.sql" -o -name "migrations" -o -name "prisma" \) 2>/dev/null | head -10

# 5. Тесты — есть ли test/spec структура
find ~/Projects -maxdepth 3 -type d \( -name "tests" -o -name "test" -o -name "__tests__" -o -name "spec" \) 2>/dev/null | head -10

# 6. CLAUDE.md — есть ли уже Claude-конфиги
find ~/Projects -maxdepth 3 -name "CLAUDE.md" 2>/dev/null
find ~/ -maxdepth 2 -name "CLAUDE.md" 2>/dev/null

# 7. Git remotes — какие GitHub/GitLab/Bitbucket
for repo in $(find ~/Projects -maxdepth 3 -name ".git" -type d 2>/dev/null | head -10); do
    echo "=== ${repo%/.git}"
    git -C "${repo%/.git}" remote -v 2>/dev/null | head -2
done
```

## Что искать в коде (минимально, не глубоко)

- **UI / frontend** — *.html, *.css, *.tsx, *.vue, *.svelte, *wwwroot*, *static*, *components*
- **Backend** — *.cs (Controllers/Endpoints), *.py (FastAPI/Django/Flask), *.ts (Express/Nest), *.go, *.rs
- **DB** — *schema*, *migrations*, *.sql, *prisma*, *Entity*
- **Reports/dashboards** — *report*, *dashboard*, *vitrina*, *showcase*
- **A/B / experiments** — *experiment*, *split*, *ab-test*, *variant*
- **Mobile** — *.xcodeproj, *.gradle, AndroidManifest.xml

## Что спросить у пользователя

После технического scan — задай 4 вопроса:

1. **«Какие из этих проектов ты сейчас активно ведёшь?»**
   - Не «какие есть» а **какие в работе** — те и нужны
2. **«Какой тип задач преобладает?»** (для frequency-based приоритизации)
   - Build new features
   - Fix bugs / maintenance
   - Reports / analytics
   - Refactoring
   - Doing reviews of someone else's code
3. **«С чем у тебя обычно случаются проблемы в работе с Claude?»** — это даст подсказку какие hooks реально нужны
   - «Делает не то что просил»
   - «Не тестирует перед "готово"»
   - «Копипаст между файлами»
   - «Пушит в prod без подтверждения»
   - «Не помнит контекст между сессиями»
4. **«Какие у тебя domain-понятия / термины которые Claude должен знать?»**
   - Названия партнёров / клиентов / систем
   - Бизнес-метрики (CR, EPC, retention, MRR)
   - Внутренние ID / ключи / эндпоинты
   - Команда (имена ответственных за зоны)

## Зафиксируй результаты

Создай файл `~/claude-install-journal/<YYYY-MM-DD>-scan.md` с собранной информацией:

```markdown
---
type: install-scan
date: YYYY-MM-DD
---

## Проекты
- <project1>: <stack> — <тип задач>
- <project2>: <stack> — <тип задач>

## Стек
- Backend: <C#/Python/Node/...>
- Frontend: <vanilla JS/React/Vue/...>
- DB: <Postgres/SQLite/...>
- CI/CD: <GitLab/GitHub Actions/...>

## Типы задач
- <feature build / bugfix / reports / refactor>

## Болевые точки в работе с Claude
- <"делает не то что просил" / "пушит без approve" / etc>

## Domain knowledge для CRITICAL_FACTS
- Партнёры/клиенты: <...>
- Внутренние термины: <...>
- ID/ключи: <...>
```

Этот журнал будет твой source of truth для steps 02-07.

## После завершения

Покажи пользователю summary что нашёл (1-2 экрана текста, не больше) и переходи к **step 02 — shortlist agents**.
