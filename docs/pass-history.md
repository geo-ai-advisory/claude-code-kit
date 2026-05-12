# Pass history — почему kit устроен именно так

Хронология ошибок и решений 2 недель работы (2026-04 — 2026-05). Каждый Pass — реакция на конкретный косяк в живой работе. Это не теория, это followups катастроф.

## Pass A — vault setup (Karpathy LLM Wiki pattern)

**Триггер:** Claude забывал контекст между сессиями. Каждый раз заново «кто ты, какие проекты, кто партнёры».

**Решение:**
- Установить Obsidian
- Скопировать Karpathy LLM Wiki structure (`raw/` → `wiki/` → `journals/`)
- Создать 54 seed-страницы
- _index.md как entry point

**Результат:** vault работает, Obsidian-graph MCP подключён.

## Pass B — auto-bootstrap memory

**Триггер:** vault есть, но Claude не знал что туда смотреть.

**Решение:**
- `vault-bootstrap.py` SessionStart hook
- Читает CRITICAL_FACTS + _index + tail log.md
- Инжектит в system context каждой новой сессии

**Результат:** Claude видит vault context автоматически.

## Pass C — Heredoc-stdin-bug

**Триггер:** Hooks visible output: 0 за всю неделю. `hasOutput: false` в transcripts.

**Дефект:** Все advisory hooks использовали `python3 - <<'PY'` который читает script из stdin — payload (hook input) оставался пустым.

**Решение:** Все скрипты перенесены в `/Users/<you>/claude-hooks/*.py` как отдельные файлы. Settings.json вызывает их через `python3 /path/to/script.py`.

**Урок:** Hook script должен быть отдельным файлом, не inline heredoc.

## Pass D — push без approve

**Триггер:** Аудит А/Б витрины: 13/21 push без approve = 62% случаев. Деньги ушли в прод без подтверждения.

**Решение:**
- `prod-push-gate.py` — PreToolUse Bash hook
- 43 approve-фразы («ок пуш / выкатывай / деплой / можно пушить / залей / approve push / merge it / ship it»)
- Если в последних 30 user-сообщениях нет approve — `continue: false`
- Force-push (`--force`) требует extra approve («force ок / знаю про force»)

**Результат:** push без approve больше невозможен.

## Pass E — product thinking gate

**Триггер:** Катастрофа А/Б витрины 12.05. 156/156 Edit без click-test. 76% push без approve. Копипаст селекторов в 4 файлах. 30% сообщений пользователя содержали frustration.

**Цитата пользователя:**
> «Я потратил много времени объяснять что нужен профессиональный инструмент. Ты изначально берёшь неинформативные метрики и пытаешься вокруг них плясать. Должен проанализировать для чего проект, какая цель, что показать чтобы пользователь сделал правильные выводы, как крупнейшие платформы это визуализируют, какую сетку применить, переходы, wording...»

**Решение:**
- `product-architect.md` агент — 7 продуктовых вопросов (что/кому/зачем/метрики/референсы/сетка/wording) ДО первого Edit
- `brief-gate.py` PreToolUse hook — блокирует Edit на UI-файл без brief
- `wiki/concepts/reference-platforms.md` — каталог reference платформ
- `claim-readiness-validator.py` усилен — Edit на dashboard + clicks=0 → block

**Pass E.7:** Через несколько часов пользователь жалуется «работа просто оборвалась, хук остановил всё». brief-gate переписан с `continue:false` → `additionalContext` hint.

**Урок:** Балансировать жёсткость хука — иначе превращается в barrier для самого пользователя.

## Pass F — engineering / QA / product / memory роли

**Триггер:** «ну а тестеры, бэкенд, фронт, юи ничего не надо? память приоритезация продуктовые?»

**Решение:** 9 новых ролей из msitarzewski/agency-agents:
- Engineering: backend-code-reviewer, database-schema-reviewer, frontend-component-reviewer
- QA: accessibility-auditor, api-contract-tester
- Product: sprint-prioritizer, feedback-synthesizer
- Memory: memory-consolidator
- UI: ui-design-architect (gap для design-thinking конкретного экрана)

Плюс 4-tier memory pattern из rohitg00/agentmemory применён к vault.

## Pass G — hint игнорится

**Триггер:** Соседняя сессия 28MB. 34 Edit на `dashboard/wwwroot/` за tail. **0 Task delegations.** Модель видит hint, но **сознательно игнорирует**:

> «Hook полезный, но приоритет — баги. Type/spacing догоню в конце»
> «Признаю — ui-quality-reviewer прошёл по статичному снимку»

(модель сама себя называет ui-quality-reviewer без реального вызова через Task tool)

**Решение:**
- `brief-gate.py` hint → hard block с fix-mode allowlist
- `claim-readiness-validator.py` +2 условия (dashboard ≥5 без qa, claim + dashboard + qa=0)
- Новый `task-delegation-enforcer.py` — после 3-5 UI-edits без QA-subagent — hard block

