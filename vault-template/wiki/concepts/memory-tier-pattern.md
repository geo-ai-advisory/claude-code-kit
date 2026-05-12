---
type: concept
tags: [memory, architecture, vault, self-learning, pass-f]
related: ["[[wiki/projects/self-learning-system]]", "[[journals/2026-05-12-pass-E/00-FINAL]]"]
created: 2026-05-12
updated: 2026-05-12
recency: 2026-05-12
confidence: high
source: rohitg00/agentmemory
---

# Memory tier pattern (4-tier из agentmemory)

## TL;DR

Память Claude в <your-workspace> разделена на 4 уровня по адаптации [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory). Уровень определяет (а) где факт живёт физически, (б) когда он пишется и кем, (в) когда и как он подгружается в контекст, (г) при каких условиях он эвиктится.

Это не теория — это карта реальных файлов и hook'ов нашего vault'а.

## Четыре tier'а

### 1. Working memory — то, что всегда в контексте

**Где живёт**: `Projects/<your-vault>/CRITICAL_FACTS.md`.

**Когда пишется**: вручную, когда факт настолько критичен, что Claude не должен его забыть никогда (бизнес-цель, ID партнёра, prod endpoint, имя пользователя).

**Когда читается**: автоматически инъектится в каждую сессию через `SessionStart` hook. То есть Claude видит этот файл до того, как пользователь напишет первое сообщение.

**Размер**: минимальный (≤200 строк), иначе перегрузит контекст.

**Примеры из нашего vault'а**:
- Имя пользователя — <your-name>, не Vozakov.
- Цель — O-1 виза США.
- ASCII-дефис `-`, не `—`.

### 2. Episodic memory — журнал «что произошло»

**Где живёт**:
- `Projects/<your-vault>/log.md` — общий append-only журнал всех сессий <your-workspace>.
- `journals/<YYYY-MM-DD>-<topic>/log.md` — отдельные журналы крупных сессий.
- `Projects/<x>/journals/<YYYY-MM-DD>-<topic>/log.md` — проектные журналы.

**Когда пишется**: автоматически Stop-hook'ом `session-auto-summary.py` в конце каждой сессии. 3-5 строк summary: что сделано, какие файлы тронуты, какие открытые вопросы.

**Когда читается**:
- В начале сессии — `grep '^## \[' log.md | head -20` (ритуал из `_CLAUDE.md`).
- При запросе «что я делал на прошлой неделе» — grep по диапазону дат.
- Перед консолидацией — `memory-consolidator` читает хвост.

**Свойства**:
- Immutable: нельзя править прошлые записи. Только append.
- Высокая частота, низкая ценность каждой записи отдельно. Ценность — в агрегате.

### 3. Semantic memory — факты «что я знаю»

**Где живёт**: `Projects/<your-vault>/wiki/concepts/*.md`, `wiki/partners/*.md`, `wiki/people/*.md`, `wiki/decisions/*.md`.

**Когда пишется**:
- `memory-consolidator` subagent раз в 5-7 сессий: анализирует log.md, находит повторяющиеся факты (упомянутые в ≥2 сессиях), создаёт/обновляет страницы.
- Вручную через `vault-writer` subagent — surgical edits после содержательной сессии (Two-Output Rule).
- Через скиллы `/sb-decide`, `/sb-question`, `/sb-recap` — пользователь явно фиксирует факт.

**Когда читается**:
- По запросу — `grep`, `Glob`, Obsidian MCP `search`.
- Через граф — `mcp__obsidian-graph__graph` обходит `[[wikilinks]]`.
- Когда `~/.claude/CLAUDE.md` упоминает страницу как источник истины (например `wiki/concepts/html-report-design-system.md`).

**Свойства**:
- Mutable: страницы переписываются по мере уточнения фактов (через `patch_section`, не overwrite).
- Низкая частота, высокая ценность каждой страницы.
- Frontmatter `recency`, `confidence`, `status` определяет насколько свежий и достоверный факт.

### 4. Procedural memory — инструкции «как делать»

**Где живёт**:
- `~/.claude/agents/*.md` — subagent'ы (14+ ролей: vault-writer, ui-quality-reviewer, mfo-db-researcher, memory-consolidator…).
- `~/.claude/skills/*/SKILL.md` — slash-команды (<report-skill>, /sb-recap, /hh, …).
- `~/.claude/CLAUDE.md`, `<your-workspace>/CLAUDE.md`, `Projects/<x>/CLAUDE.md` — операционные правила.
- `~/.claude/hooks/*.py` — автоматизированные guard'ы (selector-duplication-detector, claim-readiness-validator, prod-push-gate).

