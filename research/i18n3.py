import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


lang_code = '''static int lang = 0;   // 0 = English, 1 = Russian

static const char *L(const char *en, const char *ru)
{
    return lang ? ru : en;
}

static void lang_load(void)
{
    FILE *f = fopen("sdmc:/switch/NX-Stach/settings.ini", "r");

    if (!f) return;

    char line[64];

    while (fgets(line, sizeof(line), f)) {
        int v = 0;

        if (sscanf(line, "lang=%d", &v) == 1)
            lang = v ? 1 : 0;
    }

    fclose(f);
}

static void lang_save(void)
{
    FILE *f = fopen("sdmc:/switch/NX-Stach/settings.ini", "w");

    if (!f) return;

    fprintf(f, "lang=%d\\n", lang);
    fclose(f);
}

'''

rep("static int measure_text(FT_Face face, const char *str);",
    "static int measure_text(FT_Face face, const char *str);\n\n" + lang_code)

rep("    save_init();", "    save_init();\n    lang_load();")

# поиск ниже
rep("round_rect(pixels, 55, 86, 1170, 52, 14, COLOR_PANEL);",
    "round_rect(pixels, 55, 104, 1170, 52, 14, COLOR_PANEL);")

rep("draw_text(face_small, pixels, 78, 116, search);",
    "draw_text(face_small, pixels, 78, 136, search);")

rep('draw_text(face_small, pixels, 78, 116, L("Search...", ',
    'draw_text(face_small, pixels, 78, 136, L("Search...", ')

open(p, "w", encoding="utf-8").write(s)
print("ok")
