# INSTALL.md — точка входа для Claude Code

Этот файл читает **Claude Code пользователя** (не сам пользователь). Запускает 7-шаговый установочный протокол.

## Контракт

Ты — Claude Code. Пользователь дал тебе папку `claude-code-kit/` и попросил установить систему. Не торопись, иди по шагам. На каждом шаге **спрашивай пользователя** про важные решения (какие проекты у него, какие agents он хочет, какие нет).

## Протокол — 7 шагов

Читай и выполняй файлы из `installer/` в порядке:

1. **`installer/00-overview.md`** — общая картина что устанавливается и зачем
2. **`installer/01-scan-projects.md`** — сканирование `~/`, `~/Projects/`, `~/Documents/` чтобы понять стек пользователя (языки, frameworks, типы задач)
3. **`installer/02-shortlist-agents.md`** — на основе стека предлагай подходящих агентов из `agents-library/`
4. **`installer/03-custom-agents.md`** — помоги пользователю написать его собственных агентов под его domain (<industry> / e-commerce / SaaS / fintech / GameDev / etc)
5. **`installer/04-vault-setup.md`** — установка Obsidian-vault из `vault-template/`
6. **`installer/05-hooks-setup.md`** — копирование hooks в `~/claude-hooks/`, регистрация в `~/.claude/settings.json`
7. **`installer/06-skills-setup.md`** — установка slash-skills из `skills/`
8. **`installer/07-verify.md`** — тестовый прогон + чеклист

## Принципы

- **Не ставь всё подряд.** Ставь только то что нужно пользователю под его проекты. Лишние агенты = шум в его контексте.
- **Сначала свои, потом мои.** В первую очередь помогай пользователю описать его собственных агентов под его domain. Мои из `agents-library/` — резервный набор готовых решений.
- **Hooks по умолчанию все advisory.** Никаких hard-block кроме `prod-push-gate.py`. Если пользователь сам захочет — потом включит.
- **Vault обязателен.** Без Obsidian-vault теряется память между сессиями. Это критичный компонент.
- **Спрашивай где не уверен.** Пользователь не разработчик в общем случае. Объясняй простыми словами.

## Финальная проверка после установки

```bash
ls -la ~/.claude/agents/        # должно быть 5-20+ агентов
ls -la ~/claude-hooks/          # 10-22 hooks
ls -la ~/.claude/skills/        # 5+ skills
ls -la ~/Documents/vault/       # или другое место vault'а — установлен
cat ~/.claude/CLAUDE.md         # глобальный CLAUDE.md с HARD-rules
```

Если всё на месте — скажи пользователю «Готово. Перезапусти Claude Code (Cmd+Q + open) чтобы hooks подгрузились. Потом скажи мне новую задачу — попробуем pipeline».

## Если что-то идёт не так

- **Permission denied на `~/.claude/`** — `chmod -R u+w ~/.claude/`
- **Хуки не запускаются после установки** — нужен restart Claude Code (Cmd+Q + open). Settings.json hooks подгружаются только на старте сессии.
- **Vault не открывается в Obsidian** — открой Obsidian.app → Open vault → выбери папку vault'а
- **Агенты не вызываются автоматически** — проверь что в их frontmatter `description:` начинается с `Use PROACTIVELY when...` или похожих триггеров

## Где дальше искать инфу

- `README.md` — общая картина и принципы
- `docs/architecture.md` — как всё устроено внутри
- `docs/memory-tiers.md` — 4-tier memory pattern (working/episodic/semantic/procedural)
- `docs/pass-history.md` — почему хуки в kit устроены именно так, история ошибок и решений
- `docs/faq.md` — частые проблемы
