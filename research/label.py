import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = 'snprintf(line, sizeof(line), "Иконки %d / %d", i + 1, tmp_count);'
new = 'snprintf(line, sizeof(line), "Загрузка... %d / %d", i + 1, tmp_count);'

if old not in s:
    raise SystemExit("line not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
