#!/usr/bin/env python3
"""
PostToolUse hook: detects copy-paste between dashboard files.

Triggers on Write|Edit of files in Projects/<your-dashboard>/.
Looks for JS function names (function/const arrow/method) and HTML id/class
selectors with partner|filter|status|select keywords. If the same name is
present in another dashboard file, emits an additionalContext warning so the
agent stops the "fix-on-one-page-only" pattern.
"""

# Throttle: silent if same hint repeats in session (anti hook-fatigue)
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from _throttle import should_emit as _should_emit
except Exception:
    def _should_emit(*a, **kw):
        return True

import sys, json, os, re, glob


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or "{}")
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ""

    # Только dashboard файлы
    if "/Projects/<your-dashboard>/" not in path:
        sys.exit(0)
    if any(s in path for s in ["/_archive/", "/node_modules/", "/dist/"]):
        sys.exit(0)
    if not re.search(r"\.(html|js|css)$", path, re.IGNORECASE):
        sys.exit(0)
    if not os.path.exists(path):
        sys.exit(0)

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        sys.exit(0)

    duplicates = []

    # JS function declarations
    js_funcs = re.findall(r"function\s+(\w+)\s*\(", content)
    js_funcs += re.findall(r"const\s+(\w+)\s*=\s*(?:\([^)]*\)|\w+)\s*=>", content)
    js_funcs += re.findall(r"(\w+)\s*:\s*function\s*\(", content)

    # Уникальные имена ≥4 chars (избежать i/j/x)
    js_funcs = sorted(set(f for f in js_funcs if len(f) >= 4))

    # Базовая dashboard папка
    m = re.search(r"(.*/Projects/<your-reports>/dashboard)", path)
    if not m:
        sys.exit(0)
    dashboard_root = m.group(1)

    # Generic имена пропускаем
    generic = {
        "main", "init", "load", "save", "render", "update", "fetch",
        "config", "constructor", "data", "list", "item", "func", "name",
        "value", "result", "error", "event", "type", "node",
    }

    # Для каждой функции — поискать в other файлах dashboard
    for fn in js_funcs:
        if fn in generic:
            continue

        found_in = []
        for f in glob.glob(f"{dashboard_root}/**/*.js", recursive=True) + \
                 glob.glob(f"{dashboard_root}/**/*.html", recursive=True):
            if f == path:
                continue
            if any(s in f for s in ["/_archive/", "/node_modules/", "/dist/"]):
                continue
            try:
                with open(f, encoding="utf-8") as fh:
                    fc = fh.read()
                if re.search(rf"\bfunction\s+{re.escape(fn)}\s*\(", fc) or \
                   re.search(rf"\b{re.escape(fn)}\s*=\s*(?:\([^)]*\)|\w+)\s*=>", fc) or \
                   re.search(rf"\b{re.escape(fn)}\s*:\s*function\s*\(", fc):
                    rel = f.replace(dashboard_root + "/", "")
                    found_in.append(rel)
            except Exception:
                continue

        if found_in:
            duplicates.append((fn, found_in))

    # HTML селекторы и компоненты
    html_selectors = re.findall(
        r'<(?:select|datalist|div)\s+[^>]*?(?:id|class)\s*=\s*"([^"]*(?:partner|partn|filter|status|select)[^"]*)"',
        content, re.IGNORECASE,
    )

    seen_sel = set()
    for sel_id in html_selectors[:20]:
        if sel_id in seen_sel:
            continue
        seen_sel.add(sel_id)

        found_in = []
        for f in glob.glob(f"{dashboard_root}/**/*.html", recursive=True):
            if f == path:
                continue
            if any(s in f for s in ["/_archive/", "/node_modules/", "/dist/"]):
                continue
            try:
                with open(f, encoding="utf-8") as fh:
                    fc = fh.read()
                if re.search(rf'(?:id|class)\s*=\s*"{re.escape(sel_id)}"', fc):
                    rel = f.replace(dashboard_root + "/", "")
                    found_in.append(rel)
            except Exception:
                continue
        if found_in:
            duplicates.append((f"selector:{sel_id}", found_in))

    # Pass J: разный визуал одной entity на одной странице.
    # Эвристика: ищем известные entity-патерны и считаем уникальные HTML-renderer-сигнатуры.
    # Если на одной странице >1 разных visual pattern на одну entity → WARN.
    entity_visual_dupes = []

    entity_patterns = {
        'порядок офферов': [
            r'renderOrderCompact\s*\(',
            r'offers\.map\s*\(',
            r'class="[^"]*ep-pv-order[^"]*"',
            r'class="[^"]*offer-chip[^"]*"',
            r'class="[^"]*ep-lb-chips[^"]*"',
            r'★\s*базовый',
            r'data-offer',
        ],
        'партнёр (selector)': [
            r'<select[^>]+id="[^"]*[Pp]artner[^"]*"',
            r'class="[^"]*ps-trigger[^"]*"',
            r'PartnerSwitcher\s*\(',
            r'partner-switcher',
        ],
        'статус эксперимента': [
            r'class="[^"]*exp-status[^"]*"',
            r'class="[^"]*status-pill[^"]*"',
            r'class="[^"]*ep-status[^"]*"',
            r'status\s*===?\s*[\'"]running[\'"]',
        ],
        'probability / confidence': [
            r'class="[^"]*ep-prob-bar[^"]*"',
            r'class="[^"]*ep-lb-prob[^"]*"',
            r'class="[^"]*confidence-bar[^"]*"',
            r'Math\.round\s*\(\s*p\s*\*\s*100\s*\)',
        ],
    }

    for entity_name, patterns in entity_patterns.items():
        hit_patterns = []
        for pat in patterns:
            if re.search(pat, content):
                hit_patterns.append(pat)
        if len(hit_patterns) >= 2:
            entity_visual_dupes.append((entity_name, hit_patterns))

    if not duplicates and not entity_visual_dupes:
        sys.exit(0)

    # Build message
    lines = []
    if duplicates:
        lines += [
            f"🔁 КОПИПАСТА ОБНАРУЖЕНА в {os.path.basename(path)}:",
            "",
        ]
        for name, files in duplicates[:5]:
            lines.append(f"- `{name}` также в:")
            for f in files[:3]:
                lines.append(f"  - {f}")

        lines.append("")
        lines.append("Нарушает компонентную разработку. Фикс на одной странице не работает на других.")
        lines.append("")
        lines.append("ДЕЙСТВИЕ: вынеси в общий модуль:")
        lines.append("  - dashboard/wwwroot/static/components/<name>.js")
        lines.append("  - подключи через <script src=...> на всех страницах")
        lines.append("")

    if entity_visual_dupes:
        if duplicates:
            lines.append("---")
            lines.append("")
        lines += [
            f"🎭 РАЗНЫЕ ВИЗУАЛЫ ОДНОЙ ENTITY в {os.path.basename(path)}:",
            "",
        ]
        for ent, pats in entity_visual_dupes[:4]:
            lines.append(f"- **{ent}** — {len(pats)} разных pattern на одной странице:")
            for p in pats[:4]:
                lines.append(f"    - `{p}`")
        lines.append("")
        lines.append("Нарушает one-entity-one-renderer principle (см. wiki/concepts/component-reuse-discipline.md).")
        lines.append("Пользователь увидит несогласованный визуал: «звезда базовый тут, полный порядок там».")
        lines.append("")
        lines.append("ДЕЙСТВИЕ:")
        lines.append("  1. Вызвать ui-design-architect через Task — пусть сделает Entity reuse audit")
        lines.append("  2. Вынести entity в единый компонент в components/<entity>-renderer.js")
        lines.append("  3. Заменить все inline-рендеры на вызов компонента")
        lines.append("")

    lines.append("💡 не торопись говорить «готово» пока не унифицировано.")

    msg = "\n".join(lines)
    if not _should_emit(data.get("session_id", "") if isinstance(data, dict) else "", "selector-duplication-detector", msg[:300] if "msg" in dir() else str(locals().get("msg", ""))[:300]):
        _sys.exit(0)
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
