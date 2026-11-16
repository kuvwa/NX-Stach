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


# ---------- library: самый частый цвет ----------
patch("source/library.c", [
("""typedef struct {
    u64 title_id;
    u32 *pixels;
    u32 color;
} CoverSlot;""",
"""typedef struct {
    u64 title_id;
    u32 *pixels;
    u32 color;
    u32 dominant;
} CoverSlot;"""),

("""    free(covers[slot].pixels);
    covers[slot].pixels = pixels;
    covers[slot].title_id = title_id;
    covers[slot].color = RGBA8_MAXALPHA(cr, cg, cb);""",
"""    // самый частый цвет (грубая гистограмма 4 бита на канал)
    static u16 hist[4096];
    for (int i = 0; i < 4096; i++) hist[i] = 0;

    for (int y = 0; y < LIB_COVER_H; y += 3) {
        for (int x = 0; x < LIB_COVER_W; x += 3) {
            u32 c = pixels[(size_t)y * LIB_COVER_W + x];
            int idx = (((c >> 4) & 0xF) << 8) |
                      (((c >> 12) & 0xF) << 4) |
                      ((c >> 20) & 0xF);
            if (hist[idx] < 60000) hist[idx]++;
        }
    }

    int best = 0;
    for (int i = 1; i < 4096; i++)
        if (hist[i] > hist[best]) best = i;

    int dr = ((best >> 8) & 0xF) * 17 + 8;
    int dg = ((best >> 4) & 0xF) * 17 + 8;
    int db = (best & 0xF) * 17 + 8;

    free(covers[slot].pixels);
    covers[slot].pixels = pixels;
    covers[slot].title_id = title_id;
    covers[slot].color = RGBA8_MAXALPHA(cr, cg, cb);
    covers[slot].dominant = RGBA8_MAXALPHA(dr, dg, db);"""),

("""u32 library_cover_color(u64 title_id)""",
"""u32 library_dominant_color(u64 title_id)
{
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++)
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].dominant;

    return 0;
}

u32 library_cover_color(u64 title_id)"""),
])

patch("source/library.h", [
("""// Средний цвет обложки (для свечения).
u32 library_cover_color(u64 title_id);""",
"""// Средний цвет обложки (для свечения).
u32 library_cover_color(u64 title_id);

// Самый частый цвет обложки (для фона шапки).
u32 library_dominant_color(u64 title_id);"""),
])

# ---------- main ----------
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# убрать старый (артефактный) фон
start = s.find("// Сильно размытая и затемнённая обложка — фон шапки.")
end = s.find("static void draw_header_bg(u32 *fb)")

if start < 0 or end < 0:
    raise SystemExit("header bg block not found")

new_bg = r'''// Фон шапки: самый частый цвет обложки, затемнённый и растянутый в градиент.
static void build_header_bg(u64 title_id)
{
    header_bg_ready = 0;

    if (!header_bg) {
        header_bg = malloc((size_t)W * HEADER_BG_H * sizeof(u32));
        if (!header_bg) return;
    }

    u32 dom = library_dominant_color(title_id);

    if (!dom)
        dom = library_cover_color(title_id);

    if (!dom) {
        for (int y = 0; y < HEADER_BG_H; y++)
            for (int x = 0; x < W; x++)
                header_bg[(size_t)y * W + x] = COLOR_BG;

        header_bg_ready = 1;
        return;
    }

    // приглушаем и затемняем цвет
    u32 base = blend_px(dom, RGBA8_MAXALPHA(12, 13, 17), 105);

    for (int y = 0; y < HEADER_BG_H; y++) {
        float t = 1.0f - (float)y / (float)HEADER_BG_H;
        t = t * t;

        int alpha = (int)(200.0f * t);

        u32 color = blend_px(COLOR_BG, base, alpha);

        for (int x = 0; x < W; x++)
            header_bg[(size_t)y * W + x] = color;
    }

    header_bg_ready = 1;
}

'''

s = s[:start] + new_bg + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("header bg replaced")

# ---------- пульс медленнее, глоу темнее ----------
s = open(p, encoding="utf-8").read()

s = s.replace("pulse = 0.5f + 0.5f * sinf((float)tick * 0.19f);",
              "pulse = 0.5f + 0.5f * sinf((float)tick * 0.055f);", 1)

s = s.replace("""                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 30 + grow, glow,
                              (int)(48 + 42 * pulse));""",
              """                    u32 glow_dark = blend_px(glow, RGBA8_MAXALPHA(0, 0, 0), 90);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 30 + grow, glow_dark,
                              (int)(30 + 30 * pulse));""", 1)

# ---------- бегущая строка медленнее ----------
s = s.replace("""                    int shift = (name_w > CARD_W - 20)
                        ? (int)((shine_counter / 2) % (u32)cycle) : 0;""",
              """                    int shift = (name_w > CARD_W - 20)
                        ? (int)((tick / 3) % (u32)cycle) : 0;""", 1)

# ---------- больше воздуха под поиском ----------
s = s.replace("#define GRID_Y0 160", "#define GRID_Y0 178", 1)
s = s.replace("#define HEADER_H 140", "#define HEADER_H 150", 1)

open(p, "w", encoding="utf-8").write(s)
print("main patched")
