# Architecture — как всё устроено

## Слои

```
┌─────────────────────────────────────────────────────────────────┐
│                    User prompt                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ UserPromptSubmit hook: prompt-orchestration-hint.py             │
│ 23 regex pattern → подсказывает каких subagents вызвать         │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                Claude main session                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  Глобальный context (загружается на SessionStart):          │ │
│ │  • ~/.claude/CLAUDE.md — HARD rules                         │ │
│ │  • ~/.claude/settings.json — hooks конфиг                   │ │
│ │  • vault/CRITICAL_FACTS.md — through vault-bootstrap.py     │ │
│ │  • vault/_index.md — каталог                                │ │
│ │  • vault/log.md tail — последние сессии                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Делает Edit/Write/Bash/Task → срабатывают PreToolUse hooks      │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ PreToolUse hooks                                                │
│ • brief-gate (UI Edit без brief → hint)                         │
│ • task-delegation-enforcer (≥5 UI-edits без QA-subagent → hint) │
│ • explain-mode-guard (вопрос-объяснение без ответа → hint)      │
│ • bash-large-output-warn                                        │
│ • prod-push-gate (HARD block — push без approve)                │
│ • screenshot-fullpage-block (HARD — > 2000px валит сессию)      │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│              Tool execution                                     │
│ Edit / Write / Bash / Task / mcp__*                             │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ PostToolUse hooks                                               │
│ • ui-auto-review (Edit на *.html/*.css → hint)                  │
│ • consistency-check (изменения в numerical reports)             │
│ • selector-duplication-detector (копипаст между файлами)        │
│ • vault-frontmatter-check (Write на wiki/*.md)                  │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
              [продолжает работу]
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stop hook                                                       │
│ • claim-readiness-validator (claim без QA → hint)               │
│ • session-auto-summary (пишет 3-5 строк в log.md)               │
└─────────────────────────────────────────────────────────────────┘
                      ↓
           [сессия завершена, log.md обновлён]
```

## Где живут компоненты

```
~/.claude/                          # Claude Code workspace
├── CLAUDE.md                       # Глобальные HARD-rules
├── settings.json                   # Hooks конфиг + permissions
├── agents/                         # Субагенты (procedural memory)
│   ├── product-architect.md
│   ├── ui-design-architect.md
│   └── ... (5-23 файла)
├── skills/                         # Slash-команды
│   ├── check-ui/SKILL.md
│   ├── sb-start/SKILL.md
│   └── ...
└── projects/                       # Transcripts сессий (read-only для hooks)

~/claude-hooks/                     # Python hook scripts
├── brief-gate.py
├── claim-readiness-validator.py
├── vault-bootstrap.py
└── ... (10-22 файла)

~/Documents/second-brain/           # Obsidian-vault (выбирает user)
├── CRITICAL_FACTS.md               # Working memory (всегда в контексте)
├── _index.md                       # Каталог vault
├── _CLAUDE.md                      # Operating manual
├── log.md                          # Episodic memory — все сессии
├── wiki/
│   ├── concepts/                   # Semantic memory — стабильные знания
│   ├── decisions/                  # Decision log
│   ├── projects/                   # Per-project pages
│   ├── people/                     # People pages (если team work)
│   ├── partners/                   # Partner pages (если B2B)
│   ├── questions/                  # Open questions
│   ├── references/                 # External references
│   ├── synthesis/                  # Weekly recap files
│   └── daily/                      # Daily notes (если используешь)
└── journals/                       # Per-task working journals
    └── <date>-<topic>/
        ├── log.md
        ├── brief-N.md
        └── screen-spec-N.md
```

## Memory tiers (4-tier из agentmemory)

См. `docs/memory-tiers.md` — детальный mapping.

Кратко:

| Tier | Где | Что |
|---|---|---|
| **Working** | `CRITICAL_FACTS.md` | Всегда в контексте (через SessionStart hook). Бизнес-цели, ID, prod endpoints |
| **Episodic** | `log.md`, `journals/` | Хронология «что было когда» |
| **Semantic** | `wiki/concepts/` | Стабильные знания «что я знаю» |
| **Procedural** | `~/.claude/agents/`, `~/.claude/skills/` | Инструкции «как делать» |

Transfer:
- Working → Episodic: автомат через `session-auto-summary.py` (Stop hook)
- Episodic → Semantic: `memory-consolidator` agent раз в 5-7 сессий
- Semantic → Procedural: вручную через создание subagent / skill

## Compliance — как держится дисциплина

После Pass L все мои UX-блокировки отключены. Compliance держится через:

1. **CLAUDE.md HARD-rules** — модель видит в system context на старте
2. **Agent descriptions с `Use PROACTIVELY when...`** — авто-делегирование
3. **Orchestration hints** через `UserPromptSubmit` hook — подсказки subagents
4. **PostToolUse advisory** — warning после Edit без блокировки
5. **Domain knowledge в vault** (`wiki/concepts/`) — субагенты Read'ают перед screen-spec/brief

Если модель игнорирует всё это — это уже не technical fix, это вопрос промтов в CLAUDE.md и описаний агентов.

## Pipeline для UI-задачи (рекомендованный flow)

```
User: «сделай новый dashboard для X»
    ↓
UserPromptSubmit hook → orchestration hints: product-architect, ui-design-architect
    ↓
Главная модель: вызывает Task(product-architect) — 7+4 продуктовых вопросов
    ↓
brief-<N>.md в journals/<date>-<topic>/
    ↓
User: approve / правки
    ↓
Главная модель: вызывает Task(ui-design-architect)
    ↓
ui-design-architect: Entity reuse audit → 7 design-thinking вопросов → WebFetch 2-3 референса → screen-spec-<N>.md
    ↓
User: approve / правки
    ↓
Главная модель: Edit на HTML/CSS/JS
    ↓ PostToolUse:
ui-auto-review.py hint → вызвать ui-quality-reviewer
consistency-check.py hint → проверить числа
selector-duplication-detector.py hint → если копипаст
    ↓
Главная модель: Task(ui-quality-reviewer) → PASS/FAIL
    ↓
Главная модель: Task(qa-scenario-tester) → прогон сценариев
    ↓ Stop:
claim-readiness-validator.py — если claim «готово» без QA-subagent — hint провести тесты
session-auto-summary.py → пишет в log.md
```

## Что отличает kit от обычного use Claude Code

| Без kit | С kit |
|---|---|
| Claude не помнит предыдущие сессии | Vault держит память между сессиями |
| Каждый раз заново объяснять контекст бизнеса | CRITICAL_FACTS в каждой сессии |
| Делает UI «на коленке» — лидерборд из 7 chips | Pipeline через product-architect + ui-design-architect |
| Говорит «готово» без реальных тестов | claim-readiness hint напоминает о QA-subagent |
| Копипаст между файлами | selector-duplication-detector предупреждает |
| Push в prod без подтверждения | prod-push-gate блокирует через `continue:false` |
| Игнорирует пользовательский вопрос «зачем?», бежит править | explain-mode-guard напоминает ответить текстом |
