import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                round_rect(pixels, rx, ry, bw, bh, 10,
                           lang == 0 ? COLOR_ACCENT : COLOR_PANEL);
                set_text_color(lang == 0 ? 18 : 190,
                               lang == 0 ? 30 : 195,
                               lang == 0 ? 42 : 205);
                draw_text(face_small, pixels, rx + 17, ry + 24, "EN");
                reset_text_color();

                round_rect(pixels, rx + bw + 8, ry, bw, bh, 10,
                           lang == 1 ? COLOR_ACCENT : COLOR_PANEL);
                set_text_color(lang == 1 ? 18 : 190,
                               lang == 1 ? 30 : 195,
                               lang == 1 ? 42 : 205);
                draw_text(face_small, pixels, rx + bw + 25, ry + 24, "RU");
                reset_text_color();"""

new = """                round_rect(pixels, rx, ry, bw, bh, 10,
                           lang == 0 ? COLOR_ACCENT : COLOR_PANEL);
                set_text_color(lang == 0 ? 18 : 190,
                               lang == 0 ? 30 : 195,
                               lang == 0 ? 42 : 205);
                draw_text(face_small, pixels,
                          rx + (bw - measure_text(face_small, "EN")) / 2,
                          ry + 24, "EN");
                reset_text_color();

                round_rect(pixels, rx + bw + 8, ry, bw, bh, 10,
                           lang == 1 ? COLOR_ACCENT : COLOR_PANEL);
                set_text_color(lang == 1 ? 18 : 190,
                               lang == 1 ? 30 : 195,
                               lang == 1 ? 42 : 205);
                draw_text(face_small, pixels,
                          rx + bw + 8 + (bw - measure_text(face_small, "RU")) / 2,
                          ry + 24, "RU");
                reset_text_color();"""

if old not in s:
    raise SystemExit("lang toggle block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
