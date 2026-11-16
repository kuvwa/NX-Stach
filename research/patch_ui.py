import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

pairs = [
("""                touch.start_x = touch.start_y = 0;
                touch.start_x = touch_x;""",
 """                touch.start_x = touch_x;"""),

("""            touch.touching = false;
            tap = !touch.dragged;""",
 """            touch.touching = false;
            tap = !touch.dragged;
            touch.dragged = false;"""),

("""            int bar_w = 1130;""", """            int bar_w = 960;"""),

("""                        draw_text(face_small, pixels, 1190 - date_width, y + 40, date);""",
 """                        draw_text(face_small, pixels, 1165 - date_width, y + 40, date);"""),

("""static void draw_button(FT_Face face, u32 *fb, int x, int y, int size,
                        const char *label)
{
    round_rect(fb, x, y, size, size, size / 2, COLOR_PANEL);
    int width = measure_text(face, label);
    draw_text(face, fb, x + (size - width) / 2, y + size / 2 + size / 5, label);
}

""", ""),

("""    int frame = 0;
    u32 shine_counter = 0;""", """    u32 shine_counter = 0;"""),

("""        frame++;
        shine_counter""", """        shine_counter"""),
]

for old, new in pairs:
    if old not in s:
        print("NOT FOUND:", old.splitlines()[0][:70])
        continue
    s = s.replace(old, new, 1)

open(p, "w", encoding="utf-8").write(s)
print("patched")