**Когда пишется**: вручную, когда паттерн встречается достаточно часто чтобы его формализовать. Например: «UI-ревью после Edit *.html» → создать `ui-quality-reviewer.md` + AUTO UI-REVIEW hook.

**Когда читается**:
- Автоматически через PROACTIVELY-описание (Claude видит subagent по триггеру).
- Через `Skill` tool для slash-команд.
- Через hook'и — они срабатывают на события (Edit, Stop, SessionStart) без участия Claude.

**Свойства**:
- Высокая ценность, низкая частота изменений.
- Эвиктится только архивацией (`~/.claude/agents/_archive/`, `~/.claude/skills/<name>/_archive/`).

## Transfer rules — как факт продвигается между уровнями

```
Working ← (manual, важный факт)
   ↓ (никуда не уходит, всегда в контексте)

Episodic ← (auto Stop hook)
   ↓ (memory-consolidator раз в 5-7 сессий)

Semantic ← (consolidator или vault-writer)
   ↓ (вручную через создание subagent/skill)

Procedural ← (formalization)
```

- **Working → Episodic**: не происходит, Working факты остаются в Working. Они слишком критичны чтобы их «забыть».
- **Episodic → Semantic**: `memory-consolidator` subagent. Триггер — keyword упомянут в ≥2 сессиях log.md.
- **Semantic → Procedural**: вручную, когда видим что Semantic-факт постоянно перечитывается и используется как инструкция → оформляем subagent или skill. Пример: «UI-ревью паттерн» → `ui-quality-reviewer`.
- **Обратный трансфер** (Procedural → Semantic) тоже бывает: если subagent описывает паттерн, который полезен как факт сам по себе → выписать в wiki/concepts.

## Priority — порядок эвикции при перегрузке

При перегрузке контекста (Claude слишком много помнит, начинает тормозить или галлюцинировать), эвиктить в обратном порядке:

1. **CRITICAL** (never evict): бизнес-цели, ID партнёров, prod endpoints, имя пользователя → `CRITICAL_FACTS.md`. Не выбрасывается никогда.
2. **HIGH** (reload on task start): архитектурные решения, feedback rules → `~/.claude/projects/.../memory/*.md`. Подгружается в начале задачи, но не сидит постоянно.
3. **MEDIUM** (episodic, active project only): детали текущей задачи → `log.md` за последние 1-2 недели. Эвиктится через grep-фильтр по дате.
4. **LOW** (evict after session): raw observations, временные находки → не сохраняется явно, уходит с окончанием сессии.

## Примеры из нашего vault'а

### Пример 1: Episodic → Semantic (как сработало)

В сессиях 2026-04-12, 2026-04-19, 2026-05-03 повторно упоминался «retro-refresh experiment». Сначала это были episodic-записи в log.md — «починил retro-refresh», «доделал per-offer stats для retro-refresh». После 3-й сессии паттерн стал устойчивым → должна появиться `wiki/concepts/retro-refresh-pattern.md` с описанием логики. Это работа для `memory-consolidator`.

### Пример 2: Semantic → Procedural (как сработало)

После N сессий мы поняли, что «после Edit *.html всегда нужно прогнать UI-ревью по 6 категориям». Это сначала жило как factual reminder в `wiki/concepts/ui-grid-discipline.md`. Когда стало ясно, что это повторяемая процедура → создан `~/.claude/agents/ui-quality-reviewer.md` (Procedural). А ещё точнее — `~/.claude/hooks/*.py` для AUTO UI-REVIEW (автоматический trigger).

### Пример 3: Working memory дисциплина

`CRITICAL_FACTS.md` сейчас содержит: имя пользователя, ASCII-дефис, текущий проект <YourCompany>/InsurTech. Если добавить туда «GitLab read-only token» (длинная строка) — это уже HIGH, не CRITICAL. Working memory должна оставаться короткой, иначе перегружает каждую сессию.

## Связанные

- [[wiki/projects/self-learning-system]] — мета-проект, в рамках которого выстроена эта архитектура.
- [[2026-05-12-pass-E/00-FINAL]] — финальная сводка Pass E, где описаны введённые subagent'ы и hook'и.
- [[wiki/concepts/cursor-preview-self-contained]] — пример Semantic-страницы, которая жила несколько сессий как episodic до канонизации.

## Sources

- https://github.com/rohitg00/agentmemory — оригинальный 4-tier pattern для AI agents (Working/Episodic/Semantic/Procedural).
- Внутренняя адаптация — Pass F, 2026-05-12.
