import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s:\n%s" % (path, old[:200]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


# ---------------- library: цвет обложки ----------------
patch("source/library.c", [
("""typedef struct {
    u64 title_id;
    u32 *pixels;
} CoverSlot;

static CoverSlot covers[CACHE_SLOTS];""",
"""typedef struct {
    u64 title_id;
    u32 *pixels;
    u32 color;
} CoverSlot;

static CoverSlot covers[CACHE_SLOTS];
static u32 last_color = RGBA8_MAXALPHA(120, 200, 255);"""),

("""    free(covers[slot].pixels);
    covers[slot].pixels = pixels;
    covers[slot].title_id = title_id;

    return pixels;""",
"""    // средний цвет обложки — для подсветки
    u64 sr = 0, sg = 0, sb = 0, n = 0;

    for (int y = 0; y < LIB_COVER_H; y += 4) {
        for (int x = 0; x < LIB_COVER_W; x += 4) {
            u32 c = pixels[(size_t)y * LIB_COVER_W + x];
            sr += c & 0xFF;
            sg += (c >> 8) & 0xFF;
            sb += (c >> 16) & 0xFF;
            n++;
        }
    }

    int cr = 120, cg = 200, cb = 255;

    if (n > 0) {
        cr = (int)(sr / n);
        cg = (int)(sg / n);
        cb = (int)(sb / n);

        int mx = cr > cg ? (cr > cb ? cr : cb) : (cg > cb ? cg : cb);
        int k = mx > 0 ? 235 * 100 / mx : 100;
        if (k > 260) k = 260;

        cr = cr * k / 100;
        cg = cg * k / 100;
        cb = cb * k / 100;

        if (cr > 235) cr = 235;
        if (cg > 235) cg = 235;
        if (cb > 235) cb = 235;
    }

    free(covers[slot].pixels);
    covers[slot].pixels = pixels;
    covers[slot].title_id = title_id;
    covers[slot].color = RGBA8_MAXALPHA(cr, cg, cb);

    last_color = covers[slot].color;

    return pixels;"""),
])

# ---------------- library.h ----------------
patch("source/library.h", [
("""// Обложка игры в формате кадра (RGBA8_MAXALPHA), LIB_COVER_W x LIB_COVER_H.
// NULL, если обложку получить не удалось.
const u32 *library_cover(u64 title_id);""",
"""// Обложка игры в формате кадра (RGBA8_MAXALPHA), LIB_COVER_W x LIB_COVER_H.
// NULL, если обложку получить не удалось.
const u32 *library_cover(u64 title_id);

// Средний цвет обложки (для свечения).
u32 library_cover_color(u64 title_id);"""),
])

patch("source/library.c", [
("""bool library_online(void) { return ns_ready; }""",
"""bool library_online(void) { return ns_ready; }

u32 library_cover_color(u64 title_id)
{
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++)
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].color;

    return last_color;
}"""),
])

