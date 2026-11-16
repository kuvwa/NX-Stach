import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """            int title_x = 200;

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

new = """            int title_x = 200;

            clip_left = title_x;
            clip_right = W - 40;
            draw_text(face, pixels, title_x, 78, game->name);

            if (achievement_count > 0 && flag_count <= 0) {
                const char *tag = L("(added manually)", "(добавлено вручную)");
                int name_w = measure_text(face, game->name);
                int tx = title_x + name_w + 14;

                set_text_color(226, 142, 142);
                draw_text(face_small, pixels, tx, 74, tag);
                reset_text_color();
            }

            clip_left = 0;
            clip_right = W;"""

if old not in s:
    raise SystemExit("title block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
