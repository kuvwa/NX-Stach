import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


splash = r'''static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)
{
    for (int frame = 0; frame < 68; frame++) {
        u32 stride;
        u32 *px = (u32 *)framebufferBegin(fb, &stride);
        fb_width = stride / sizeof(u32);

        fill_bg(px, COLOR_BG);

        clip_left = 0;
        clip_right = W;
        clip_top = 0;
        clip_bottom = H;

        int tw = measure_text(face, "NX-Stach");
        draw_text_shine(face, px, (W - tw) / 2, H / 2 - 8, "NX-Stach",
                        frame * 30);

        const char *sub = "Developed by kuba";
        int sw = measure_text(face_small, sub);

        set_text_color(112, 118, 130);
        draw_text(face_small, px, (W - sw) / 2, H / 2 + 42, sub);
        reset_text_color();

        framebufferEnd(fb);
    }
}

'''

rep("/* --------------------------------- main --------------------------------- */",
    splash + "/* --------------------------------- main --------------------------------- */")

rep("""    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""",
    """    show_splash(&fb, face, face_small);

    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