# ---------------- main: стики, свечение, выравнивание, кнопка ----------------
patch("source/main.c", [
# правый стик — прокрутка, левый — выбор
("""                int sx = 0, sy = 0;

                stick_update(&stick_left, padGetStickPos(&pad, 0), &sx, &sy);

                if (sx && view_count > 0)
                    selected = (selected + sx + view_count) % view_count;
                if (sy)
                    grid_target -= (float)sy * (float)GRID_STEP_Y;

                stick_update(&stick_right, padGetStickPos(&pad, 1), &sx, &sy);

                if (sy)
                    grid_target -= (float)sy * (float)GRID_STEP_Y;""",
"""                int sx = 0, sy = 0;

                stick_update(&stick_left, padGetStickPos(&pad, 0), &sx, &sy);

                if (view_count > 0) {
                    if (sx)
                        selected = (selected + sx + view_count) % view_count;
                    if (sy) {
                        int next = selected - sy * GRID_COLS;

                        if (next >= 0 && next < view_count)
                            selected = next;
                    }
                }

                stick_update(&stick_right, padGetStickPos(&pad, 1), &sx, &sy);

                if (sy)
                    grid_target -= (float)sy * (float)GRID_STEP_Y;"""),

# свечение цветом обложки
("""                if (i == selected) {
                    draw_glow(pixels, x, y, COVER_SIZE, 18, 26, COLOR_ACCENT, 70);

                    if (cover)
                        round_rect(pixels, x - 5, y - 5, COVER_SIZE + 10,
                                   COVER_SIZE + 10, 22, COLOR_ACCENT);
                }""",
"""                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);

                    draw_glow(pixels, x, y, COVER_SIZE, 18, 30, glow, 80);

                    if (cover)
                        round_rect(pixels, x - 4, y - 4, COVER_SIZE + 8,
                                   COVER_SIZE + 8, 21, glow);
                }"""),

# шапка достижений — прижать влево
("""            const u32 *cover = library_cover(game->title_id);
            if (cover)
                draw_cover(pixels, 125, 20, 120, cover, COLOR_BG, 16);
            else
                round_rect(pixels, 125, 20, 120, 120, 16, COLOR_PANEL);

            clip_left = 270;
            clip_right = W - 40;
            draw_text(face, pixels, 270, 60, game->name);""",
"""            const u32 *cover = library_cover(game->title_id);
            if (cover)
                draw_cover(pixels, 55, 20, 120, cover, COLOR_BG, 16);
            else
                round_rect(pixels, 55, 20, 120, 120, 16, COLOR_PANEL);

            clip_left = 200;
            clip_right = W - 40;
            draw_text(face, pixels, 200, 60, game->name);"""),

("""            set_text_color(160, 165, 175);
            draw_text(face_small, pixels, 270, 92, stats);
            reset_text_color();""",
"""            set_text_color(160, 165, 175);
            draw_text(face_small, pixels, 200, 92, stats);
            reset_text_color();"""),

# кнопка Guide без чёрных колец
("""            for (int i = 3; i >= 1; i--) {
                u32 shadow = blend_px(COLOR_BG, RGBA8_MAXALPHA(0, 0, 0), 45);
                round_rect(pixels, bx - i * 3, by - i * 3,
                           size + i * 6, size + i * 6,
                           size / 2 + i * 3, shadow);
            }

            u32 ring = guide_anim > 0.5f
                ? COLOR_ACCENT
                : blend_px(COLOR_BG, COLOR_ACCENT, 120);

            round_rect(pixels, bx, by, size, size, size / 2, ring);
            round_rect(pixels, bx + 2, by + 2, size - 4, size - 4,
                       (size - 4) / 2, RGBA8_MAXALPHA(46, 49, 55));""",
"""            u32 ring = blend_px(COLOR_BG, COLOR_ACCENT,
                                guide_anim > 0.5f ? 200 : 110);

            round_rect(pixels, bx, by, size, size, size / 2, ring);
            round_rect(pixels, bx + 2, by + 2, size - 4, size - 4,
                       (size - 4) / 2, blend_px(COLOR_BG, RGBA8_MAXALPHA(70, 74, 82), 200));"""),

# тень гайда — мягче
("""            // тень
            for (int i = 3; i >= 1; i--) {
                u32 shadow = blend_px(COLOR_BG, RGBA8_MAXALPHA(0, 0, 0), 60 * i / 3);
                round_rect(pixels, x - i * 5, y - i * 5, w + i * 10, h + i * 10,
                           26 + i * 4, shadow);
            }""",
"""            // мягкая тень
            for (int i = 2; i >= 1; i--) {
                u32 shadow = blend_px(COLOR_BG, RGBA8_MAXALPHA(0, 0, 0), 40 * i / 2);
                round_rect(pixels, x - i * 6, y - i * 6, w + i * 12, h + i * 12,
                           26 + i * 5, shadow);
            }"""),
])

