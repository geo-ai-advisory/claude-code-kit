# claude-code-kit

Готовая система агентов, хуков и Obsidian-vault для Claude Code на macOS. Адаптируется под твои проекты — Claude сам сканирует код, предлагает релевантных агентов и собирает рабочую среду под ключ.

Собрано из 2 недель итераций — Pass A → Pass L, каждый шаг чинит конкретный косяк из реальной работы (см. `docs/pass-history.md`).

## Что внутри

| Папка | Что |
|---|---|
| `agents-library/` | 23 проверенных субагента — UI/UX дизайн (product-architect, ui-design-architect, ui-quality-reviewer), QA (qa-scenario-tester, accessibility-auditor, api-contract-tester), engineering (backend-code-reviewer, database-schema-reviewer, frontend-component-reviewer), product (sprint-prioritizer, feedback-synthesizer, consistency-checker), memory (memory-consolidator, vault-reader, vault-writer), core (web-researcher, verifier, journals-explorer, code-explorer), integrations (gitlab/telegram/sheets/tracker) |
| `hooks-library/` | 22 hook для macOS Claude Code — advisory (hints, не блокируют), hard-block (только `prod-push-gate`), safety (предотвращают session-crash от больших скриншотов), session (vault auto-bootstrap) |
| `vault-template/` | Obsidian-vault шаблон в стиле Karpathy LLM Wiki — wiki/concepts (semantic), log.md (episodic), CRITICAL_FACTS.md (working), 10 готовых концептов про продуктовое мышление, A/B эксперименты, дизайн, component reuse |
| `claude-config-template/` | Готовые `CLAUDE.md` и `settings.json` с HARD-rules и подключёнными hooks |
| `skills/` | 5 slash-skills — `/check-ui`, `/check-consistency`, `/check-scenarios`, `/sb-start`, `/sb-recap` |
| `installer/` | 7-шаговый протокол для Claude Code — сканирование проектов → подбор агентов → vault → hooks → verify |
| `voiceink/` | Инструкция как поставить VoiceInk (open-source SuperWhisper-альтернатива) без trial |
| `docs/` | Архитектура, 4-tier memory pattern, история Pass A-L |

## Установка под ключ (через свой Claude Code)

1. Склонируй этот репо:
   ```bash
   git clone https://github.com/<your-user>/claude-code-kit.git ~/claude-code-kit
   ```

2. Открой папку в Claude Code и скажи:
   > Прочитай `INSTALL.md` и установи систему. Сначала просканируй мои проекты, потом предложи релевантных агентов, потом vault и хуки. Не торопись, спрашивай меня где нужно.

3. Claude пройдёт 7 шагов:
   - **scan** — найдёт твой стек (C#/Python/Node/Swift, frontend, базы, отчёты)
   - **shortlist** — предложит подходящих агентов из библиотеки
   - **custom** — поможет написать агентов под твой domain
   - **vault** — поставит Obsidian-vault с двойной памятью (semantic + episodic)
   - **hooks** — подключит advisory-хуки (без агрессивных блокировок)
   - **skills** — slash-команды
   - **verify** — финальный прогон что всё работает

Полный протокол — в `installer/00-overview.md`.

## Философия

**Hooks не должны блокировать работу.** Урок Pass G-L: hard-block`continue:false`превращает помощника в надсмотрщика. Все хуки в kit — **advisory** (печатают `additionalContext`, не блокируют). Единственное исключение —`prod-push-gate.py`(деньги в риске).

**Двойная память.** `CRITICAL_FACTS.md` всегда в контексте (working), `log.md` хронология (episodic), `wiki/concepts/*.md` стабильные знания (semantic), `~/.claude/agents/*.md` инструкции «как делать» (procedural). Transfer episodic→semantic делает `memory-consolidator` раз в 5-7 сессий.

**Сначала thinking, потом код.** Перед UI-задачей — `product-architect` (что/кому/зачем) → `ui-design-architect` (как выглядит / референсы / mental model) → Edit → `ui-quality-reviewer` → `qa-scenario-tester`. Без этого получается «лидерборд из 7 chips в одну строку растянутых на весь экран» (реальный случай).

**Domain knowledge в vault, не в агентах.** Концепты типа «эксперимент это живой процесс, не разовый contest» или «one entity → one renderer» — отдельные `wiki/concepts/*.md`. Агенты их подгружают на каждый вызов через `Read`.

## VoiceInk free build

В `voiceink/` — инструкция как собрать VoiceInk из исходников (GPL v3) с флагом `LOCAL_BUILD`, который делает `licenseState = .licensed` сразу при init. **Никакого trial.** Разработчик намеренно дал такую опцию.

## Лицензия

MIT для kit. Отдельные файлы наследуют свои лицензии (VoiceInk — GPL v3, Obsidian-плагины — MIT).

## Авторство

Собрано <your-name> при работе с Claude Code, 2026-04 — 2026-05.
