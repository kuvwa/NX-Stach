import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


# --- SD-first каталог ---
rep("""    char path[128];
    snprintf(path, sizeof(path), "romfs:/catalog/%.32s.json", appid);

    FILE *file = fopen(path, "rb");
    if (!file) return -1;""",
    """    char path[192];

    snprintf(path, sizeof(path),
             "sdmc:/switch/NX-Stach/catalog/%.32s.json", appid);
    FILE *file = fopen(path, "rb");

    if (!file) {
        snprintf(path, sizeof(path), "romfs:/catalog/%.32s.json", appid);
        file = fopen(path, "rb");
    }

    if (!file) return -1;""")

# --- SD-first иконки достижений ---
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

# --- предзагрузка первых 8 иконок ---
rep("                        for (int i = 0; i < steam_result_count; i++) {",
    "                        for (int i = 0; i < steam_result_count && i < 8; i++) {")

open(p, "w", encoding="utf-8").write(s)
print("ok")
