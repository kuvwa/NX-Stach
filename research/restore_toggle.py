import subprocess, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

old = subprocess.run(["git", "show", "HEAD:source/main.c"], cwd=ROOT,
                     capture_output=True, text=True, encoding="utf-8").stdout

start = old.find("// Тумблер: пилюля со светлой окантовкой")
end = old.find("static void draw_scrollbar(", start)

if start < 0 or end < 0:
    raise SystemExit("toggle block not found in HEAD")

toggle = old[start:end]

p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

if "static void draw_toggle(" in s:
    print("already present")
else:
    anchor = "static void draw_scrollbar("
    s = s.replace(anchor, toggle + anchor, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("restored draw_toggle")
