# FAQ

## Общие

### Q: Зачем мне это, если Claude Code и так работает?

Стандартный Claude Code:
- Не помнит ничего между сессиями
- Делает UI «на коленке» без продуктового мышления
- Говорит «готово» без реальных тестов
- Пушит в prod без подтверждения
- Игнорирует вопросы пользователя, бежит править

Kit чинит каждое из этого через 4-tier memory, hooks-orchestration и agents pipeline.

### Q: Это для разработчиков или для бизнеса?

Для обоих. У kit разные слои:
- **Agents** для разработки (backend-code-reviewer, database-schema-reviewer)
- **Agents** для product (sprint-prioritizer, feedback-synthesizer)
- **Agents** для отчётов (consistency-checker)
- **Vault** для всех (память между сессиями)

Installer step 02 отфильтрует нерелевантное.

### Q: Сколько времени установка?

30-60 минут активной работы Claude Code + пользователя. Зависит от того сколько custom-агентов вы решите написать сразу.

### Q: Будут ли обновления?

`git pull origin main` подтянет последние улучшения. Конфликты с твоей кастомизацией — реши вручную (kit это template, твой `~/.claude/` уже свой).

## Установка

### Q: Где должен лежать репо kit?

Не важно где — `~/claude-code-kit/`, `~/Projects/claude-code-kit/`, что угодно. Installer работает из любой папки.

### Q: macOS 12 (Monterey) поддерживается?

Большинство hooks и агентов — да. Но VoiceInk (опциональная часть) требует macOS 14.4+. Vault и Obsidian работают на macOS 11+.

### Q: Можно ли только агенты без vault?

Можно, но вы теряете 70% value. Память — главная фича.

### Q: А если у меня уже есть свой Obsidian-vault?

Не смешивайте. Создайте отдельный для работы с Claude. Личные заметки в одном vault, working memory в другом.

## Hooks

### Q: Hooks замедляют работу?

Каждый hook — Python script ~30-100ms. На 5-10 hooks per event — добавляет 200-500ms к каждому tool call. Заметно но не критично.

### Q: Можно ли отключить конкретный hook?

