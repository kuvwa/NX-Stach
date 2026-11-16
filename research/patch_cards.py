import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# ---------- параметры сетки: квадраты, 5 в ряд ----------
rep("""// сетка постеров как в Steam
#define CARD_W 162
#define CARD_H 243
#define GRID_COLS 7
#define GRID_GAP_X 10
#define GRID_GAP_Y 10
#define GRID_STEP_X (CARD_W + GRID_GAP_X)
#define GRID_STEP_Y (CARD_H + GRID_GAP_Y)
#define GRID_Y0 150
#define HEADER_H 140""",
    """// сетка карточек
#define CARD_W 190
#define CARD_H 190
#define GRID_COLS 5
#define GRID_GAP_X 55
#define GRID_GAP_Y 25
#define GRID_STEP_X (CARD_W + GRID_GAP_X)
#define GRID_STEP_Y (CARD_H + GRID_GAP_Y)
#define GRID_Y0 160
#define HEADER_H 140""")

# ---------- helpers: стеклянная полоса и свечение ----------
rep("""/* --------------------------- ачивки: иконки --------------------------- */""",
    r'''static u32 blend_px(u32 bg, u32 fg, int a)
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

// Матовое стекло поверх прямоугольного участка кадра.
static void glass_region(u32 *fb, int x, int y, int w, int h,
                         int block, int alpha, int radius)
{
    if (w <= 0 || h <= 0) return;

    int sw = (w + block - 1) / block;
    int sh = (h + block - 1) / block;

    u32 *small = malloc((size_t)sw * sh * sizeof(u32));

    if (!small) return;

    for (int sy = 0; sy < sh; sy++) {
        for (int sx = 0; sx < sw; sx++) {
            int r = 0, g = 0, b = 0, n = 0;

            for (int j = 0; j < block; j++) {
                int py = y + sy * block + j;
                if (py < 0 || py >= H) continue;

                for (int i = 0; i < block; i++) {
                    int px = x + sx * block + i;
                    if (px < 0 || px >= W) continue;

                    u32 c = fb[(size_t)py * fb_width + px];
                    r += c & 0xFF;
                    g += (c >> 8) & 0xFF;
                    b += (c >> 16) & 0xFF;
                    n++;
                }
            }

            if (!n) n = 1;
            small[(size_t)sy * sw + sx] = RGBA8_MAXALPHA(r / n, g / n, b / n);
        }
    }

    for (int j = 0; j < h; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;

        int iy = j / block, ty = j % block;
        int iy1 = (iy + 1 < sh) ? iy + 1 : iy;

        for (int i = 0; i < w; i++) {
            int px = x + i;
            if (px < 0 || px >= W) continue;

            if (radius > 0 && j >= h - radius) {
                int dy = j - (h - radius);
                if (dy * dy > radius * radius) continue;
            }

            int ix = i / block, tx = i % block;
            int ix1 = (ix + 1 < sw) ? ix + 1 : ix;

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

            fb[(size_t)py * fb_width + px] =
                blend_px(blurred, RGBA8_MAXALPHA(12, 13, 17), alpha);
        }
    }

    free(small);
}

// Очень мягкое свечение вокруг карточки (несколько слоёв + затухание).
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

            float t = 1.0f - d / (float)spread;
            t = t * t * (3.0f - 2.0f * t);

            int a = (int)((float)strength * t);
            if (a <= 0) continue;

            u32 *dst = &fb[(size_t)py * fb_width + px];
            *dst = blend_px(*dst, color, a);
        }
    }
}

/* --------------------------- ачивки: иконки --------------------------- */''')

# ---------- стрелки как левый стик ----------
rep("""                    if (kDown & HidNpadButton_Down)
                        grid_target += GRID_STEP_Y;
                    if (kDown & HidNpadButton_Up)
                        grid_target -= GRID_STEP_Y;""",
    """                    if (kDown & HidNpadButton_Down) {
                        int next = selected + GRID_COLS;
                        if (next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }
                    if (kDown & HidNpadButton_Up) {
                        int next = selected - GRID_COLS;
                        if (next >= 0) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }""")

rep("""                    if (sx)
                        selected = (selected + sx + view_count) % view_count;
                    if (sy) {
                        int next = selected - sy * GRID_COLS;

                        if (next >= 0 && next < view_count)
                            selected = next;
                    }""",
    """                    if (sx) {
                        selected = (selected + sx + view_count) % view_count;
                        follow_selection = 1;
                    }
                    if (sy) {
                        int next = selected - sy * GRID_COLS;

                        if (next >= 0 && next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }""")

