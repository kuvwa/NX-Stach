import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- library.c ----------
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

variants = r'''
// Один образ на Switch может содержать несколько игр (например, Hotline Miami
// Collection). Здесь такие игры разворачиваются в отдельные плитки.
typedef struct {
    u64 title_id;
    const char *label;
    const char *steam_appid;
} Variant;

static const Variant VARIANTS[] = {
    { 0x0100D0E00E51E000ULL, "Hotline Miami", "219150" },
    { 0x0100D0E00E51E000ULL, "Hotline Miami 2: Wrong Number", "274170" },
};

static int expand_variants(Game *games, int count, int max_games) {
    Game out[MAX_GAMES];
    int n = 0;

    for (int i = 0; i < count && n < max_games; i++) {
        bool matched = false;

        for (unsigned v = 0; v < sizeof(VARIANTS) / sizeof(VARIANTS[0]); v++) {
            if (games[i].title_id != VARIANTS[v].title_id) continue;
            if (n >= max_games) break;

            out[n].title_id = games[i].title_id;
            snprintf(out[n].name, sizeof(out[n].name), "%s", VARIANTS[v].label);
            snprintf(out[n].steam_appid, sizeof(out[n].steam_appid), "%s",
                     VARIANTS[v].steam_appid);
            n++;
            matched = true;
        }

        if (!matched && n < max_games)
            out[n++] = games[i];
    }

    memcpy(games, out, sizeof(Game) * (size_t)n);
    return n;
}

'''

marker = "static int compare_games(const void *a, const void *b) {"
if marker not in s:
    raise SystemExit("marker not found in library.c")

s = s.replace(marker, variants + marker, 1)

old = """    qsort(games, count, sizeof(Game), compare_games);

    return count;"""
new = """    count = expand_variants(games, count, max_games);

    qsort(games, count, sizeof(Game), compare_games);

    return count;"""

if old not in s:
    raise SystemExit("qsort block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)

# ---------- main.c ----------
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """static const SaveSource SAVE_SOURCES[] = {
    { "219150", 0x0100D0E00E51E000ULL, "/HotlineMiami", 1 },
};"""
new = """static const SaveSource SAVE_SOURCES[] = {
    { "219150", 0x0100D0E00E51E000ULL, "/HotlineMiami", 1 },
    { "274170", 0x0100D0E00E51E000ULL, "/HotlineMiami2", 1 },
};"""

if old not in s:
    raise SystemExit("save sources not found")

s = s.replace(old, new, 1)

old = """    save_init();
    bool net_ready = net_init();
    history_load();"""
new = """    save_init();
    bool net_ready = net_init();
    history_load();

    // диагностика структуры сейва коллекции
    gamesave_dump_tree(0x0100D0E00E51E000ULL);"""

if old not in s:
    raise SystemExit("init block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)

print("ok")
