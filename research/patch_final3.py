import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# ---------- 1. бегущая строка: средняя скорость ----------
rep("""                        ? (int)((tick / 3) % (u32)cycle) : 0;""",
    """                        ? (int)(tick % (u32)cycle) : 0;""")

# ---------- 2. фон шапки: ярче, длиннее ----------
rep("#define HEADER_BG_H 210", "#define HEADER_BG_H 260")

rep("""    // приглушаем и затемняем цвет
    u32 base = blend_px(dom, RGBA8_MAXALPHA(12, 13, 17), 105);

    for (int y = 0; y < HEADER_BG_H; y++) {
        float t = 1.0f - (float)y / (float)HEADER_BG_H;
        t = t * t;

        int alpha = (int)(200.0f * t);

        u32 color = blend_px(COLOR_BG, base, alpha);

        for (int x = 0; x < W; x++)
            header_bg[(size_t)y * W + x] = color;
    }""",
    """    // вытягиваем цвет наверх по яркости, чтобы тёмные обложки тоже светились
    int cr = dom & 0xFF;
    int cg = (dom >> 8) & 0xFF;
    int cb = (dom >> 16) & 0xFF;

    int mx = cr > cg ? (cr > cb ? cr : cb) : (cg > cb ? cg : cb);

    if (mx > 0 && mx < 210) {
        int k = 210 * 100 / mx;
        cr = cr * k / 100;
        cg = cg * k / 100;
        cb = cb * k / 100;

        if (cr > 235) cr = 235;
        if (cg > 235) cg = 235;
        if (cb > 235) cb = 235;
    }

    u32 bright = RGBA8_MAXALPHA(cr, cg, cb);
    u32 base = blend_px(bright, RGBA8_MAXALPHA(10, 11, 14), 60);

    for (int y = 0; y < HEADER_BG_H; y++) {
        float t = 1.0f - (float)y / (float)HEADER_BG_H;
        t = powf(t, 1.7f);

        int alpha = (int)(238.0f * t);

        u32 color = blend_px(COLOR_BG, base, alpha);

        for (int x = 0; x < W; x++)
            header_bg[(size_t)y * W + x] = color;
    }""")

# ---------- 3. больше отступа сверху в шапке ----------
rep("#define LIST_TOP 316", "#define LIST_TOP 342")

rep("""                draw_cover(pixels, 55, 20, 120, cover, COLOR_BG, 16);
            else
                round_rect(pixels, 55, 20, 120, 120, 16, COLOR_PANEL);""",
    """                draw_cover(pixels, 55, 38, 120, cover, COLOR_BG, 16);
            else
                round_rect(pixels, 55, 38, 120, 120, 16, COLOR_PANEL);""")

rep("""            draw_text(face, pixels, 200, 60, game->name);""",
    """            draw_text(face, pixels, 200, 78, game->name);""")

rep("""            draw_text(face_small, pixels, 200, 92, stats);""",
    """            draw_text(face_small, pixels, 200, 110, stats);""")

rep("""            round_rect(pixels, 55, 152, 1170, 76, 16, COLOR_PANEL);""",
    """            round_rect(pixels, 55, 176, 1170, 76, 16, COLOR_PANEL);""")

rep("""            draw_text(face_small, pixels, 85, 182, progress);""",
    """            draw_text(face_small, pixels, 85, 206, progress);""")

rep("""            round_rect(pixels, 85, 196, bar_w, 12, 6, COLOR_TRACK);
            if (filled > 0)
                round_rect(pixels, 85, 196, filled, 12, 6, COLOR_ACCENT);""",
    """            round_rect(pixels, 85, 220, bar_w, 12, 6, COLOR_TRACK);
            if (filled > 0)
                round_rect(pixels, 85, 220, filled, 12, 6, COLOR_ACCENT);""")

rep("""            draw_text(face_small, pixels, 55, 280, "Только невыполненные");""",
    """            draw_text(face_small, pixels, 55, 306, "Только невыполненные");""")

rep("""            draw_toggle(pixels, 1138, 251, toggle_anim);""",
    """            draw_toggle(pixels, 1138, 277, toggle_anim);""")

# зона тапа тумблера
rep("""                } else if (tap_y >= 250 && tap_y <= 306) {""",
    """                } else if (tap_y >= 276 && tap_y <= 332) {""")

# сообщение об отсутствии каталога
rep("""                draw_text(face_small, pixels, 55, 380, "Нет каталога достижений");
                draw_text(face_small, pixels, 55, 410,""",
    """                draw_text(face_small, pixels, 55, 410, "Нет каталога достижений");
                draw_text(face_small, pixels, 55, 440,""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
