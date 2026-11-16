import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# ---------- 6 карточек в ряд ----------
rep("""#define CARD_W 190
#define CARD_H 190
#define GRID_COLS 5
#define GRID_GAP_X 55
#define GRID_GAP_Y 25""",
    """#define CARD_W 175
#define CARD_H 175
#define GRID_COLS 6
#define GRID_GAP_X 30
#define GRID_GAP_Y 30""")

# ---------- фон шапки из обложки ----------
rep("""/* --------------------------- ачивки: иконки --------------------------- */""",
    r'''#define HEADER_BG_H 210

static u32 *header_bg = NULL;
static int header_bg_ready = 0;

// Сильно размытая и затемнённая обложка — фон шапки.
static void build_header_bg(u64 title_id)
{
    header_bg_ready = 0;

    const u32 *cover = library_cover(title_id);

    if (!cover) return;

    if (!header_bg) {
        header_bg = malloc((size_t)W * HEADER_BG_H * sizeof(u32));
        if (!header_bg) return;
    }

    const int block = 14;
    int sw = (W + block - 1) / block;
    int sh = (HEADER_BG_H + block - 1) / block;

    u32 *small = malloc((size_t)sw * sh * sizeof(u32));

    if (!small) return;

    // уменьшенная копия обложки, растянутой на весь заголовок
    for (int sy = 0; sy < sh; sy++) {
        int sy_src = sy * block * LIB_COVER_H / HEADER_BG_H;
        if (sy_src >= LIB_COVER_H) sy_src = LIB_COVER_H - 1;

        for (int sx = 0; sx < sw; sx++) {
            int sx_src = sx * block * LIB_COVER_W / W;
            if (sx_src >= LIB_COVER_W) sx_src = LIB_COVER_W - 1;

            small[(size_t)sy * sw + sx] = cover[(size_t)sy_src * LIB_COVER_W + sx_src];
        }
    }

    for (int y = 0; y < HEADER_BG_H; y++) {
        int iy = y * sh / HEADER_BG_H;
        int iy1 = (iy + 1 < sh) ? iy + 1 : iy;
        int ty = (y * sh) % HEADER_BG_H;

        for (int x = 0; x < W; x++) {
            int ix = x * sw / W;
            int ix1 = (ix + 1 < sw) ? ix + 1 : ix;
            int tx = (x * sw) % W;

            u32 c00 = small[(size_t)iy * sw + ix];
            u32 c10 = small[(size_t)iy * sw + ix1];
            u32 c01 = small[(size_t)iy1 * sw + ix];
            u32 c11 = small[(size_t)iy1 * sw + ix1];

            int r = 0, g = 0, b = 0;

            for (int k = 0; k < 2; k++) {
                int wy = k ? ty : (block - ty);
                u32 t = k ? c01 : c00;
                u32 bo = k ? c11 : c10;

                for (int m = 0; m < 2; m++) {
                    int wx = m ? tx : (block - tx);
                    u32 c = m ? bo : t;
                    int wgt = wx * wy;

                    r += (c & 0xFF) * wgt;
                    g += ((c >> 8) & 0xFF) * wgt;
                    b += ((c >> 16) & 0xFF) * wgt;
                }
            }

            int div = block * block;
            u32 blurred = RGBA8_MAXALPHA(r / div, g / div, b / div);

            // затемняем к низу, чтобы текст читался
            int alpha = 150 + 70 * y / HEADER_BG_H;

            header_bg[(size_t)y * W + x] =
                blend_px(blurred, RGBA8_MAXALPHA(10, 11, 14), alpha);
        }
    }

    free(small);
    header_bg_ready = 1;
}

static void draw_header_bg(u32 *fb)
{
    if (!header_bg_ready || !header_bg) return;

    for (int y = 0; y < HEADER_BG_H; y++) {
        if (y >= H) break;
        memcpy(fb + (size_t)y * fb_width, header_bg + (size_t)y * W,
               (size_t)W * sizeof(u32));
    }
}

/* --------------------------- ачивки: иконки --------------------------- */''')

# ---------- пульс выбранной карточки ----------
rep("""                    int grow = (int)(hover_anim * 6.0f);""",
    """                    int grow = (int)(hover_anim * 6.0f);""")

rep("""                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);
                    int grow = (int)(hover_anim * 6.0f);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 34 + grow, glow, 78);

                    round_rect(pixels, x - 3, y - 3, CARD_W + 6, CARD_H + 6,
                               10, COLOR_SELECT);
                }""",
    """                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);
                    int grow = (int)(hover_anim * 4.0f);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 30 + grow, glow,
                              (int)(48 + 42 * pulse));

                    u32 frame = blend_px(COLOR_BG, COLOR_SELECT,
                                         (int)(120 + 130 * pulse));

                    round_rect(pixels, x - 3, y - 3, CARD_W + 6, CARD_H + 6,
                               10, frame);
                }""")

# тик для пульса
rep("""    u32 shine_counter = 0;""",
    """    u32 shine_counter = 0;
    u32 tick = 0;
    float pulse = 1.0f;""")

rep("""        hover_anim += (1.0f - hover_anim) * 0.22f;""",
    """        tick++;
        pulse = 0.5f + 0.5f * sinf((float)tick * 0.19f);

        hover_anim += (1.0f - hover_anim) * 0.22f;""")

# ---------- B сбрасывает поиск ----------
rep("""            } else {
                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }""",
    """            } else {
                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }""")

rep("""        if (!consumed) {
            if (screen == 0) {""",
    """        if (!consumed) {
            if (screen == 0 && (kDown & HidNpadButton_B) && search[0]) {
                search[0] = '\\0';
                selected = 0;
                grid_scroll = grid_target = 0.0f;

                view_count = 0;
                for (int i = 0; i < game_count; i++)
                    view[view_count++] = i;

                consumed = true;
            }

            if (!consumed && screen == 0) {""")

rep("""            } else {
                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }

                if (kDown & HidNpadButton_Down) list_target += ROW_H;""",
    """            } else if (screen == 1) {
                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }

                if (kDown & HidNpadButton_Down) list_target += ROW_H;""")

# ---------- фон шапки ачивок ----------
rep("""                    ach_icons_load(game->steam_appid, achievement_count, achievements);
                    playtime_minutes = game_playtime_minutes(game->title_id);""",
    """                    ach_icons_load(game->steam_appid, achievement_count, achievements);
                    playtime_minutes = game_playtime_minutes(game->title_id);
                    build_header_bg(game->title_id);""")

rep("""            rect(pixels, 0, 0, W, LIST_TOP - 6, COLOR_BG);""",
    """            rect(pixels, 0, 0, W, LIST_TOP - 6, COLOR_BG);
            draw_header_bg(pixels);""")

rep("""    free(glass_buf);
    framebufferClose(&fb);""",
    """    framebufferClose(&fb);""") if "free(glass_buf);" in s else None

rep("""    framebufferClose(&fb);
    FT_Done_Face(face_small);""",
    """    free(header_bg);
    framebufferClose(&fb);
    FT_Done_Face(face_small);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
