import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- чистим net.h ---
p = os.path.join(ROOT, "source", "net.h")
s = open(p, encoding="utf-8").read()
lines = [l for l in s.splitlines() if l.strip()]
out = []
for l in lines:
    if out and out[-1].strip() == l.strip():
        continue
    out.append(l)
open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")

# --- main.c ---
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


rep('#include "history.h"', '#include "history.h"\n#include "steamsearch.h"')
rep("#include <math.h>", "#include <math.h>\n#include <sys/stat.h>\n#include <errno.h>")

# ---------- каталог: сначала SD, потом romfs ----------
rep("""    char path[128];
    snprintf(path, sizeof(path), "romfs:/catalog/%.32s.json", appid);

    FILE *file = fopen(path, "rb");
    if (!file) return -1;""",
    """    char path[192];

    snprintf(path, sizeof(path), "sdmc:/switch/NX-Stach/catalog/%.32s.json", appid);
    FILE *file = fopen(path, "rb");

    if (!file) {
        snprintf(path, sizeof(path), "romfs:/catalog/%.32s.json", appid);
        file = fopen(path, "rb");
    }

    if (!file) return -1;""")

# ---------- иконки: сначала SD, потом romfs ----------
rep("""    char path[256];
    snprintf(path, sizeof(path), "romfs:/catalog/icons/%.32s/%.96s.jpg",
             appid, id);

    FILE *file = fopen(path, "rb");
    if (!file) return NULL;""",
    """    char path[256];

    snprintf(path, sizeof(path),
             "sdmc:/switch/NX-Stach/catalog/icons/%.32s/%.96s.jpg", appid, id);
    FILE *file = fopen(path, "rb");

    if (!file) {
        snprintf(path, sizeof(path), "romfs:/catalog/icons/%.32s/%.96s.jpg",
                 appid, id);
        file = fopen(path, "rb");
    }

    if (!file) return NULL;""")

# ---------- состояние поиска ----------
rep("""    float toggle_anim = 0.0f;""",
    """    float toggle_anim = 0.0f;

    SteamSearchResult steam_results[STEAM_MAX_RESULTS];
    int steam_result_count = 0;
    int steam_selected = 0;
    int steam_mode = 0;      // 1 = окно выбора игры из Steam
    int import_request = 0;
    int import_title_index = 0;""")

# ---------- модальное окно: ввод ----------
rep("""        bool consumed = false;

        /* ------------------------------- тапы ------------------------------- */
        if (touch_tapped) {""",
    """        bool consumed = false;

        if (steam_mode == 1) {
            if (steam_result_count > 0) {
                if (kDown & HidNpadButton_Down)
                    steam_selected = (steam_selected + 1) % steam_result_count;
                if (kDown & HidNpadButton_Up)
                    steam_selected = (steam_selected + steam_result_count - 1) %
                                     steam_result_count;
                if (kDown & HidNpadButton_A)
                    import_request = 1;
            }

            if (kDown & HidNpadButton_B)
                steam_mode = 0;

            consumed = true;
        }

        /* ------------------------------- тапы ------------------------------- */
        if (!consumed && touch_tapped) {""")

# ---------- X: поиск в Steam ----------
rep("""            if (!consumed && screen == 0 && (kDown & HidNpadButton_Y)) {""",
    """            if (!consumed && screen == 0 && (kDown & HidNpadButton_X) && view_count > 0) {
                char query[64];
                snprintf(query, sizeof(query), "%s", games[view[selected]].name);

                if (ask_search(query, sizeof(query)) && query[0]) {
                    steam_result_count = 0;
                    steam_selected = 0;

                    steam_result_count = steam_search(query, steam_results,
                                                      STEAM_MAX_RESULTS);

                    if (steam_result_count > 0) {
                        steam_mode = 1;
                        import_title_index = view[selected];
                    }
                }

                consumed = true;
            }

            if (!consumed && screen == 0 && (kDown & HidNpadButton_Y)) {""")

open(p, "w", encoding="utf-8").write(s)
print("main patched")