# ---------------- иконки кнопок в стиле Joy-Con ----------------
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old_start = s.find("static void draw_icon_letter(")
old_end = s.find("/* --------------------------- иконки достижений --------------------------- */")

if old_start < 0 or old_end < 0 or old_end < old_start:
    raise SystemExit("icon block not found")

new_block = r'''static void draw_icon_letter(FT_Face face, u32 *fb, int x, int y, int size,
                             const char *letter)
{
    round_rect(fb, x, y, size, size, size / 2, RGBA8_MAXALPHA(52, 56, 63));
    round_rect(fb, x + 1, y + 1, size - 2, size - 2, (size - 2) / 2,
               RGBA8_MAXALPHA(34, 37, 42));

    int w = measure_text(face, letter);
    draw_text(face, fb, x + (size - w) / 2, y + size / 2 + 7, letter);
}

static void draw_icon_pill(FT_Face face, u32 *fb, int x, int y, int w, int h,
                           const char *letter)
{
    round_rect(fb, x, y, w, h, 5, RGBA8_MAXALPHA(40, 43, 49));

    int tw = measure_text(face, letter);
    draw_text(face, fb, x + (w - tw) / 2, y + h / 2 + 7, letter);
}

// Левый Joy-Con: четыре отдельные кнопки-стрелки.
static void draw_icon_dpad(u32 *fb, int x, int y, int size)
{
    int b = size / 4;
    int gap = size / 4;
    int cx = x + size / 2 - b / 2;
    int cy = y + size / 2 - b / 2;

    u32 c = RGBA8_MAXALPHA(48, 52, 58);

    round_rect(fb, cx, y, b, b, b / 2, c);
    round_rect(fb, cx, y + size - b, b, b, b / 2, c);
    round_rect(fb, x, cy, b, b, b / 2, c);
    round_rect(fb, x + size - b, cy, b, b, b / 2, c);

    u32 arrow = RGBA8_MAXALPHA(190, 196, 206);

    // маленькие треугольники-стрелки
    for (int i = 0; i < b / 3; i++) {
        rect(fb, cx + b / 2 - i, y + b / 2 - i / 2, i * 2 + 1, 1, arrow);
        rect(fb, cx + b / 2 - i, y + size - b / 2 + i / 2 - 2, i * 2 + 1, 1, arrow);
        rect(fb, x + b / 2 - i / 2, cy + b / 2 - i + 1, 1, i * 2 + 1, arrow);
        rect(fb, x + size - b / 2 + i / 2 - 2, cy + b / 2 - i + 1, 1, i * 2 + 1, arrow);
    }

    (void)gap;
}

static void draw_icon_stick(u32 *fb, int x, int y, int size)
{
    round_rect(fb, x, y, size, size, size / 2, RGBA8_MAXALPHA(44, 47, 53));
    round_rect(fb, x + 3, y + 3, size - 6, size - 6, (size - 6) / 2,
               RGBA8_MAXALPHA(62, 66, 73));
    round_rect(fb, x + size / 3, y + size / 3, size / 3, size / 3, size / 6,
               RGBA8_MAXALPHA(120, 126, 136));
}

static void draw_icon_touch(u32 *fb, int x, int y, int size)
{
    round_rect(fb, x + size / 3, y + size / 8, size / 3, size / 2, size / 6,
               RGBA8_MAXALPHA(215, 220, 230));
    round_rect(fb, x + size / 6, y + size * 2 / 3, size * 2 / 3, 4, 2,
               RGBA8_MAXALPHA(120, 200, 255));
    round_rect(fb, x + size / 3, y + size * 5 / 6, size / 3, 4, 2,
               RGBA8_MAXALPHA(120, 200, 255));
}

'''

s = s[:old_start] + new_block + s[old_end:]
open(p, "w", encoding="utf-8").write(s)
print("icons replaced")
