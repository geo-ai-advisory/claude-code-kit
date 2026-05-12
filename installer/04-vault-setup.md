# Installer step 04 — Vault setup (Obsidian)

Цель: поставить Obsidian-vault с двойной памятью (semantic + episodic) — без него теряется контекст между сессиями.

## Зачем нужен vault

Claude Code сам не помнит ничего между сессиями. Vault даёт ему 4 уровня памяти:

| Tier | Где живёт | Когда читается |
|---|---|---|
| **Working** | `CRITICAL_FACTS.md` | Каждая сессия (SessionStart hook) |
| **Episodic** | `log.md`, `journals/*/log.md` | По требованию, grep по теме |
| **Semantic** | `wiki/concepts/*.md` | По требованию, через Obsidian search |
| **Procedural** | `~/.claude/agents/`, `~/.claude/skills/` | Автоматически через PROACTIVELY |

Подробности — `docs/memory-tiers.md`.

## Установка Obsidian (если ещё нет)

```bash
brew install --cask obsidian
```

Или скачать с https://obsidian.md/download

## Развёртывание vault-template

1. **Спроси пользователя где хранить vault**
   - Стандарт: `~/Documents/vault/` или `~/Documents/second-brain/`
   - Если у него уже есть Obsidian-vault для личных заметок — **не смешивать**, делать отдельный для работы

2. **Скопировать template:**

```bash
VAULT_DIR="$HOME/Documents/second-brain"  # уточни у пользователя
KIT_DIR="$(pwd)"  # папка claude-code-kit

mkdir -p "$VAULT_DIR"
cp -R "$KIT_DIR/vault-template/"* "$VAULT_DIR/"
cp -R "$KIT_DIR/vault-template/.obsidian" "$VAULT_DIR/" 2>/dev/null || true
```

3. **Открыть в Obsidian:**

```bash
open -a Obsidian "$VAULT_DIR"
```

В Obsidian: "Open folder as vault" → выбери папку `$VAULT_DIR`.

## Кастомизация CRITICAL_FACTS.md

`CRITICAL_FACTS.md` — самый важный файл. Он попадает в system context каждой сессии Claude Code (через SessionStart hook).

**Заполни его на основе scan-журнала (step 01):**

```bash
cat > "$VAULT_DIR/CRITICAL_FACTS.md" <<EOF
# CRITICAL_FACTS

## Кто
<имя пользователя>, <роль>, <компания>. Цель: <главная цель работы>.

## Активные проекты
- <project1> — <одна строка что это>
- <project2> — ...

## Партнёры / клиенты / системы
- <X>: <ID/URL/ключевая инфа>
- ...

## Команда (если работает с людьми)
<имя>-<роль>: <в чём помогает>

## Технические инварианты
- <Важная константа 1> (например: ProductTypeId=5)
- <Важная константа 2>
- <Domain rule что нельзя забывать>

## Ключевые документы / ссылки
- <название>: <URL или Google Doc ID>

## Стиль / формат
<правила написания: язык, длина, форматирование>
EOF
```

**Длина < 2000 токенов** — это работает как «всегда в контексте». Если больше — Claude не сможет всё удержать.

## Кастомизация _CLAUDE.md (operating manual)

`_CLAUDE.md` — это инструкция как работать с vault. Шаблон уже есть. Просто проверь что путь vault в нём правильный:

```bash
$EDITOR "$VAULT_DIR/_CLAUDE.md"
# Поправь упоминания путей <your-workspace> / Projects/<your-vault>/ на свои
```

## Кастомизация wiki/concepts

Концепты универсальные (про дизайн, UI, A/B, memory) — оставь как есть. Они полезны всем.

Если пользователь хочет свои concepts — создавай позже по мере появления повторяющихся знаний.

## Установка SessionStart hook для bootstrap

Этот hook будет писать содержимое `CRITICAL_FACTS.md` + `_index.md` + tail `log.md` в system context каждой новой сессии. Без него Claude не увидит память.

**Это будет сделано в step 05 — hooks** (а здесь только подготавливаем).

Но проверим что `_CLAUDE.md` указывает на правильный vault path:

```bash
grep "Projects/second-brain" "$VAULT_DIR/_CLAUDE.md" | head -5
```

Если есть упоминания старого пути — замени на свой `$VAULT_DIR`:

```bash
# macOS sed требует -i ''
sed -i '' "s|Projects/second-brain|${VAULT_DIR##*/}|g" "$VAULT_DIR/_CLAUDE.md"
```

## Opcjonalnie — Obsidian Graph MCP

Если хочешь чтобы Claude мог искать по vault через obsidian-graph MCP (точнее чем grep):

```bash
brew install bun  # если нет
# Установи semantic-vault-mcp через BRAT в Obsidian (community plugin)
```

Подробности — `docs/obsidian-setup.md`. Это **опционально**, можно пропустить — grep + Read работают и без MCP.

## Запиши в журнал

```bash
cat >> ~/claude-install-journal/<date>-scan.md <<EOF

## Vault (step 04)
- Path: $VAULT_DIR
- CRITICAL_FACTS.md filled: yes
- _CLAUDE.md customized: yes
- Obsidian app installed: yes/no (already had)
- MCP obsidian-graph: yes/no (optional)
EOF
```

## После завершения

Vault готов. Переходи к **step 05 — hooks setup** (там подключим SessionStart hook который сделает CRITICAL_FACTS видимым для Claude).
