import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """            if (view_count > 0 && !games[view[selected]].steam_appid[0]) {
                const char *hint = "Добавить достижения из Steam";
                int text_w = measure_text(face_small, hint);
                int pill_w = text_w + 96;
                int pill_x = (W - pill_w) / 2;
                int pill_y = H - 84;

                round_rect(pixels, pill_x, pill_y, pill_w, 50, 14,
                           RGBA8_MAXALPHA(38, 41, 47));
                round_rect(pixels, pill_x, pill_y, pill_w, 50, 14,
                           blend_px(COLOR_BG, COLOR_ACCENT, 90));

                round_rect(pixels, pill_x + 18, pill_y + 11, 28, 28, 14,
                           RGBA8_MAXALPHA(74, 79, 88));

                set_text_color(238, 242, 250);
                draw_text(face_small, pixels, pill_x + 25, pill_y + 32, "X");
                draw_text(face_small, pixels, pill_x + 60, pill_y + 32, hint);
                reset_text_color();
            }

"""

if old not in s:
    raise SystemExit("hint block not found")

s = s.replace(old, "", 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