rep("""                    if (kDown & HidNpadButton_Right)
                        selected = (selected + 1) % view_count;
                    if (kDown & HidNpadButton_Left)
                        selected = (selected + view_count - 1) % view_count;""",
    """                    if (kDown & HidNpadButton_Right) {
                        selected = (selected + 1) % view_count;
                        follow_selection = 1;
                    }
                    if (kDown & HidNpadButton_Left) {
                        selected = (selected + view_count - 1) % view_count;
                        follow_selection = 1;
                    }""")

rep("""                    if (screen == 0 && view_count > 0) {
                        int next = selected + step * GRID_COLS;

                        if (next >= 0 && next < view_count)
                            selected = next;
                    }""",
    """                    if (screen == 0 && view_count > 0) {
                        int next = selected + step * GRID_COLS;

                        if (next >= 0 && next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }""")

# флаг в состоянии
rep("""    int only_locked = 0;""",
    """    int only_locked = 0;
    int follow_selection = 0;
    float hover_anim = 0.0f;""")

# подтягиваем скролл к выбранной карточке
rep("""            if (grid_target < 0) grid_target = 0;""",
    """            if (follow_selection) {
                int row = selected / GRID_COLS;
                float top = (float)row * GRID_STEP_Y;
                float bottom = top + GRID_STEP_Y;

                if (top < grid_target) grid_target = top;
                if (bottom > grid_target + visible)
                    grid_target = bottom - visible;

                follow_selection = 0;
            }

            if (grid_target < 0) grid_target = 0;""")

# ---------- отрисовка карточек ----------
old_start = s.find("            int grid_x0 = (W - (GRID_COLS * GRID_STEP_X - GRID_GAP_X)) / 2;")
old_end = s.find("            rect(pixels, 0, 0, W, HEADER_H, COLOR_BG);")

if old_start < 0 or old_end < 0:
    raise SystemExit("grid block not found")

new_grid = r'''            int grid_x0 = (W - (GRID_COLS * GRID_STEP_X - GRID_GAP_X)) / 2;

            for (int i = 0; i < view_count; i++) {
                int col = i % GRID_COLS;
                int row = i / GRID_COLS;

                int x = grid_x0 + col * GRID_STEP_X;
                int y = GRID_Y0 + (int)((float)row * GRID_STEP_Y - grid_scroll);

                if (y + CARD_H < HEADER_H) continue;
                if (y > H) continue;

                int game_index = view[i];
                const u32 *cover = library_cover(games[game_index].title_id);

                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);
                    int grow = (int)(hover_anim * 6.0f);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 34 + grow, glow, 78);
                }

                if (cover)
                    draw_cover(pixels, x, y, CARD_W, cover,
                               i == selected ? COLOR_SELECT : COLOR_BG, 8);
                else
                    round_rect(pixels, x, y, CARD_W, CARD_H, 8, COLOR_PANEL);

                if (i == selected) {
                    // стеклянная плашка с названием
                    int strip_h = 44;
                    int strip_y = y + CARD_H - strip_h;

                    glass_region(pixels, x, strip_y, CARD_W, strip_h,
                                 5, 130, 0);

                    round_corners(pixels, x, y, CARD_W, CARD_H, 8, COLOR_BG);

                    clip_left = x + 8;
                    clip_right = x + CARD_W - 8;
                    clip_top = strip_y;
                    clip_bottom = y + CARD_H;

                    const char *name = games[game_index].name;
                    int name_w = measure_text(face_small, name);
                    int cycle = name_w + 40;
                    if (cycle < 1) cycle = 1;

                    int shift = (name_w > CARD_W - 20)
                        ? (int)((shine_counter / 2) % (u32)cycle) : 0;

                    set_text_color(248, 250, 253);
                    draw_text(face_small, pixels, x + 10 - shift,
                              strip_y + 30, name);
                    if (name_w > CARD_W - 20)
                        draw_text(face_small, pixels, x + 10 - shift + cycle,
                                  strip_y + 30, name);
                    reset_text_color();

                    clip_left = 0;
                    clip_right = W;
                    clip_top = 0;
                    clip_bottom = H;
                }
            }

'''

s = s[:old_start] + new_grid + s[old_end:]

# hover-анимация
rep("""        shine_counter = (u32)(shine_counter + 30);""",
    """        hover_anim += (1.0f - hover_anim) * 0.22f;
        shine_counter = (u32)(shine_counter + 30);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
