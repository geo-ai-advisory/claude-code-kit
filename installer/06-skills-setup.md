# Installer step 06 — Skills setup

Цель: установить slash-команды (skills) которые упрощают часто-используемые действия. Не все нужны всем — выбираем по релевантности.

## Skills в kit

| Skill | Что делает | Кому нужен |
|---|---|---|
| `/check-ui <file>` | Делегирует ui-quality-reviewer на конкретный HTML/CSS | Всем кто делает UI |
| `/check-consistency <file>` | Делегирует consistency-checker (числа, sum-detail, wikilinks) | Reports / отчёты |
| `/check-scenarios <file>` | Прогон qa-scenario-tester по всем сценариям | Dashboard / интерактивные UI |
| `/sb-start` | Vault entry-point ритуал (читает CRITICAL_FACTS, _index, log.md tail) | Всем с vault'ом |
| `/sb-recap [N]` | Синтез последних N session entries в `wiki/synthesis/<date>.md` | Всем с vault'ом (раз в неделю) |

## Установка

```bash
KIT_DIR="$(pwd)"
SKILLS_DEST="$HOME/.claude/skills"

mkdir -p "$SKILLS_DEST"

# Все 5 universal skills
for skill in check-ui check-consistency check-scenarios sb-start sb-recap; do
    src="$KIT_DIR/skills/$skill"
    if [ -d "$src" ]; then
        cp -R "$src" "$SKILLS_DEST/"
        echo "✓ installed: /$skill"
    fi
done

ls -d "$SKILLS_DEST"/*/ | head -10
```

## Проверка что skills видны

После Cmd+Q → open Claude Code заново, проверь:

```
В Claude Code: /
```

Должны появиться `/check-ui`, `/check-consistency`, `/check-scenarios`, `/sb-start`, `/sb-recap` в списке доступных skills.

## Кастомизация

Skills могут содержать project-specific логику. Например `/sb-start` читает vault — путь к vault указан в `sb-start/SKILL.md`. Замени на свой:

```bash
$EDITOR "$SKILLS_DEST/sb-start/SKILL.md"
# Найди путь к vault — замени Projects/<your-vault>/ на твой path
```

## Создание собственных skills

Базовый шаблон skill:

```
~/.claude/skills/<your-skill>/
├── SKILL.md        # инструкция Claude как этот skill работает
└── helpers/        # опционально — скрипты, шаблоны
```

`SKILL.md` структура:

```markdown
---
name: <your-skill>
description: <Когда вызывать>
---

# /your-skill

## Что делает

<1 параграф>

## Когда вызывать

- /your-skill
- "<триггерная фраза 1>"
- "<триггерная фраза 2>"

## Workflow

1. <Step 1>
2. <Step 2>
3. ...

## Параметры

<args description>

## Output

<что возвращает>
```

## Связь skills и agents

Skill ≠ Agent. Различие:
- **Agent** — отдельная подсессия с инструкцией. Вызывается через Task tool.
- **Skill** — slash-команда. Это инструкция main-session что сделать.

Часто skill вызывает внутри себя agent через Task. Например `/check-ui <file>` делегирует `ui-quality-reviewer` subagent через Task tool.

## Запиши в журнал

```bash
cat >> ~/claude-install-journal/<date>-scan.md <<EOF

## Skills (step 06)
$(ls -d $SKILLS_DEST/*/ | xargs -n1 basename | sed 's/^/- /')
EOF
```

После завершения — переходи к **step 07 — verify**.
