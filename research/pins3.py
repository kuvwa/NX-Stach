import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                if (i == selected) {
                    // стеклянная плашка с названием
                    int strip_h = 44;"""

new = """                if (is_pinned(games[game_index].title_id)) {
                    round_rect(pixels, x + 8, y + 8, 20, 20, 10, COLOR_ACCENT);
                    round_rect(pixels, x + 14, y + 14, 8, 8, 4,
                               RGBA8_MAXALPHA(24, 26, 30));
                }

                if (i == selected) {
                    // стеклянная плашка с названием
                    int strip_h = 44;"""

if old not in s:
    raise SystemExit("tile anchor not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
