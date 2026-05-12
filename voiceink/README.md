# VoiceInk free build

VoiceInk — лучшая open-source альтернатива SuperWhisper для macOS. Hotkey-driven dictation: зажал клавишу, говоришь, текст вставляется в активное приложение.

**Источник:** [Beingpax/VoiceInk](https://github.com/Beingpax/VoiceInk) — GPL v3.

## Дилемма

| Способ | Цена | Тривиальность |
|---|---|---|
| `brew install --cask voiceink` | Trial 7 дней, потом «Buy License» | Очень просто |
| Сборка из source через `make local` | **Бесплатно навсегда** | Нужен Xcode |
| Pre-built DMG из этого репо (Releases) | **Бесплатно** | Просто скачать и поставить |

GPL v3 разрешает любой из этих способов. Разработчик намеренно включил `LOCAL_BUILD` Swift flag который делает `licenseState = .licensed` сразу при init.

## Способ 1 — pre-built DMG (рекомендуется)

Скачай готовый `.dmg` из Releases этого репозитория:

1. Иди на https://github.com/<your-user>/claude-code-kit/releases
2. Скачай последний `VoiceInk-free-<version>.dmg`
3. Открой DMG, перетащи `VoiceInk.app` в `/Applications`
4. Сними quarantine: `xattr -d com.apple.quarantine /Applications/VoiceInk.app` (раз DMG не подписан Apple)
5. Запусти

## Способ 2 — сборка из source

См. [`build-from-source.md`](build-from-source.md).

Кратко:
```bash
brew install cmake
git clone https://github.com/Beingpax/VoiceInk.git
cd VoiceInk
make local
# Готовый .app в .local-build/Build/Products/Debug/VoiceInk.app
```

## Первая настройка

1. **Открой VoiceInk** — окно onboarding
2. **Дай Accessibility permission** — System Settings → Privacy & Security → Accessibility → включи VoiceInk. Без этого hotkey не работает.
3. **Скачай модель Whisper** — Settings → AI Models. Рекомендую `large-v3-turbo` (~800 MB, отличное распознавание русского)
4. **Выбери hotkey** — Settings → Recording Shortcut. Рекомендую `rightShift` (правый Shift) — push-to-talk, удобно одной рукой
5. **Language** — Settings → Language → Russian (или Auto-detect)

## Тест

- Открой Notes / Telegram / любое поле ввода
- Зажми **правый Shift** → говори → отпусти
- Текст вставится в активное окно

## Если не вставляется

Главная причина — **Accessibility permission не дан** (или дан старой подписи).

После каждой пересборки `make local` — ad-hoc подпись новая, identity для TCC другая. Старые permissions относятся к старой подписи. Решение:

1. System Settings → Privacy & Security → Accessibility
2. Найди VoiceInk → удали через "-"
3. Добавь заново через "+" → `/Applications/VoiceInk.app`
4. Включи ползунок

## Обновления

```bash
cd <where-you-cloned-VoiceInk>
git pull
make local
# Скопируй новый .app в /Applications
```

После пересборки придётся заново дать Accessibility (см. выше).

## Лицензия

Источник — GPL v3 ([LICENSE](https://github.com/Beingpax/VoiceInk/blob/main/LICENSE)). Это значит:

- ✓ Можно собирать без trial, использовать у себя
- ✓ Можно раздавать друзьям (наш fork тоже под GPL)
- ⛔ Нельзя продавать closed-source форк

Pre-built DMG в Releases — GPL v3, как и исходник.

## Альтернативы которые мы рассматривали и отбросили

- ❌ **FreeWhisper** — мало звёзд, забагованное, cursor reset в селекторе
- ❌ **MacWhisper free tier** — только batch transcribe файла, нет hotkey-dictation
- ❌ **Buzz** — 19k stars но это batch transcriber, не диктовщик
- ❌ **whisper-writer** (Python) — работает, но Python venv + GPL-3.0 + последний commit год назад
- ❌ **OpenWhispr** — Electron, не нативный
- ✓ **VoiceInk** — Swift native, активная разработка, Whisper large-v3-turbo, GPL v3
