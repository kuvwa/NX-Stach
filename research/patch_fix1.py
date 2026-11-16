import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

s = s.replace("#include <time.h>", "#include <time.h>\n#include <math.h>", 1)

s = s.replace("""                if (stick.y > 16000 || stick.y < -16000 || 
                    stick.y < -16000) {""",
              """                if (stick.y > 16000 || stick.y < -16000) {""", 1)

old = """static void draw_toggle(u32 *fb, int x, int y, bool on)
{
    round_rect(fb, x, y, 62, 32, 16, on ? COLOR_ACCENT : COLOR_TRACK);

    int knob = 24;
    int kx = on ? x + 62 - knob - 4 : x + 4;

    round_rect(fb, kx, y + 4, knob, knob, knob / 2, RGBA8_MAXALPHA(245, 248, 252));
}

"""
s = s.replace(old, "", 1)

open(p, "w", encoding="utf-8").write(s)
print("ok")
