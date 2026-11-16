import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# ---------- стеклянный буфер ----------
rep("""/* --------------------------- иконки достижений --------------------------- */""",
    r'''#define GLASS_W 620
#define GLASS_H 470

static u32 *glass_buf = NULL;
static int glass_ready = 0;

// Запоминает фон под окном, размывает и тонирует — «матовое стекло».
static void glass_capture(u32 *fb, int x0, int y0, int w, int h)
{
    if (w > GLASS_W) w = GLASS_W;
    if (h > GLASS_H) h = GLASS_H;

    if (!glass_buf) {
        glass_buf = malloc((size_t)GLASS_W * GLASS_H * sizeof(u32));
        if (!glass_buf) return;
    }

    const int block = 7;
    int sw = (w + block - 1) / block;
    int sh = (h + block - 1) / block;

    u32 *small = malloc((size_t)sw * sh * sizeof(u32));

    if (!small) return;

    for (int sy = 0; sy < sh; sy++) {
        for (int sx = 0; sx < sw; sx++) {
            u64 r = 0, g = 0, b = 0, n = 0;

            for (int j = 0; j < block; j++) {
                int py = y0 + sy * block + j;
                if (py < 0 || py >= H) continue;

                for (int i = 0; i < block; i++) {
                    int px = x0 + sx * block + i;
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

    const int div = block * block;

    for (int y = 0; y < h; y++) {
        int iy = y / block;
        int ty = y % block;
        int iy1 = (iy + 1 < sh) ? iy + 1 : iy;

        for (int x = 0; x < w; x++) {
            int ix = x / block;
            int tx = x % block;
            int ix1 = (ix + 1 < sw) ? ix + 1 : ix;

            u32 c00 = small[(size_t)iy * sw + ix];
            u32 c10 = small[(size_t)iy * sw + ix1];
            u32 c01 = small[(size_t)iy1 * sw + ix];
            u32 c11 = small[(size_t)iy1 * sw + ix1];

            int r = 0, g = 0, b = 0;

            for (int k = 0; k < 2; k++) {
                int wy = k ? ty : (block - ty);
                u32 top = k ? c01 : c00;
                u32 bot = k ? c11 : c10;

                for (int m = 0; m < 2; m++) {
                    int wx = m ? tx : (block - tx);
                    u32 c = m ? bot : top;
                    int wgt = wx * wy;

                    r += (c & 0xFF) * wgt;
                    g += ((c >> 8) & 0xFF) * wgt;
                    b += ((c >> 16) & 0xFF) * wgt;
                }
            }

            u32 blurred = RGBA8_MAXALPHA(r / div, g / div, b / div);
            u32 tone = blend_px(blurred, RGBA8_MAXALPHA(16, 18, 22), 130);

            if (y < 74)
                tone = blend_px(tone, RGBA8_MAXALPHA(255, 255, 255), 16);

            glass_buf[(size_t)y * GLASS_W + x] = tone;
        }
    }

    free(small);
    glass_ready = 1;
}

static void glass_draw(u32 *fb, int x0, int y0, int w, int h, int radius)
{
    if (!glass_buf) return;

    if (w > GLASS_W) w = GLASS_W;
    if (h > GLASS_H) h = GLASS_H;

    for (int j = 0; j < h; j++) {
        int py = y0 + j;
        if (py < 0 || py >= H) continue;

        for (int i = 0; i < w; i++) {
            int px = x0 + i;
            if (px < 0 || px >= W) continue;

            int cx = i < radius ? radius : (i >= w - radius ? w - radius - 1 : i);
            int cy = j < radius ? radius : (j >= h - radius ? h - radius - 1 : j);
            int dx = i - cx, dy = j - cy;

            if (dx * dx + dy * dy > radius * radius) continue;

            fb[(size_t)py * fb_width + px] = glass_buf[(size_t)j * GLASS_W + i];
        }
    }

    u32 edge = RGBA8_MAXALPHA(255, 255, 255);

    for (int i = radius; i < w - radius; i++) {
        int px = x0 + i;
        if (px < 0 || px >= W) continue;

        if (y0 >= 0 && y0 < H)
            fb[(size_t)y0 * fb_width + px] =
                blend_px(fb[(size_t)y0 * fb_width + px], edge, 60);
        if (y0 + h - 1 >= 0 && y0 + h - 1 < H)
            fb[(size_t)(y0 + h - 1) * fb_width + px] =
                blend_px(fb[(size_t)(y0 + h - 1) * fb_width + px], edge, 30);
    }

    for (int j = radius; j < h - radius; j++) {
        int py = y0 + j;
        if (py < 0 || py >= H) continue;

        if (x0 >= 0 && x0 < W)
            fb[(size_t)py * fb_width + x0] =
                blend_px(fb[(size_t)py * fb_width + x0], edge, 35);
        if (x0 + w - 1 >= 0 && x0 + w - 1 < W)
            fb[(size_t)py * fb_width + x0 + w - 1] =
                blend_px(fb[(size_t)py * fb_width + x0 + w - 1], edge, 35);
    }
}

/* --------------------------- иконки достижений --------------------------- */''')

