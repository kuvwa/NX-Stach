import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

start = s.find("static bool looks_like_homebrew(const char *name) {")
end = s.find("int library_load(Game *games, int max_games)")

if start < 0 or end < 0:
    raise SystemExit("filter block not found")

new_block = (
"static bool looks_like_homebrew(const char *name) {\n"
"    static const char *skip[] = {\n"
"        // эмуляторы\n"
"        \"PPSSPP\", \"RetroArch\", \"melonDS\", \"mGBA\", \"DeSmuME\", \"Dolphin\",\n"
"        \"Citra\", \"yuzu\", \"Skyline\", \"Strato\", \"Flycast\", \"DuckStation\",\n"
"        \"Snes9x\", \"FCEUX\", \"Genesis Plus\", \"Mednafen\", \"Vita3K\",\n"
"        // лончеры и установщики\n"
"        \"hbmenu\", \"Homebrew\", \"DBI\", \"Goldleaf\", \"Awoo\", \"Tinfoil\",\n"
"        \"Appstore\", \"hb-appstore\", \"NUT\", \"ftpd\", \"sys-ftpd\",\n"
"        // утилиты\n"
"        \"NX-Shell\", \"NXThemes\", \"nx-themes\", \"EdiZon\", \"Checkpoint\",\n"
"        \"JKSV\", \"Lockpick\", \"TegraExplorer\", \"Hekate\", \"Fizeau\",\n"
"        \"sys-clk\", \"Status Monitor\", \"SimpleModManager\",\n"
"        // стриминг\n"
"        \"Moonlight\", \"Chiaki\", \"PSPlay\", \"Steam Link\",\n"
"    };\n"
"\n"
"    if (!name) return true;\n"
"\n"
"    for (unsigned i = 0; i < sizeof(skip) / sizeof(skip[0]); i++) {\n"
"        size_t len = strlen(skip[i]);\n"
"        const char *p = name;\n"
"\n"
"        while (*p) {\n"
"            if (strncasecmp(p, skip[i], len) == 0)\n"
"                return true;\n"
"            p++;\n"
"        }\n"
"    }\n"
"\n"
"    return false;\n"
"}\n"
"\n")

s = s[:start] + new_block + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
