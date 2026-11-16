import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

start = s.find("static void draw_cover(u32 *fb, int x, int y, int size, const u32 *cover,")
if start < 0:
    raise SystemExit("draw_cover not found")

end = s.find("static void draw_scrollbar(", start)
if end < 0:
    raise SystemExit("next function not found")

new_fn = '''static void draw_cover(u32 *fb, int x, int y, int size, const u32 *cover,
                       u32 corner_color, int radius)
{
    (void)corner_color;

    for (int j = 0; j < size; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;

        int dy = 0;

        if (j < radius) dy = radius - j;
        else if (j >= size - radius) dy = j - (size - radius - 1);

        for (int i = 0; i < size; i++) {
            int px = x + i;
            if (px < 0 || px >= W) continue;

            if (radius > 0) {
                int dx = 0;

                if (i < radius) dx = radius - i;
                else if (i >= size - radius) dx = i - (size - radius - 1);

                // вне скругления — не рисуем, остаётся настоящий фон
                if (dx * dx + dy * dy > radius * radius)
                    continue;
            }

            int sy = j * LIB_COVER_H / size;
            int sx = i * LIB_COVER_W / size;

            if (sy >= LIB_COVER_H) sy = LIB_COVER_H - 1;
            if (sx >= LIB_COVER_W) sx = LIB_COVER_W - 1;

            fb[(size_t)py * fb_width + px] =
                cover[(size_t)sy * LIB_COVER_W + sx];
        }
    }
}

'''

s = s[:start] + new_fn + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