# ---------- инерция прокрутки ----------
rep("""    float grid_scroll = 0.0f, grid_target = 0.0f;
    float list_scroll = 0.0f, list_target = 0.0f;""",
    """    float grid_scroll = 0.0f, grid_target = 0.0f;
    float list_scroll = 0.0f, list_target = 0.0f;
    float drag_velocity = 0.0f;""")

rep("""                if (touch_dragged && !guide_open) {
                    if (screen == 0) {""",
    """                if (touch_dragged && !guide_open) {
                    drag_velocity = drag_velocity * 0.6f + (float)dy * 0.4f;

                    if (screen == 0) {""")

rep("""            if (!touch_dragged) {
                touch_tapped = true;""",
    """            if (touch_dragged && !guide_open) {
                float fling = -drag_velocity * 8.0f;

                if (screen == 0) grid_target += fling;
                else list_target += fling;
            }

            drag_velocity = 0.0f;

            if (!touch_dragged) {
                touch_tapped = true;""")

rep("""                grid_scroll += (grid_target - grid_scroll) * 0.35f;""",
    """                grid_scroll += (grid_target - grid_scroll) * 0.13f;""")

rep("""                list_scroll += (list_target - list_scroll) * 0.35f;""",
    """                list_scroll += (list_target - list_scroll) * 0.14f;""")

# ---------- окно Guide на стекле ----------
rep("""            // затемнение фона
            for (int py = 0; py < H; py++) {
                for (int px = 0; px < W; px++) {
                    u32 *dst = &pixels[(size_t)py * fb_width + px];
                    *dst = blend_px(*dst, RGBA8_MAXALPHA(0, 0, 0), 130);
                }
            }
""",
    """            // лёгкое затемнение фона
            for (int py = 0; py < H; py++) {
                for (int px = 0; px < W; px++) {
                    u32 *dst = &pixels[(size_t)py * fb_width + px];
                    *dst = blend_px(*dst, RGBA8_MAXALPHA(0, 0, 0), 70);
                }
            }

            if (!glass_ready)
                glass_capture(pixels, x, y, w, h);
""")

rep("""            round_rect(pixels, x, y, w, h, 26, RGBA8_MAXALPHA(38, 41, 46));
            round_rect(pixels, x, y, w, 72, 26, RGBA8_MAXALPHA(50, 54, 61));
            rect(pixels, x, y + 52, w, 20, RGBA8_MAXALPHA(50, 54, 61));""",
    """            glass_draw(pixels, x, y, w, h, 26);""")

# сброс кэша стекла
rep("""        toggle_anim += ((only_locked ? 1.0f : 0.0f) - toggle_anim) * 0.25f;""",
    """        if (!guide_open && guide_anim < 0.05f)
            glass_ready = 0;

        toggle_anim += ((only_locked ? 1.0f : 0.0f) - toggle_anim) * 0.25f;""")

# освободить буфер
rep("""    framebufferClose(&fb);
    FT_Done_Face(face_small);""",
    """    free(glass_buf);
    framebufferClose(&fb);
    FT_Done_Face(face_small);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
