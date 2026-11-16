# NX-Stach — установка

## Что копировать на SD-карту

Папку `switch` из этого архива кладём в корень карты памяти (с заменой файлов).

Должно получиться:

```
SD:/switch/NX-Stach.nro
SD:/switch/.overlays/NX-Stach-Tracker.ovl
SD:/switch/NX-Stach/games.json
SD:/switch/NX-Stach/progress.json      <- создастся сам
```

## Как запустить

1. NX-Stach: Homebrew Menu (Album) → NX-Stach.
2. Tracker (оверлей): запустить любую игру → HOME → Ultrahand/Tesla → NX-Stach Tracker.

## Что должно быть видно

- Оверлей: название запущенной игры + её Title ID.
  Если вместо названия `Unknown game` — значит игра не запущена или оверлей запущен не поверх игры.
- NX-Stach: экран достижений Hotline Miami — 35 настоящих достижений Steam
  (Combo Beginner, Playing Pool, Dog Lover, ...), а не тестовые "First Steps".

## Сборка (если правишь код)

```bash
export DEVKITPRO=/opt/devkitpro DEVKITA64=/opt/devkitpro/devkitA64
cd ~/NX-Stach && make -j8            # .nro
cd ~/NX-Stach/tracker && make -j8    # .ovl
```