Да. Закомментируйте его в `~/.claude/settings.json` или удалите запись:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit", "hooks": [
        // { "command": "python3 ~/claude-hooks/brief-gate.py", "timeout": 10 },  // disabled
        { "command": "python3 ~/claude-hooks/task-delegation-enforcer.py", "timeout": 10 }
      ]}
    ]
  }
}
```

После Cmd+Q + open подхватится.

### Q: Hooks вообще не стреляют — что делать?

1. Cmd+Q + open Claude Code (settings.json читается на старте)
2. Проверить syntax: `python3 -c "import json; json.load(open('~/.claude/settings.json'))"`
3. Проверить права на `.py`: `chmod +x ~/claude-hooks/*.py`
4. Проверить путь к Python: `which python3` — hooks используют `python3` в PATH

### Q: Hook жалуется в logs но я не вижу его output?

Output hook'а попадает в `additionalContext` который добавляется в system context Claude. Сам Claude видит это, но это **не** в чате. Если хотите видеть — добавьте `print(..., file=sys.stderr)` для дебага.

## Agents

### Q: Как агент узнаёт когда его вызывать?

В description агента: `Use PROACTIVELY when <триггер>`. Claude видит это и решает сам.

Дополнительно `prompt-orchestration-hint.py` сматчит regex в твоём prompt → подскажет каких агентов.

### Q: Можно ли иметь много custom-агентов?

Технически — да. Но если >30 агентов — orchestration hints начинают шуметь. Лучше иметь 10-15 нужных.

### Q: Как удалить агента?

```bash
rm ~/.claude/agents/<agent-name>.md
```

Cmd+Q + open для подхвата.

### Q: Агент не вызывается автоматически — почему?

Проверь:
1. `description` начинается с `Use PROACTIVELY when...` или `Use when...`
2. В `description` есть конкретные триггерные фразы которые могли бы быть в твоём prompt
3. Проверь что Claude знает про агент: спроси «какие у меня агенты установлены?»

## Vault

### Q: Vault в iCloud или локально?

Лучше iCloud (`~/Library/Mobile Documents/com~apple~CloudDocs/...`) если хочешь синк между Mac'ами. Локально (`~/Documents/`) если только один Mac.

### Q: CRITICAL_FACTS должен быть очень коротким?

< 2000 токенов. Иначе в каждой сессии большая часть system context уходит только на это.

### Q: Что такое semantic vs episodic?

- **Episodic** = «что было когда» (log.md, journals). Хронология.
- **Semantic** = «что я знаю» (wiki/concepts). Стабильные знания.

Когда факт упоминается в нескольких сессиях — пора мигрировать из episodic в semantic.

### Q: Как часто запускать memory-consolidator?

Раз в неделю или когда log.md > 1000 строк.

## VoiceInk

### Q: Зачем VoiceInk если есть macOS Voice Control?

macOS Voice Control:
- Слабый распознавалка для русского
- Не вставляет в активное приложение
- Требует «Hey Siri» или меню

VoiceInk:
- Whisper large-v3-turbo модель (gold standard)
- Hotkey push-to-talk → текст в активное приложение
- Офлайн, не отправляет в облако

### Q: VoiceInk заявлен как paid с trial. Как бесплатно?

Источник на GitHub — GPL v3. Разработчик включил `LOCAL_BUILD` Swift compilation flag который делает `licenseState = .licensed` сразу при init. **Сборка из source через `make local` — полностью без trial, легально.**

См. `voiceink/build-from-source.md`.

### Q: Можно скачать готовый билд без сборки?

Да, мой fork `voiceink-free` (если опубликован) содержит pre-built DMG в Releases. См. `voiceink/README.md`.

## Permissions / TCC

### Q: Каждая пересборка VoiceInk просит permissions заново — почему?

Ad-hoc подпись каждой сборки — уникальная identity для macOS TCC. Старые permissions относятся к старой подписи. Решение: в System Settings → Privacy & Security → Accessibility → удалить старый VoiceInk через "-", добавить текущий через "+".

### Q: Hammerspoon не реагирует на hotkey — что проверить?

System Settings → Privacy & Security → Accessibility → включи Hammerspoon. Без этого глобальные hotkey'и не работают.

### Q: Скрипты hooks читают transcripts из `~/.claude/projects/...` — это безопасно?

Hooks работают от твоего пользователя, читают только то что Claude Code и так пишет. Никакой эскалации привилегий.

## Production push

### Q: Hook prod-push-gate.py блокирует мой git push — как обойти?

Скажи в свежем prompt «ок пуш» / «выкатывай» / «деплой». Hook найдёт approve в последних 30 user-сообщениях и пропустит.

Если force-push нужен — нужна **дополнительная** фраза «force ок» / «знаю про force».

### Q: Как полностью отключить prod-push-gate если он мешает?

Удали из settings.json в Bash matcher:

```json
"matcher": "Bash",
"hooks": [
  // { "command": "python3 ~/claude-hooks/prod-push-gate.py", "timeout": 10 }  // disabled
]
```

Cmd+Q + open.

## Troubleshooting

### Q: Hooks работают, но `vault-bootstrap.py` ничего не инжектит — почему?

Проверь:
1. Путь к vault в начале `vault-bootstrap.py` правильный
2. `CRITICAL_FACTS.md` существует в этом пути
3. Запусти hook вручную: `echo '{}' | python3 ~/claude-hooks/vault-bootstrap.py` — должен напечатать JSON с `additionalContext`

### Q: «Hook timeout» в Claude Code

Hook должен завершиться за `timeout` секунд. Если читает большие файлы — увеличь timeout в settings.json:

```json
{ "command": "python3 ~/claude-hooks/heavy-hook.py", "timeout": 30 }
```

### Q: Slash skill не виден в списке — что проверить?

1. Папка `~/.claude/skills/<name>/` существует
2. Внутри есть `SKILL.md` с frontmatter (`name: <name>`)
3. Cmd+Q + open

### Q: Subagent не возвращает результат

Возможные причины:
1. Subagent зашёл в цикл — отмени через Ctrl+C
2. Subagent ждёт permissions которых нет — проверь settings.json `permissions.additionalDirectories`
3. Subagent упёрся в hook который заблокировал — проверь `~/claude-hooks/*.py` логи (если есть)
