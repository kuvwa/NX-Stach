import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                    round_corners(pixels, x, y, CARD_W, CARD_H, 8, COLOR_BG);"""

new = """                    round_corners(pixels, x, y, CARD_W, CARD_H, 8,
                                  i == selected ? COLOR_SELECT : COLOR_BG);"""

if old not in s:
    raise SystemExit("round_corners call not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
