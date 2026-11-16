import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:140])
    s = s.replace(old, new, 1)


# ---------- закреплённые игры ----------
pins_code = (
"static u64 pins[MAX_GAMES];\n"
"static int pin_count = 0;\n"
"\n"
"static bool is_pinned(u64 id)\n"
"{\n"
"    for (int i = 0; i < pin_count; i++)\n"
"        if (pins[i] == id)\n"
"            return true;\n"
"\n"
"    return false;\n"
"}\n"
"\n"
"static void pins_save(void)\n"
"{\n"
"    FILE *f = fopen(\"sdmc:/switch/NX-Stach/pins.txt\", \"w\");\n"
"\n"
"    if (!f) return;\n"
"\n"
"    for (int i = 0; i < pin_count; i++)\n"
"        fprintf(f, \"%016llX\\n\", (unsigned long long)pins[i]);\n"
"\n"
"    fclose(f);\n"
"}\n"
"\n"
"static void pins_load(void)\n"
"{\n"
"    FILE *f = fopen(\"sdmc:/switch/NX-Stach/pins.txt\", \"r\");\n"
"\n"
"    pin_count = 0;\n"
"\n"
"    if (!f) return;\n"
"\n"
"    char line[64];\n"
"\n"
"    while (fgets(line, sizeof(line), f) && pin_count < MAX_GAMES) {\n"
"        unsigned long long v = 0;\n"
"\n"
"        if (sscanf(line, \"%llX\", &v) == 1 && v)\n"
"            pins[pin_count++] = (u64)v;\n"
"    }\n"
"\n"
"    fclose(f);\n"
"}\n"
"\n"
"static void pin_toggle(u64 id)\n"
"{\n"
"    for (int i = 0; i < pin_count; i++) {\n"
"        if (pins[i] != id)\n"
"            continue;\n"
"\n"
"        for (int k = i; k + 1 < pin_count; k++)\n"
"            pins[k] = pins[k + 1];\n"
"\n"
"        pin_count--;\n"
"        pins_save();\n"
"        return;\n"
"    }\n"
"\n"
"    if (pin_count < MAX_GAMES)\n"
"        pins[pin_count++] = id;\n"
"\n"
"    pins_save();\n"
"}\n"
"\n")

rep("static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)",
    pins_code + "static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)")

# ---------- загрузка закрепов ----------
rep("    save_init();\n    lang_load();", "    save_init();\n    lang_load();\n    pins_load();")

# ---------- перестроение списка с закрепами ----------
rebuild = (
"static void rebuild_view(int *view, int *view_count, Game *games,\n"
"                         int game_count, const char *search)\n"
"{\n"
"    *view_count = 0;\n"
"\n"
"    for (int pass = 0; pass < 2; pass++) {\n"
"        for (int i = 0; i < game_count && *view_count < MAX_GAMES; i++) {\n"
"            bool pinned = is_pinned(games[i].title_id);\n"
"\n"
"            if ((pass == 0) != pinned)\n"
"                continue;\n"
"\n"
"            if (!text_contains(games[i].name, search))\n"
"                continue;\n"
"\n"
"            view[(*view_count)++] = i;\n"
"        }\n"
"    }\n"
"}\n"
"\n")

rep("/* --------------------------------- main --------------------------------- */",
    rebuild + "/* --------------------------------- main --------------------------------- */")

open(p, "w", encoding="utf-8").write(s)
print("ok")
