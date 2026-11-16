import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, count)


# ---------- 1. helpers: blend / glow / иконки кнопок ----------
old = """/* --------------------------- иконки достижений --------------------------- */"""
new = r'''static u32 blend_px(u32 bg, u32 fg, int a)
{
    if (a <= 0) return bg;
    if (a >= 255) return fg;

    int br = bg & 0xFF, bg_g = (bg >> 8) & 0xFF, bb = (bg >> 16) & 0xFF;
    int fr = fg & 0xFF, fg_g = (fg >> 8) & 0xFF, fb_ = (fg >> 16) & 0xFF;

    int r = br + (fr - br) * a / 255;
    int g = bg_g + (fg_g - bg_g) * a / 255;
    int b = bb + (fb_ - bb) * a / 255;

    return RGBA8_MAXALPHA(r, g, b);
}

// Мягкое свечение вокруг плитки.
static void draw_glow(u32 *fb, int x, int y, int size, int radius,
                      int spread, u32 color, int strength)
{
    int cx = x + size / 2;
    int cy = y + size / 2;
    int half = size / 2;
    int outer = half + spread;
    int inner = half - radius;

    for (int py = cy - outer; py <= cy + outer; py++) {
        if (py < 0 || py >= H) continue;

        for (int px = cx - outer; px <= cx + outer; px++) {
            if (px < 0 || px >= W) continue;

            int dx = abs(px - cx) - inner;
            int dy = abs(py - cy) - inner;

            if (dx < 0) dx = 0;
            if (dy < 0) dy = 0;

            float d = sqrtf((float)(dx * dx + dy * dy)) - (float)radius;

            if (d < 0.0f || d > (float)spread) continue;

            int a = (int)((float)strength * (1.0f - d / (float)spread));
            if (a <= 0) continue;

            u32 *dst = &fb[(size_t)py * fb_width + px];
            *dst = blend_px(*dst, color, a);
        }
    }
}

static void draw_icon_letter(FT_Face face, u32 *fb, int x, int y, int size,
                             const char *letter)
{
    round_rect(fb, x, y, size, size, size / 2, RGBA8_MAXALPHA(62, 66, 74));

    int w = measure_text(face, letter);
    int h = 14;

    draw_text(face, fb, x + (size - w) / 2, y + (size + h) / 2, letter);
}

static void draw_icon_pill(FT_Face face, u32 *fb, int x, int y, int w, int h,
                           const char *letter)
{
    round_rect(fb, x, y, w, h, h / 2, RGBA8_MAXALPHA(62, 66, 74));

    int tw = measure_text(face, letter);
    draw_text(face, fb, x + (w - tw) / 2, y + h / 2 + 7, letter);
}

static void draw_icon_dpad(u32 *fb, int x, int y, int size)
{
    int arm = size / 3;
    u32 c = RGBA8_MAXALPHA(70, 74, 82);
    int cx = x + size / 2, cy = y + size / 2;

    round_rect(fb, cx - arm / 2, y, arm, size, 4, c);
    round_rect(fb, x, cy - arm / 2, size, arm, 4, c);
}

static void draw_icon_stick(u32 *fb, int x, int y, int size)
{
    round_rect(fb, x, y, size, size, size / 2, RGBA8_MAXALPHA(58, 62, 70));
    round_rect(fb, x + size / 3, y + size / 3, size / 3, size / 3, size / 6,
               RGBA8_MAXALPHA(200, 205, 215));
}

static void draw_icon_touch(u32 *fb, int x, int y, int size)
{
    round_rect(fb, x + size / 3, y + size / 6, size / 3, size / 2, size / 6,
               RGBA8_MAXALPHA(215, 220, 230));
    round_rect(fb, x + size / 6, y + size * 3 / 5, size * 2 / 3, 4, 2,
               RGBA8_MAXALPHA(120, 200, 255));
    round_rect(fb, x + size / 6, y + size * 3 / 4, size * 2 / 3, 4, 2,
               RGBA8_MAXALPHA(120, 200, 255));
}

/* --------------------------- иконки достижений --------------------------- */'''

rep(old, new)

