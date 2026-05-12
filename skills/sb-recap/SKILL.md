---
name: sb-recap
description: Синтезирует последние N TODO-entries из Projects/<your-vault>/log.md в wiki/synthesis/<date>-recap.md. Запускать раз в неделю или после содержательной работы. Триггер `/sb-recap [N]` где N — количество последних entries (default 10). Решает проблему «Stop hook пишет TODO, но никто не доводит до wiki-страниц». Без MCP — прямой filesystem read/write.
---

# /sb-recap

## Что делает

Stop hook автоматически добавляет в `Projects/<your-vault>/log.md` запись после каждой содержательной сессии:
```
## [YYYY-MM-DD HH:MM] auto | session <id>
- **Files touched (top):** ...
- **Tools:** ...
- **TODO:** human review and write proper wiki entry
```

Проблема: эти TODO висят, никто не превращает их в полноценные `wiki/concepts/<topic>.md` или `wiki/synthesis/<period>-recap.md`. `/sb-recap` решает это.

## Workflow

1. Параметр N (default 10) — сколько последних `auto |` entries обработать.
2. Read `Projects/<your-vault>/log.md` — извлечь N последних `## [YYYY-MM-DD HH:MM] auto | session <id>` блоков.
3. Для каждой entry — найти соответствующий transcript JSONL в `~/.claude/projects/-Users-via-Library-Mobile-Documents-com-apple-CloudDocs-Cursor-cloud-<your-workspace>/<session_id>.jsonl`.
4. Через jq+grep извлечь:
   - main topic сессии (по first/last user prompts + TodoWrite content)
   - какие проекты затронуты (top file paths)
   - какие spec-роли вызывались (subagent_type)
   - решения / факты / новые паттерны (search для слов «решено», «выяснили», «оказалось»)
5. Сгенерировать `Projects/<your-vault>/wiki/synthesis/YYYY-MM-DD-recap-N-sessions.md`:
   ```yaml
   ---
   type: synthesis
   period: YYYY-MM-DD..YYYY-MM-DD
   sessions: N
   created: 2026-MM-DD
   ---

   # Recap: N сессий
   
   ## Главные темы
   - ...
   
   ## Затронутые проекты
   - ...
   
   ## Spec-роли которые сработали
   - ...
   
   ## Найденные паттерны / решения
   - ...
   
   ## Open questions
   - ...
   ```
6. Update `Projects/<your-vault>/_index.md` секция «Synthesis».
7. Прокручиваем log.md — заменяем `TODO: human review` на `→ recapped in [[wiki/synthesis/YYYY-MM-DD-recap]]` для обработанных entries (чтобы не двойной разбор).

## Использование

```
/sb-recap          # последние 10
/sb-recap 30       # последние 30 (за месяц если ~1 сессия/день)
/sb-recap weekly   # все за последние 7 дней по datetime
```

## Что нельзя
- НЕ перезаписывать существующие entries в log.md полностью — только заменить TODO-маркер на ссылку.
- НЕ писать в wiki через MCP пока MCP Obsidian не починен (используй Write напрямую через filesystem).
- НЕ выдумывать паттерны — только то что реально в transcripts.
