import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


# Y-подсказка в строке поиска — по центру новой высоты
rep("""            set_text_color(110, 115, 125);
            draw_text(face_small, pixels, W - 90, 116, "Y");
            reset_text_color();""",
    """            set_text_color(110, 115, 125);
            draw_text(face_small, pixels, W - 90, 136, "Y");
            reset_text_color();

            // переключатель языка
            {
                const int bw = 56, bh = 34;
                const int rx = W - 55 - bw * 2 - 8;
                const int ry = 36;

                round_rect(pixels, rx, ry, bw, bh, 10,
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
                reset_text_color();
            }""")

# тап по переключателю
rep("""                if (tap_y >= 82 && tap_y <= 134) {""",
    """                if (tap_y >= 36 && tap_y <= 70 && tap_x >= W - 175) {
                    int rx = W - 55 - 56 * 2 - 8;

                    lang = (tap_x < rx + 56 + 4) ? 0 : 1;
                    lang_save();
                    consumed = true;
                } else if (tap_y >= 104 && tap_y <= 156) {""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
