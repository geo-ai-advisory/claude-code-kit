# Installer step 07 — Verify

Цель: проверить что всё установилось правильно и работает в живой сессии.

## Чеклист

### A. Файлы на местах

```bash
echo "=== Agents ==="
ls ~/.claude/agents/*.md 2>/dev/null | wc -l
echo

echo "=== Hooks ==="
ls ~/claude-hooks/*.py 2>/dev/null | wc -l
echo

echo "=== Skills ==="
ls -d ~/.claude/skills/*/ 2>/dev/null | wc -l
echo

echo "=== Config ==="
ls -la ~/.claude/CLAUDE.md ~/.claude/settings.json 2>&1 | head -5
echo

echo "=== Vault ==="
ls -la "$VAULT_DIR/CRITICAL_FACTS.md" "$VAULT_DIR/_index.md" "$VAULT_DIR/_CLAUDE.md" 2>&1 | head -5
```

Минимум:
- Agents: ≥ 5
- Hooks: ≥ 10
- Skills: ≥ 5
- CLAUDE.md и settings.json — оба файла на месте
- Vault: 3 файла (CRITICAL_FACTS, _index, _CLAUDE) присутствуют

### B. settings.json синтаксически валиден

```bash
python3 -c "
import json
with open('$HOME/.claude/settings.json') as f:
    s = json.load(f)
hooks_count = sum(len(g['hooks']) for events in s.get('hooks', {}).values() for g in events)
print(f'✓ settings.json valid, {hooks_count} hooks registered')
"
```

### C. Hooks syntax (Python)

```bash
for h in ~/claude-hooks/*.py; do
    if ! python3 -c "import py_compile; py_compile.compile('$h')" 2>/dev/null; then
        echo "❌ syntax error: $h"
    fi
done
echo "✓ all hooks have valid syntax"
```

### D. Claude Code перезапущен

```bash
pgrep -lf "Claude.app" | head -3
```

Если процесс старый (запущен ДО изменений) — попроси пользователя сделать Cmd+Q + open.

### E. Live тест в новой сессии

Скажи пользователю:

> Перезапусти Claude Code (Cmd+Q + open). Открой ту же папку. Напиши мне `/sb-start` или скажи «прочитай vault и проверь что CRITICAL_FACTS подгрузились».

Жди ответ. Если в системном контексте появилось содержимое `CRITICAL_FACTS.md` — vault-bootstrap hook работает.

### F. Тест агента

Скажи пользователю: «Попроси Claude сделать что-то UI-related — что-нибудь маленькое». Например «добавь button в этот HTML».

В новой сессии после Edit должен сработать `ui-auto-review.py` hook — выдаст hint про вызов ui-quality-reviewer. Это значит pipeline работает.

### G. Финальный отчёт

Создай файл `~/claude-install-journal/<date>-DONE.md`:

```markdown
---
type: install-complete
date: <YYYY-MM-DD>
duration_minutes: <время>
---

# Installation Complete

## Установлено

| Компонент | Количество |
|---|---|
| Agents | <N> |
| Hooks | <N> |
| Skills | <N> |
| Vault concepts | <N> |

## Проверки PASS

- [x] Файлы на местах
- [x] settings.json valid
- [x] Hooks syntax OK
- [x] Claude Code перезапущен
- [x] Vault bootstrap работает (CRITICAL_FACTS в контексте)
- [x] Hooks стреляют (тестовый Edit показал hint)

## Custom agents добавленные пользователем

<список>

## Open questions (на будущее)

<список из step 03 если откладывали>

## Следующие шаги для пользователя

1. Поработать 1-2 дня — посмотреть какие hooks реально полезны, какие шумят
2. Через неделю — `/sb-recap 20` чтобы консолидировать первые сессии в wiki
3. Если какой-то агент мешает — удалить его из `~/.claude/agents/`
4. Если какой-то hook слишком шумит — закомментировать в settings.json
5. Создавать новых custom-агентов под domain по мере того как появляются повторяющиеся задачи
```

## Если что-то не работает

| Симптом | Что проверить |
|---|---|
| Hooks не стреляют | Перезапуск Claude Code; правильный JSON в settings.json; права на исполнение `.py` |
| Vault context не появляется на старте | `vault-bootstrap.py` имеет правильный VAULT_DIR; SessionStart hook зарегистрирован |
| Slash skills не видны | Cmd+Q + open; папки в `~/.claude/skills/` имеют `SKILL.md` внутри |
| Agents не вызываются автоматически | `description:` начинается с `Use PROACTIVELY when...`; orchestration-hint hook работает |
| Permission denied на чем-то | `chmod -R u+w ~/.claude/ ~/claude-hooks/`; пользователь должен дать Accessibility/Microphone в System Settings |

## Done

Если все 7 чеков PASS — установка завершена.

Скажи пользователю:

> Готово. Система установлена. Поработай 1-2 дня — посмотри что полезно, что мешает. Через неделю запусти `/sb-recap` чтобы консолидировать первые сессии в wiki. Если какой-то агент или hook оказывается шумным — скажи мне, выключу.

Запиши финальный отчёт. Установка закончена.
