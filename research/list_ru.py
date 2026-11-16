import re, os

ROOT = dirs = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

cyr = re.compile(r'"[^"\n]*[\u0400-\u04FF][^"\n]*"')
seen = []
for m in cyr.finditer(s):
    t = m.group(0)
    if t not in seen:
        seen.append(t)

for t in seen:
    print(t)
