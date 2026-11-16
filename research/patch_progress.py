import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


rep("""/* ------------------------------- стики ------------------------------- */""",
r'''static void draw_progress(Framebuffer *fb, FT_Face face, FT_Face face_small,
                          const char *title, const char *line, int percent)
{
    u32 stride;
    u32 *px = (u32 *)framebufferBegin(fb, &stride);
    fb_width = stride / sizeof(u32);

    fill_bg(px, COLOR_BG);

    clip_left = 0;
    clip_right = W;
    clip_top = 0;
    clip_bottom = H;

    draw_text(face, px, 55, 300, title);

    set_text_color(170, 175, 185);
    draw_text(face_small, px, 55, 340, line);
    reset_text_color();

    round_rect(px, 55, 370, 1170, 16, 8, COLOR_TRACK);

    if (percent > 0)
        round_rect(px, 55, 370, 1170 * percent / 100, 16, 8, COLOR_ACCENT);

    framebufferEnd(fb);
}

/* ------------------------------- стики ------------------------------- */''')

rep("""    float toggle_anim = 0.0f;""",
    """    float toggle_anim = 0.0f;

    char toast[160] = "";
    int toast_frames = 0;""")

rep("""        framebufferEnd(&fb);

        tick++;""",
    """        if (toast_frames > 0) {
            int tw = measure_text(face_small, toast);
            int w = tw + 48;

            if (w > W - 80) w = W - 80;

            int x = (W - w) / 2;
            int y = H - 96;

            round_rect(pixels, x, y, w, 46, 14, RGBA8_MAXALPHA(52, 56, 63));

            clip_left = x + 20;
            clip_right = x + w - 20;
            set_text_color(235, 240, 250);
            draw_text(face_small, pixels, x + 24, y + 30, toast);
            reset_text_color();
            clip_left = 0;
            clip_right = W;

            toast_frames--;
        }

        framebufferEnd(&fb);

        tick++;""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