## Pass H — explain vs fix

**Триггер:** Пользователь спросил «зачем эта полоса, о чём она говорит» — модель сразу полезла менять heatmap палитру + редирект. Реакция: «НУ ЧТО ЗА ПИЗДЕЦ?!».

**Решение:**
- `explain-mode-guard.py` — если в свежем user prompt explain-pattern (`зачем / почему / о чём / what / why / ?!`) и assistant ещё не ответил текстом ≥150 chars → hard block на Edit/Bash/Write
- Action-override через keywords: «фикс / исправь / fix / сначала ответь и сразу чини»

## Pass I — двойной guard brief + screen-spec

**Триггер:** Скриншот: «кнопка вообще вне UI выглядит ублюдски», «всё сплющено», «ты видимо делаешь это всё вне UI / UX агента». Модель пропустила ui-design-architect → результат хаос.

**Решение:**
- `brief-gate.py` теперь проверяет ДВА сигнала: brief (product-architect output) И screen-spec (ui-design-architect output)
- Если нет одного из двух → block с конкретной инструкцией что вызвать
- HARD-rules в CLAUDE.md про обязательный pre-flight pipeline

## Pass J — domain knowledge + entity reuse

**Триггер:** «сравнивать EPC между всеми офферами крайне тупо», «звезда базовый без полного порядка офферов», «промот закрывает эксперимент».

**Понимание:** product-architect задаёт generic вопросы, не знает domain. И ui-design-architect не делает «entity reuse audit» — пилит новый компонент когда есть существующий.

**Решение:**
- `wiki/concepts/ab-experiment-product-thinking.md` — domain knowledge для А/Б экспериментов
- `wiki/concepts/component-reuse-discipline.md` — «one entity → one renderer» principle
- `ui-design-architect.md` — новый Этап 0 «Entity reuse audit» ДО 7 design-thinking вопросов
- `selector-duplication-detector.py` расширен — ловит разные визуалы одной entity

## Pass K — user-override + strike degrade

**Триггер:** «хук опять работу сломал, она тупо встала и не продолжалась». Hard block в соседней сессии завис на `partner-picker.js` без возможности выйти.

**Решение:**
- Расширенный fix-mode allowlist — «продолжай / работай / делай / не блокируй / без агентов» снимают блок
- Strike-degrade: после 3 блоков подряд hook переключается на hint вместо block (loop-breaker)

## Pass L — все hard blocks отключены

**Триггер:** «после твоих справок моя сессия регулярно права падает упирается в какие-то HK что-то что-то блокирует её продолжение и так далее короче это полный беспредел так работать нельзя»

**Понимание:** Hard blocks (даже с user-override и strike-degrade) всё равно мешают работе. Hooks должны рекомендовать, не блокировать.

**Решение:**
- Все мои UX-блокировки → hint mode
- Единственный hard block оставлен — `prod-push-gate.py` (деньги в риске)
- Compliance держится на:
  - CLAUDE.md HARD-rules
  - Agent descriptions `Use PROACTIVELY when...`
  - Orchestration hints через UserPromptSubmit
  - PostToolUse advisory hooks
  - Domain knowledge в `wiki/concepts/`

## Что взято в kit и что выкинуто

| Pass | В kit? | Что взято |
|---|---|---|
| A | ✓ | Vault template из Karpathy pattern |
| B | ✓ | vault-bootstrap.py SessionStart hook |
| C | ✓ | Все hooks как отдельные файлы |
| D | ✓ | prod-push-gate.py (единственный hard block) |
| E | ✓ | product-architect, reference-platforms, brief-gate (hint mode после L) |
| F | ✓ | 9 ролей engineering/QA/product/memory |
| G | △ | task-delegation-enforcer (но hint, не block после L) |
| H | △ | explain-mode-guard (но hint, не block после L) |
| I | △ | brief-gate проверяет brief + screen-spec (но hint, не block) |
| J | ✓ | Domain knowledge concepts + ui-design-architect Этап 0 |
| K | ✗ | Strike-degrade убран (не нужен когда hooks уже advisory) |
| L | ✓ | Финальная философия — hooks advisory + HARD-rules в CLAUDE.md |

## Главные уроки

1. **Hint vs Block.** Hooks могут рекомендовать, не должны блокировать (кроме денег в риске).
2. **Сначала thinking, потом код.** Без product-architect и ui-design-architect — результат всегда сырой.
3. **Двойная память обязательна.** Без vault теряется контекст между сессиями.
4. **Domain knowledge — отдельно от агентов.** Концепты в `wiki/concepts/`, агенты Read'ают их перед screen-spec.
5. **Не воспринимать вопрос как задачу.** Если пользователь спросил «зачем X?» — сначала ответ текстом, потом код.
6. **One entity → one renderer.** Нельзя одну сущность визуализировать по-разному на одной странице.
