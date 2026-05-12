# Hooks Library — каталог

22 hook для Claude Code на macOS. Разбиты на 4 категории — `advisory/`, `safety/`, `session/`, `hard-block/`.

## advisory/ — 15 hint-only hooks (не блокируют, дают подсказки)

Урок Pass G-L (см. `docs/pass-history.md`): hard-block `continue:false` превращает помощника в надсмотрщика. Все эти hooks — **только hint** через `additionalContext` или `systemMessage`.

| Hook | Когда стреляет | Что советует |
|---|---|---|
| `brief-gate.py` | PreToolUse Write\|Edit на UI-файл (HTML/CSS/JS) | Рекомендует вызвать product-architect + ui-design-architect ДО Edit |
| `task-delegation-enforcer.py` | PreToolUse Write\|Edit на UI | После 3-5 UI-edits без UI-review subagent — hint вызвать ui-quality-reviewer / qa-scenario-tester |
| `explain-mode-guard.py` | PreToolUse Edit/Bash | Если в свежем user prompt explain-pattern (`зачем / почему / о чём / what / why`) и модель ещё не ответила текстом ≥150 chars — hint «сначала ответь текстом» |
| `claim-readiness-validator.py` | Stop | Если в transcript claim («готово/работает/опубликовано») при ≥5 dashboard edits и 0 qa-subagent — hint провести интеграционный тест |
| `prompt-orchestration-hint.py` | UserPromptSubmit | По 23 regex-паттернам в prompt — подсказывает каких subagents вызвать (product-architect, ui-design-architect, backend-code-reviewer, accessibility-auditor, sprint-prioritizer, и т.д.) |
| `ui-auto-review.py` | PostToolUse Write\|Edit на *.html/*.css | После Edit UI-файла — hint вызвать ui-quality-reviewer |
| `consistency-check.py` | PostToolUse Write\|Edit на *.md / *.html / *.csv | Проверка числовой консистентности (sum-detail, cross-section), wikilinks |
| `selector-duplication-detector.py` | PostToolUse Edit в dashboard | Ловит копипаст JS-функций + разные визуалы одной entity на одной странице |
| `vault-frontmatter-check.py` | PostToolUse Write на wiki/*.md | Проверка YAML frontmatter — type/tags/created/updated |
| `mcp-restart-hint.py` | PostToolUse Bash | Если в команде `claude mcp add` — предупреждает что нужен restart Claude Desktop перед использованием mcp__* tools |
| `session-auto-summary.py` | Stop | Пишет 3-5 строк в `log.md` — topic, top files, top tools, total tool count |
| `bash-large-output-warn.py` | PreToolUse Bash | Если в команде find без пути / git log без лимита / grep -r без include / cat большого .json → warn «запиши в файл, читай через Read offset/limit» |
| `browser-evaluate-warn.py` | PreToolUse browser_evaluate | Если код > 1000 строк — warn |
| `browser-navigate-info.py` | PreToolUse browser_navigate | Контекст inject |
| `db-no-limit-warn.py` | PreToolUse db-query | Если SELECT без LIMIT — warn делегировать db-researcher |

## safety/ — 5 hooks предотвращают session crash

Эти блокируют ad-hoc разрушительные действия которые ВСЕГДА вредят:

| Hook | Что блокирует |
|---|---|
| `screenshot-fullpage-block.py` | `browser_take_screenshot` с `fullPage: true` — full-page screenshot > 2000px валит сессию ошибкой "image exceeds dimension limit" |
| `preview-screenshot-block.py` | То же для `preview_screenshot` |
| `browser-resize-block.py` | `browser_resize` > 1600px |
| `preview-resize-block.py` | То же для `preview_resize` |
| `browser-snapshot-block.py` | `browser_snapshot` если уже сделан в этом turn (дубль) |

Эти HARD-block оправданы — действие технически вредно, без вариантов.

## session/ — 1 hook (vault bootstrap)

| Hook | Когда стреляет | Что делает |
|---|---|---|
| `vault-bootstrap.py` | SessionStart, PostCompact | Читает `CRITICAL_FACTS.md` + `_index.md` + tail `log.md` (15 строк), инжектит в system context новой сессии |

## hard-block/ — 1 hook (деньги в риске)

| Hook | Когда блокирует |
|---|---|
| `prod-push-gate.py` | PreToolUse Bash | Если команда содержит `git push` в shared remote (main/master), `gh release create`, `gh pr merge`, `/html-push`, `/gitlab_push`, `/publick_push` — БЛОКИРУЕТ через `continue:false` если в последних 30 user-сообщениях НЕТ approve-фразы («ок пуш / выкатывай / деплой / можно пушить / залей / approve push / merge it / ship it»). Force-push (`--force`) требует ДОПОЛНИТЕЛЬНО «force ок» / «знаю про force» |

Этот hard-block оправдан тем что push в shared remote = реальные деньги ушли в прод. Пользователь сам выбирает ставить его или нет (опциональный в installer).

## Регистрация в settings.json

См. `claude-config-template/settings.json.template`. Структура:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit", "hooks": [...] },
      { "matcher": "Bash", "hooks": [...] },
      { "matcher": ".*browser_take_screenshot$", "hooks": [...] }
    ],
    "PostToolUse": [...],
    "UserPromptSubmit": [...],
    "Stop": [...],
    "SessionStart": [...],
    "PostCompact": [...]
  }
}
```

## Кастомизация vault-bootstrap.py

`vault-bootstrap.py` имеет hard-coded путь к vault. После установки замени в начале файла:

```python
VAULT_DIR = "/Users/<your-user>/Documents/second-brain"  # твой путь
```

Это единственный hook требующий ручной правки. Остальные универсальны.