# ---------- 2. каталог грузим локально, сеть только если локального нет ----------
old = """                    if (game->steam_appid[0]) {
                        if (net_ready) {
                            char *response = malloc(262144);

                            if (response) {
                                char path[192];
                                snprintf(path, sizeof(path),
                                    \"/IPlayerService/GetGameAchievements/v1/?appid=%s&language=english\",
                                    game->steam_appid);

                                if (net_https_get(\"api.steampowered.com\",
                                                  path, response, 262144))
                                    achievement_count = steam_parse_achievements(
                                        response, achievements, MAX_ACHIEVEMENTS);

                                free(response);
                            }
                        }

                        if (achievement_count <= 0)
                            achievement_count = romfs_ready
                                ? load_catalog(game->steam_appid, achievements,
                                               MAX_ACHIEVEMENTS)
                                : 0;
"""
new = """                    if (game->steam_appid[0]) {
                        // сначала локальный каталог (мгновенно), сеть — только если его нет
                        achievement_count = romfs_ready
                            ? load_catalog(game->steam_appid, achievements,
                                           MAX_ACHIEVEMENTS)
                            : 0;

                        if (achievement_count <= 0 && net_ready) {
                            char *response = malloc(262144);

                            if (response) {
                                char path[192];
                                snprintf(path, sizeof(path),
                                    \"/IPlayerService/GetGameAchievements/v1/?appid=%s&language=english\",
                                    game->steam_appid);

                                if (net_https_get(\"api.steampowered.com\",
                                                  path, response, 262144))
                                    achievement_count = steam_parse_achievements(
                                        response, achievements, MAX_ACHIEVEMENTS);

                                free(response);
                            }
                        }
"""
rep(old, new)

# ---------- 3. навигация: свободный скролл ----------
old = """                if (view_count > 0) {
                    if (kDown & HidNpadButton_Right)
                        selected = (selected + 1) % view_count;
                    if (kDown & HidNpadButton_Left)
                        selected = (selected + view_count - 1) % view_count;
                    if ((kDown & HidNpadButton_Down) && selected + GRID_COLS < view_count)
                        selected += GRID_COLS;
                    if ((kDown & HidNpadButton_Up) && selected >= GRID_COLS)
                        selected -= GRID_COLS;
                }

                HidAnalogStickState stick = padGetStickPos(&pad, 0);

                if (stick.y > 16000 || stick.y < -16000) {
                    if (!stick_latch && view_count > 0) {
                        stick_latch = true;

                        if (stick.y < 0) {
                            if (selected + GRID_COLS < view_count)
                                selected += GRID_COLS;
                        } else {
                            if (selected >= GRID_COLS)
                                selected -= GRID_COLS;
                        }
                    }
                } else {
                    stick_latch = false;
                }
"""
new = """                if (view_count > 0) {
                    if (kDown & HidNpadButton_Right)
                        selected = (selected + 1) % view_count;
                    if (kDown & HidNpadButton_Left)
                        selected = (selected + view_count - 1) % view_count;
                    if (kDown & HidNpadButton_Down)
                        grid_target += GRID_STEP_Y;
                    if (kDown & HidNpadButton_Up)
                        grid_target -= GRID_STEP_Y;
                }

                HidAnalogStickState stick = padGetStickPos(&pad, 0);

                if (stick.y > 16000 || stick.y < -16000 || 
                    stick.y < -16000) {
                    if (!stick_latch) {
                        stick_latch = true;
                        grid_target += (stick.y > 0 ? GRID_STEP_Y : -GRID_STEP_Y);
                    }
                } else {
                    stick_latch = false;
                }
"""
rep(old, new)

# ---------- 4. убрать авто-подтягивание к выбранной плитке ----------
old = """            if (!touch_dragged) {
                int row = selected / GRID_COLS;
                float top = (float)row * GRID_STEP_Y;

                if (top < grid_target) grid_target = top;
                if (top + GRID_STEP_Y > grid_target + visible)
                    grid_target = top + GRID_STEP_Y - visible;
            }

"""
new = ""
rep(old, new)

# ---------- 5. удержание 0.5 сек ----------
rep("if (hold_frames > 90 && (hold_frames % 4) == 0) {",
    "if (hold_frames > 30 && (hold_frames % 4) == 0) {")

# ---------- 6. удалить кнопку назад (рисование) ----------
old = """            round_rect(pixels, 55, 26, 52, 52, 16, COLOR_PANEL);
            set_text_color(220, 226, 236);
            draw_text(face, pixels, 72, 64, "‹");
            reset_text_color();

"""
new = ""
rep(old, new)

# ---------- 7. glow у выбранной игры ----------
old = """                if (i == selected && cover)
                    round_rect(pixels, x - 7, y - 7, COVER_SIZE + 14,
                               COVER_SIZE + 14, 24, COLOR_ACCENT);
"""
new = """                if (i == selected) {
                    draw_glow(pixels, x, y, COVER_SIZE, 18, 26, COLOR_ACCENT, 70);

                    if (cover)
                        round_rect(pixels, x - 5, y - 5, COVER_SIZE + 10,
                                   COVER_SIZE + 10, 22, COLOR_ACCENT);
                }
"""
rep(old, new)

