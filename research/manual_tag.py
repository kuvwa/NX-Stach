import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                clip_left = 120;
                clip_right = 1010;
                draw_text(face_small, pixels, 120, y + 26, achievements[index].name);
                clip_left = 0;
                clip_right = W;"""

new = """                clip_left = 120;
                clip_right = 1010;
                draw_text(face_small, pixels, 120, y + 26, achievements[index].name);

                if (flag_count <= 0) {
                    int nw = measure_text(face_small, achievements[index].name);

                    set_text_color(226, 142, 142);
                    draw_text(face_small, pixels, 120 + nw + 8, y + 26,
                              "(added manually)");
                    reset_text_color();
                }

                clip_left = 0;
                clip_right = W;"""

if old not in s:
    raise SystemExit("row text block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
