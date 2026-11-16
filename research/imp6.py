import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s: %s" % (path, old[:100]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


patch("source/steamsearch.h", [
("#define STEAM_MAX_RESULTS 6", "#define STEAM_MAX_RESULTS 24"),
])

patch("source/main.c", [
# каталог: сначала SD, потом romfs
("""    char path[128];
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

    if (!file) return -1;"""),

# иконки достижений: сначала SD, потом romfs
("""    char path[256];
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

    if (!file) return NULL;"""),
])
