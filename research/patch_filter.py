import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

start = s.find("static bool looks_like_homebrew(const char *name) {")
end = s.find("int library_load(Game *games, int max_games)")

if start < 0 or end < 0:
    raise SystemExit("filter block not found")

new_block = r'''static bool looks_like_homebrew(const char *name) {
    static const char *skip[] = {
        // лончеры и установщики
        "hbmenu", "Homebrew", "DBI", "Goldleaf", "Awoo", "Tinfoil",
        "Appstore", "hb-appstore", "NUT", "ftpd", "sys-ftpd",
        // эмуляторы
        "PPSSPP", "RetroArch", "melonDS", "mGBA", "DeSmuME", "Dolphin",
        "Citra", "yuzu", "Skyline", "Strato", "Flycast", "DuckStation",
        "Snes9x", "FCEUX", "Genesis Plus", "Mednafen", "Vita3K",
        // утилиты
        "NX-Shell", "NXThemes", "nx-themes", "EdiZon", "Checkpoint",
        "JKSV", "Lockpick", "TegraExplorer", "Hekate", "Fizeau",
        "sys-clk", "Status Monitor", "SimpleModManager", "SwitchPresence",
        // стриминг
        "Moonlight", "Chiaki", "PSPlay", "Steam Link",
    };

    if (!name) return true;

    for (unsigned i = 0; i < sizeof(skip) / sizeof(skip[0]); i++) {
        size_t len = strlen(skip[i]);
        const char *p = name;

        while (*p) {
            if (strncasecmp(p, skip[i], len) == 0)
                return true;
            p++;
        }
    }

    return false;
}

'''

s = s[:start] + new_block + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
