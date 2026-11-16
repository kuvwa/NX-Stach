import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# --- чёрный ящик ---
rep("/* --------------------------------- main --------------------------------- */",
r'''static const char *g_stage = "init";
static int g_detail = -1;

static void beat(const char *stage, int detail)
{
    g_stage = stage;
    g_detail = detail;
}

static void beat_flush(void)
{
    FILE *f = fopen("sdmc:/switch/NX-Stach/last_frame.txt", "w");

    if (!f) return;

    fprintf(f, "stage=%s detail=%d\n", g_stage, g_detail);
    fclose(f);
}

/* --------------------------------- main --------------------------------- */''')

# --- отмечаем этапы в главном цикле ---
rep("""        padUpdate(&pad);
        u32 kDown = padGetButtonsDown(&pad);
        u32 held = padGetButtons(&pad);""",
    """        beat("input", 0);

        padUpdate(&pad);
        u32 kDown = padGetButtonsDown(&pad);
        u32 held = padGetButtons(&pad);""")

rep("""        fill_bg(pixels, COLOR_BG);
        clip_top = 0;
        clip_bottom = H;

        if (screen == 0) {""",
    """        beat("clear", 0);

        fill_bg(pixels, COLOR_BG);
        clip_top = 0;
        clip_bottom = H;

        if (screen == 0) {""")

rep("""                int game_index = view[i];
                const u32 *cover = library_cover(games[game_index].title_id);""",
    """                beat("tile", i);

                int game_index = view[i];
                const u32 *cover = library_cover(games[game_index].title_id);""")

rep("""            rect(pixels, 0, 0, W, HEADER_H, COLOR_BG);

            draw_text_shine""",
    """            beat("header", 0);

            rect(pixels, 0, 0, W, HEADER_H, COLOR_BG);

            draw_text_shine""")

rep("""            build_list(game->steam_appid, achievements, achievement_count,""",
    """            beat("ach_list", 0);

            build_list(game->steam_appid, achievements, achievement_count,""")

rep("""        framebufferEnd(&fb);""",
    """        beat("present", 0);
        beat_flush();

        framebufferEnd(&fb);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
