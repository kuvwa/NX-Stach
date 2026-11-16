import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

start = s.find("static void draw_progress(Framebuffer *fb")
if start < 0:
    raise SystemExit("draw_progress not found")

end = s.find("/* ------------------------------- стики ------------------------------- */", start)
if end < 0:
    raise SystemExit("next section not found")

s = s[:start] + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
