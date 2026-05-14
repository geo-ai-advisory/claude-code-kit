#!/usr/bin/env python3
"""Shared throttle для advisory hooks.

Цель: убрать повторы одного и того же hint в одной сессии. Hook fatigue
происходит когда 5 Edit подряд × 4 hooks = 20 advisory messages в одном
turn, агент захлёбывается и теряет фокус.

Usage:
    from _throttle import should_emit
    if not should_emit(session_id, "ui-auto-review", "shrift-skachet-h1-h2"):
        sys.exit(0)
    # ... продолжаем нормальный hook output

Логика:
    Каждая комбинация (session_id, hook_name, content_fingerprint) пишется
    в /tmp/hook-throttle/<session_id>.json. Если та же запись уже есть —
    should_emit вернёт False (не повторяй).

    max_per_session=3: один и тот же fingerprint может стрелять не больше
    3 раз в session (на случай если первый hint был не замечен).
"""

import os
import json
import hashlib

THROTTLE_DIR = '/tmp/hook-throttle'


def _state_path(session_id: str) -> str:
    os.makedirs(THROTTLE_DIR, exist_ok=True)
    safe = session_id.replace('/', '_').replace(' ', '_')[:64]
    return os.path.join(THROTTLE_DIR, f'{safe}.json')


def _load(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(path: str, state: dict) -> None:
    try:
        with open(path, 'w') as f:
            json.dump(state, f)
    except Exception:
        pass


def should_emit(session_id: str, hook_name: str, content: str,
                max_per_session: int = 3) -> bool:
    """Вернёт True если hook должен выдать output, False — пропустить (throttle).

    content: текст hint'а или fingerprint того о чём предупреждаешь.
    max_per_session: лимит повторов одного fingerprint в одной сессии.
    """
    if not session_id:
        return True  # без session_id throttle бесполезен

    fp = hashlib.sha256(f'{hook_name}|{content}'.encode('utf-8')).hexdigest()[:16]
    path = _state_path(session_id)
    state = _load(path)
    count = state.get(fp, 0)

    if count >= max_per_session:
        return False  # уже выдавали — throttle

    state[fp] = count + 1
    _save(path, state)
    return True


def reset_session(session_id: str) -> None:
    """Очистить throttle state для session (например при /clear)."""
    path = _state_path(session_id)
    try:
        os.remove(path)
    except Exception:
        pass