# ---------- 8. Y в строке поиска — ближе к краю, плашкой ----------
old = """            set_text_color(110, 115, 125);
            draw_text(face_small, pixels, W - 130, 120, "Y");
            reset_text_color();
"""
new = """            set_text_color(225, 230, 240);
            draw_icon_letter(face_small, pixels, W - 96, 98, 28, "Y");
            reset_text_color();
"""
rep(old, new)

# ---------- 9. анимации тумблера + гайда ----------
rep("""    int selected = 0;
    int screen = 0;
    int guide_open = 0;
    int only_locked = 0;""",
    """    int selected = 0;
    int screen = 0;
    int guide_open = 0;
    int only_locked = 0;

    float toggle_anim = 0.0f;
    float guide_anim = 0.0f;""")

rep("""            draw_toggle(pixels, 1140, 252, only_locked != 0);""",
    """            {
                int kn = (int)(toggle_anim * 38.0f);
                round_rect(pixels, 1140, 252, 62, 32, 16,
                           toggle_anim > 0.5f ? COLOR_ACCENT : COLOR_TRACK);
                round_rect(pixels, 1144 + kn, 256, 24, 24, 12,
                           RGBA8_MAXALPHA(245, 248, 252));
            }""")

rep("""        shine_counter = (u32)(shine_counter + 30);""",
    """        toggle_anim += ((only_locked ? 1.0f : 0.0f) - toggle_anim) * 0.25f;
        guide_anim += ((guide_open ? 1.0f : 0.0f) - guide_anim) * 0.22f;

        shine_counter = (u32)(shine_counter + 30);""")

# ---------- 10. новый гайд ----------
old = s[s.find("        if (guide_open) {"):s.find("        framebufferEnd(&fb);")]
new = r'''        if (guide_anim > 0.04f) {
            const int w = 620, h = 470;
            const int x = (W - w) / 2;
            const int y = (H - h) / 2 + (int)((1.0f - guide_anim) * 26.0f);

            // затемнение фона
            for (int py = 0; py < H; py++) {
                for (int px = 0; px < W; px++) {
                    u32 *dst = &pixels[(size_t)py * fb_width + px];
                    *dst = blend_px(*dst, RGBA8_MAXALPHA(0, 0, 0), 130);
                }
            }

            // тень
            for (int i = 3; i >= 1; i--) {
                u32 shadow = blend_px(COLOR_BG, RGBA8_MAXALPHA(0, 0, 0), 60 * i / 3);
                round_rect(pixels, x - i * 5, y - i * 5, w + i * 10, h + i * 10,
                           26 + i * 4, shadow);
            }

            round_rect(pixels, x, y, w, h, 26, RGBA8_MAXALPHA(38, 41, 46));
            round_rect(pixels, x, y, w, 72, 26, RGBA8_MAXALPHA(50, 54, 61));
            rect(pixels, x, y + 52, w, 20, RGBA8_MAXALPHA(50, 54, 61));

            draw_text(face, pixels, x + 32, y + 48, "Guide");

            struct {
                int kind;
                const char *label;
            } rows[] = {
                { 0, "Выбор игры" },
                { 1, "Прокрутка" },
                { 2, "Открыть игру" },
                { 3, "Назад" },
                { 4, "Поиск" },
                { 5, "Этот гайд" },
                { 6, "Выход" },
                { 7, "Прокрутка и нажатие" },
            };

            int row_y = y + 106;

            for (unsigned i = 0; i < sizeof(rows) / sizeof(rows[0]); i++) {
                int ix = x + 40;
                int iy = row_y - 24;

                switch (rows[i].kind) {
                case 0: draw_icon_dpad(pixels, ix, iy, 34); break;
                case 1: draw_icon_stick(pixels, ix, iy, 34); break;
                case 2: draw_icon_letter(face, pixels, ix, iy, 34, "A"); break;
                case 3: draw_icon_letter(face, pixels, ix, iy, 34, "B"); break;
                case 4: draw_icon_letter(face, pixels, ix, iy, 34, "Y"); break;
                case 5: draw_icon_pill(face, pixels, ix, iy + 8, 34, 18, "-"); break;
                case 6: draw_icon_pill(face, pixels, ix, iy + 8, 34, 18, "+"); break;
                case 7: draw_icon_touch(pixels, ix, iy, 34); break;
                }

                set_text_color(210, 215, 225);
                draw_text(face_small, pixels, x + 100, row_y, rows[i].label);
                reset_text_color();

                row_y += 42;
            }

            set_text_color(125, 130, 140);
            draw_text(face_small, pixels, x + 40, y + h - 26, "Тап вне окна - закрыть");
            reset_text_color();
        }

'''
s = s.replace(old, new, 1)

open(p, "w", encoding="utf-8").write(s)
print("patched main.c")
