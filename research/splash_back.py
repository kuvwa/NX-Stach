import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


splash = (
"static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)\n"
"{\n"
"    for (int frame = 0; frame < 68; frame++) {\n"
"        u32 stride;\n"
"        u32 *px = (u32 *)framebufferBegin(fb, &stride);\n"
"        fb_width = stride / sizeof(u32);\n"
"\n"
"        fill_bg(px, COLOR_BG);\n"
"\n"
"        clip_left = 0;\n"
"        clip_right = W;\n"
"        clip_top = 0;\n"
"        clip_bottom = H;\n"
"\n"
"        int tw = measure_text(face, \"NX-Stach\");\n"
"        draw_text_shine(face, px, (W - tw) / 2, H / 2 - 8, \"NX-Stach\",\n"
"                        frame * 30);\n"
"\n"
"        const char *sub = \"Developed by kuba\";\n"
"        int sw = measure_text(face_small, sub);\n"
"\n"
"        set_text_color(112, 118, 130);\n"
"        draw_text(face_small, px, (W - sw) / 2, H / 2 + 42, sub);\n"
"        reset_text_color();\n"
"\n"
"        framebufferEnd(fb);\n"
"    }\n"
"}\n"
"\n")

rep("/* --------------------------------- main --------------------------------- */",
    splash + "/* --------------------------------- main --------------------------------- */")

rep("""    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""",
    """    show_splash(&fb, face, face_small);

    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
