import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:150])
    s = s.replace(old, new, 1)


rep("""                if (flag_count <= 0) {
                    int nw = measure_text(face_small, achievements[index].name);

                    set_text_color(226, 142, 142);
                    draw_text(face_small, pixels, 120 + nw + 8, y + 26,
                              L("(added manually)", "(добавлено вручную)"));
                    reset_text_color();
                }

""", "")

old_title = """            clip_left = 200;
            clip_right = W - 40;
            draw_text(face, pixels, 200, 78, game->name);
            clip_left = 0;
            clip_right = W;"""

new_title = """            int title_x = 200;

            if (achievement_count > 0 && flag_count <= 0) {
                const char *tag = L("(added manually)", "(добавлено вручную)");

                set_text_color(226, 142, 142);
                draw_text(face_small, pixels, title_x, 73, tag);
                reset_text_color();

                title_x += measure_text(face_small, tag) + 12;
            }

            clip_left = title_x;
            clip_right = W - 40;
            draw_text(face, pixels, title_x, 78, game->name);
            clip_left = 0;
            clip_right = W;"""

if old_title not in s:
    raise SystemExit("title block not found")

s = s.replace(old_title, new_title, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
