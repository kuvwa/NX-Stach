import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """        // кнопка Guide
        {
            const int bx = 55, by = H - 85, size = 52;

            round_rect(pixels, bx, by, size, size, size / 2, COLOR_PANEL);

            int glyph = measure_text(face, "!");
            set_text_color(235, 240, 250);
            draw_text(face, pixels, bx + size / 2 - glyph / 2, by + size / 2 + 10, "!");
            reset_text_color();
        }
"""

new = """        // кнопка Guide
        {
            const int bx = 55, by = H - 85, size = 52;

            if (guide_anim > 0.02f)
                draw_glow(pixels, bx - 8, by - 8, size + 16, (size + 16) / 2, 18,
                          COLOR_ACCENT, (int)(60 * guide_anim));

            for (int i = 3; i >= 1; i--) {
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
                       (size - 4) / 2, RGBA8_MAXALPHA(46, 49, 55));

            int glyph = measure_text(face, "!");
            set_text_color(235, 240, 250);
            draw_text(face, pixels, bx + size / 2 - glyph / 2,
                      by + size / 2 + 10, "!");
            reset_text_color();
        }
"""

if old not in s:
    raise SystemExit("guide button block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
