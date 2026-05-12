# Installer step 05 — Hooks setup

Цель: поставить hooks так чтобы они помогали, а не блокировали работу. Урок Pass G-L (см. `docs/pass-history.md`): hard-block превращает помощника в надзирателя.

## Категории hooks в `hooks-library/`

| Категория | Цель | По умолчанию |
|---|---|---|
| **advisory/** | hint-only — печатают `additionalContext`, не блокируют | ВСЕ ставим, фильтруем по релевантности |
| **safety/** | блокируют действия которые валят сессию (full-page screenshot >2000px, resize >1600) | ВСЕ ставим (всем нужно) |
| **session/** | SessionStart bootstrap (vault context в каждую сессию) | ОБЯЗАТЕЛЬНО ставим (vault от step 04 теряет смысл без этого) |
| **hard-block/** | прерывают tool call через `continue:false` | ТОЛЬКО `prod-push-gate.py` если есть push в shared remote |

## Установка скриптов

```bash
KIT_DIR="$(pwd)"  # папка claude-code-kit
HOOKS_DEST="$HOME/claude-hooks"

mkdir -p "$HOOKS_DEST"

# Все advisory
cp "$KIT_DIR/hooks-library/advisory/"*.py "$HOOKS_DEST/"

# Все safety
cp "$KIT_DIR/hooks-library/safety/"*.py "$HOOKS_DEST/"

# Session bootstrap (только vault-bootstrap.py)
cp "$KIT_DIR/hooks-library/session/"*.py "$HOOKS_DEST/"

# Hard-block — спрашиваем пользователя
echo "Установить prod-push-gate.py? (блокирует git push в shared remote без явного 'ок')"
read -p "y/n: " ans
if [ "$ans" = "y" ]; then
    cp "$KIT_DIR/hooks-library/hard-block/"*.py "$HOOKS_DEST/"
fi

chmod +x "$HOOKS_DEST/"*.py
ls -la "$HOOKS_DEST/" | head -25
```

## Кастомизация vault-bootstrap.py

В `vault-bootstrap.py` зашит путь к vault. Замени на путь который пользователь выбрал в step 04:

```bash
VAULT_DIR="$HOME/Documents/second-brain"  # тот же что в step 04

# В vault-bootstrap.py найди VAULT_DIR = "..." и замени:
sed -i '' "s|VAULT_DIR\s*=\s*['\"][^'\"]*['\"]|VAULT_DIR = '$VAULT_DIR'|" "$HOOKS_DEST/vault-bootstrap.py"
```

Проверь что путь правильный:

```bash
grep VAULT_DIR "$HOOKS_DEST/vault-bootstrap.py" | head -3
```

## Регистрация hooks в settings.json

Конфигурация — в `claude-config-template/settings.json.template`. Этот файл нужно адаптировать и сохранить как `~/.claude/settings.json`.

Простой путь — взять template как есть, заменить пути:

```bash
KIT_DIR="$(pwd)"
SETTINGS="$HOME/.claude/settings.json"

# Backup существующих settings если есть
[ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d-%H%M%S)"

cp "$KIT_DIR/claude-config-template/settings.json.template" "$SETTINGS"

# Заменяет /Users/<you>/claude-hooks на $HOOKS_DEST
sed -i '' "s|/Users/<you>/claude-hooks|$HOOKS_DEST|g" "$SETTINGS"

# Проверка валидности JSON
python3 -c "import json; json.load(open('$SETTINGS')); print('✓ JSON valid')"
```

## Что внутри settings.json (общая структура)

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit", "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/brief-gate.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/task-delegation-enforcer.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/explain-mode-guard.py", "timeout": 10 }
      ]},
      { "matcher": "Bash", "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/bash-large-output-warn.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/explain-mode-guard.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/prod-push-gate.py", "timeout": 10 }
      ]},
      { "matcher": ".*browser_take_screenshot$", "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/screenshot-fullpage-block.py", "timeout": 5 }
      ]}
    ],
    "PostToolUse": [
      { "matcher": "Write|Edit", "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/ui-auto-review.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/consistency-check.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/selector-duplication-detector.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/vault-frontmatter-check.py", "timeout": 10 }
      ]}
    ],
    "UserPromptSubmit": [
      { "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/prompt-orchestration-hint.py", "timeout": 10 }
      ]}
    ],
    "Stop": [
      { "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/claim-readiness-validator.py", "timeout": 10 },
        { "type": "command", "command": "python3 ~/claude-hooks/session-auto-summary.py", "timeout": 10 }
      ]}
    ],
    "SessionStart": [
      { "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/vault-bootstrap.py", "timeout": 10 }
      ]}
    ],
    "PostCompact": [
      { "hooks": [
        { "type": "command", "command": "python3 ~/claude-hooks/vault-bootstrap.py", "timeout": 10 }
      ]}
    ]
  }
}
```

## Permissions для hooks

Hooks читают transcripts из `~/.claude/projects/<encoded-path>/<session>.jsonl`. По умолчанию Python имеет доступ.

Если hooks работают с MCP (<your-db>, gitlab, telegram) — нужно добавить permissions в settings.json:

```json
"permissions": {
  "additionalDirectories": [
    "~/.claude/",
    "~/claude-hooks/",
    "~/Documents/second-brain/"
  ]
}
```

## CLAUDE.md (HARD-rules)

Скопируй template глобальных правил:

```bash
[ -f ~/.claude/CLAUDE.md ] && cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak-$(date +%Y%m%d)
cp "$KIT_DIR/claude-config-template/CLAUDE.md.template" ~/.claude/CLAUDE.md

# Адаптируй под пользователя
$EDITOR ~/.claude/CLAUDE.md
# Убери / замени личные данные Geo на пользовательские
# Минимум: "Идентичность" в первой секции
```

## Restart Claude Code

**После всех изменений** — Claude Code нужно перезапустить чтобы подгрузить hooks (settings.json читается только на старте сессии).

```bash
osascript -e 'quit app "Claude"'
sleep 2
open -a Claude
```

Или вручную через Cmd+Q → open.

## Запиши в журнал

```bash
cat >> ~/claude-install-journal/<date>-scan.md <<EOF

## Hooks (step 05)
- Path: $HOOKS_DEST
- Advisory: $(ls $HOOKS_DEST/*.py | wc -l) скриптов
- Hard-block: prod-push-gate $(test -f $HOOKS_DEST/prod-push-gate.py && echo yes || echo no)
- settings.json: deployed at ~/.claude/settings.json
- CLAUDE.md: deployed at ~/.claude/CLAUDE.md
- Claude Code restarted: yes/no
EOF
```

После завершения — переходи к **step 06 — skills setup**.
