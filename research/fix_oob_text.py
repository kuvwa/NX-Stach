import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """            if (px < clip_left || px >= clip_right) continue;
            if (py < clip_top || py >= clip_bottom) continue;"""

new = """            if (px < clip_left || px >= clip_right) continue;
            if (py < clip_top || py >= clip_bottom) continue;

            // жёсткая страховка: никогда не писать за пределы кадра
            if (px < 0 || px >= W || py < 0 || py >= H) continue;"""

if old not in s:
    raise SystemExit("clip block not found")

s = s.replace(old, new, 1)

# и у остальных рисовалок — обрезка в кадре уже есть, дублируем проверку для текста
open(p, "w", encoding="utf-8").write(s)
print("ok")
