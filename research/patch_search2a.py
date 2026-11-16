import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


PROGRESS = '''static void draw_progress(Framebuffer *fb, FT_Face face, FT_Face face_small,
                          const char *title, const char *line, int percent)
{
    u32 stride;
    u32 *px = (u32 *)framebufferBegin(fb, &stride);
    fb_width = stride / sizeof(u32);

    fill_bg(px, COLOR_BG);

    draw_text(face, px, 55, 300, title);

    set_text_color(170, 175, 185);
    draw_text(face_small, px, 55, 340, line);
    reset_text_color();

    round_rect(px, 55, 370, 1170, 16, 8, COLOR_TRACK);

    if (percent > 0)
        round_rect(px, 55, 370, 1170 * percent / 100, 16, 8, COLOR_ACCENT);

    framebufferEnd(fb);
}

'''

rep("/* ------------------------------- стики ------------------------------- */",
    PROGRESS + "/* ------------------------------- стики ------------------------------- */")

rep("""    int import_request = 0;
    int import_title_index = 0;""",
    """    int import_request = 0;
    int import_title_index = 0;
    char toast[128] = "";
    int toast_frames = 0;""")

rep("""                    if (steam_result_count > 0) {
                        steam_mode = 1;
                        import_title_index = view[selected];
                    }""",
    """                    if (steam_result_count > 0) {
                        steam_mode = 1;
                        import_title_index = view[selected];
                    } else {
                        snprintf(toast, sizeof(toast), "В Steam ничего не найдено");
                        toast_frames = 150;
                    }""")

open(p, "w", encoding="utf-8").write(s)
print("part1 ok")
