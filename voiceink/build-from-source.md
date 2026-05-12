# VoiceInk — сборка из source

Полная инструкция как собрать VoiceInk без trial.

## Предусловия

| Что | Версия | Установка |
|---|---|---|
| macOS | 14.4+ | — |
| Xcode | Latest (15+) | App Store или developer.apple.com |
| CMake | 3.28+ | `brew install cmake` |
| Git | любая | обычно есть |

Проверка:

```bash
sw_vers | head -3
xcodebuild -version
cmake --version
git --version
```

## Шаги

```bash
# 1. Клонировать репозиторий
mkdir -p ~/Projects-build
cd ~/Projects-build
git clone https://github.com/Beingpax/VoiceInk.git
cd VoiceInk

# 2. Установить cmake если ещё нет
brew install cmake

# 3. Проверить prerequisites через Makefile
make check

# 4. Собрать (long — 5-15 минут, собирает whisper.xcframework + сам app)
make local

# 5. Скопировать .app в /Applications
rm -rf /Applications/VoiceInk.app  # удалить старую если есть
cp -R .local-build/Build/Products/Debug/VoiceInk.app /Applications/

# 6. Снять quarantine (для надёжности)
xattr -d com.apple.quarantine /Applications/VoiceInk.app 2>/dev/null
find /Applications/VoiceInk.app -exec xattr -d com.apple.quarantine {} \; 2>/dev/null

# 7. Запустить
open /Applications/VoiceInk.app
```

## Что делает `make local`

`make local` — специальная цель Makefile разработчика VoiceInk для local-сборки **без Apple Developer аккаунта**:

1. Использует `LocalBuild.xcconfig` (ad-hoc подпись `CODE_SIGN_IDENTITY = -`)
2. Использует `VoiceInk.local.entitlements` (без CloudKit и keychain groups)
3. Компилирует с флагом `LOCAL_BUILD`

`LOCAL_BUILD` Swift flag в коде:

```swift
// LicenseViewModel.swift строка 27
init() {
    #if LOCAL_BUILD
    licenseState = .licensed   ← Сразу как licensed, без проверки
    #else
    loadLicenseState()         ← Иначе грузит license (платная версия)
    #endif
}
```

То есть **сборка через `make local` стартует как fully licensed**. Никакого trial. Разработчик намеренно сделал такую опцию для open-source community.

## Verify build

После `make local`:

```bash
ls -la /Applications/VoiceInk.app/Contents/MacOS/VoiceInk
defaults read /Applications/VoiceInk.app/Contents/Info CFBundleShortVersionString
```

Должно вернуть имя бинаря + версию (например `1.76`).

Запусти app. На главном экране **НЕ должно быть** баннера «Trial Active / Buy License». Если есть — что-то пошло не так с `LOCAL_BUILD` flag.

## Обновление

```bash
cd ~/Projects-build/VoiceInk
git pull
make clean   # очистить старый build
make local
cp -R .local-build/Build/Products/Debug/VoiceInk.app /Applications/
```

## Возможные проблемы

### `cmake: command not found`

```bash
brew install cmake
```

### `whisper.xcframework not found`

`make local` сам клонирует `whisper.cpp` в `~/VoiceInk-Dependencies/` и собирает framework. Если упало — проверь логи:

```bash
make local 2>&1 | tee build.log
grep -i "error\|fail" build.log
```

### Build SUCCEEDED но app не запускается

1. Сними quarantine: `xattr -d com.apple.quarantine /Applications/VoiceInk.app`
2. Если SIP блокирует — в System Settings → Privacy & Security → разрешить запуск VoiceInk
3. Если "damaged or can't be opened" — `codesign --force --deep --sign - /Applications/VoiceInk.app`

### Hotkey не работает после установки

Дай Accessibility permission в System Settings → Privacy & Security → Accessibility.

После каждой пересборки `make local` подпись новая, нужно заново разрешить (или удалить старый VoiceInk из списка и добавить заново).

### Микрофон permission опрашивается каждый раз

Тоже из-за ad-hoc подписи. Решение — то же что и для Accessibility (delete + add заново в System Settings → Privacy & Security → Microphone).

## Альтернативный путь — постоянная подпись

Если хочешь чтобы permissions сохранялись между пересборками — нужна постоянная подпись (Apple Developer сертификат $99/год или self-signed).

Это **не покрыто в kit** — выходит за scope. Для большинства пользователей `make local` + одноразовая боль с TCC после каждой пересборки — приемлемо.

## Лицензия

Источник VoiceInk — GPL v3. См. `LICENSE` в их репо.

Твоя сборка — GPL v3.

Можешь использовать у себя, раздавать друзьям, модифицировать. Если публикуешь свою модификацию — открой исходники тоже под GPL.
