# NX-Stach

Steam achievements viewer for Nintendo Switch homebrew.

NX-Stach shows the achievement list of the Steam version of the games installed on your
console, and (where it is technically possible) tracks progress directly from the game's
save file.

Switch has no system-wide achievement system, so there are three sources of progress:

| Source | Coverage | Accuracy |
|---|---|---|
| Save recipe (reads the game's save) | some games | exact |
| Manual marking (tap an achievement) | every game | as marked |
| (planned) memory probes via sysmodule | some games | exact |

## Features

- Game grid built from the console itself (covers are read from the installed titles).
- Steam catalog import by name: search, pick from up to 24 results with icons, and the
  achievement catalog + icons are stored on the SD card.
- Steam-style achievement screen: unlocked / locked sections, dates, play time,
  progress bar, "locked only" filter.
- Manual marking for games without a save recipe.
- Pins: `X` pins a game to the top of the grid.
- English / Russian UI switch (game and achievement names stay English).
- Overlay (`NX-Stach Tracker`) that shows the currently running game.

## Requirements

- Atmosphere CFW
- Homebrew Menu (hbmenu) to launch the `.nro`
- For the overlay only: Tesla / Ultrahand + ovlloader

## Install

Copy the `switch` folder from the release archive to the SD card root:

```
SD:/switch/NX-Stach.nro
SD:/switch/.overlays/NX-Stach-Tracker.ovl
```

## Build

```bash
export DEVKITPRO=/opt/devkitpro
export DEVKITA64=/opt/devkitpro/devkitA64

cd NX-Stach && make -j8            # .nro
cd tracker && make -j8             # .ovl
```

Dependencies (pacman): `switch-dev`, `switch-freetype`, `switch-jansson`,
`switch-curl`, `switch-zlib`, `switch-mbedtls`, `switch-minizip`.

The overlay uses [libultrahand](https://github.com/ppkantorski/libultrahand) as a submodule
in `lib/libultrahand`.

## Save recipes

Progress reading is data-driven, so adding a game does not require a rebuild:

```
SD:/switch/NX-Stach/recipes/<TITLE_ID>_<STEAM_APPID>.json
```

```json
{
  "steam_appid": "219150",
  "file_path": "/HotlineMiami/savedata.vfs",
  "marker": "unlocked_achievements.dat",
  "offset": 0,
  "skip": 1,
  "format": 0,
  "count": 35
}
```

`format`:

- `0` — ASCII `0`/`1` separated by newlines
- `1` — raw bytes `0`/`1`
- `3` — bitmask stored as a number after `marker` (text file, e.g. `trophyFlag="4"`)
- `4` — keys `<marker><index>` (Unity PlayerPrefs)

`skip` — how many leading flags to ignore.

## Files created on the SD card

```
SD:/switch/NX-Stach/settings.ini   UI language
SD:/switch/NX-Stach/pins.txt       pinned games
SD:/switch/NX-Stach/progress.json  manual marks
SD:/switch/NX-Stach/history.json   unlock dates
SD:/switch/NX-Stach/games.json     Title ID -> Steam AppID
SD:/switch/NX-Stach/catalog/       imported catalogs and icons
SD:/switch/NX-Stach/recipes/       save recipes
```

Replacing the `.nro` does not touch any of these.

## Limitations

- Nintendo provides no achievement system, so automatic progress is only possible for
  games that store achievement state in their own save file.
- Achievement names, descriptions and icons are Steam metadata.

## License

MIT — see [LICENSE](LICENSE).
