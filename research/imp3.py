import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

dup = """
    char toast[128] = "";
    int toast_frames = 0;"""

if dup in s:
    s = s.replace(dup, "", 1)
    open(p, "w", encoding="utf-8").write(s)
    print("removed duplicate toast")
else:
    print("no duplicate")
