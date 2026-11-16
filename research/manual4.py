import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = "            draw_toggle(pixels, 1138, 277, toggle_anim);"

new = """            draw_toggle(pixels, 1138, 277, toggle_anim);

            if (achievement_count > 0 && flag_count <= 0) {
                set_text_color(118, 124, 136);
                draw_text(face_small, pixels, 55, 712,
                          "\\u0422\\u0430\\u043f \\u043f\\u043e \\u0434\\u043e\\u0441\\u0442\\u0438\\u0436\\u0435\\u043d\\u0438\\u044e \\u2014 \\u043e\\u0442\\u043c\\u0435\\u0442\\u0438\\u0442\\u044c \\u0432\\u0440\\u0443\\u0447\\u043d\\u0443\\u044e");
                reset_text_color();
            }"""

if old not in s:
    raise SystemExit("toggle call not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
