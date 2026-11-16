import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# 1) обработчик Y (выгрузка сейва)
start = s.find("                if (kDown & HidNpadButton_Y) {")
end = s.find("                if (kDown & HidNpadButton_B) {", start)

if start < 0 or end < 0:
    raise SystemExit("Y handler not found")

s = s[:start] + s[end:]

# 2) кнопка в шапке
start = s.find('            {\n                const char *label = "Выгрузить сейв";')
if start >= 0:
    end = s.find("            }\n", start)
    if end > start:
        s = s[:start] + s[end + len("            }\n"):]

# 3) зона тапа
old_tap = """                } else if (tap_y >= 30 && tap_y <= 78 && tap_x >= 980) {
                    kDown |= HidNpadButton_Y;
                } else if (tap_y >= 276 && tap_y <= 332) {"""
new_tap = """                } else if (tap_y >= 276 && tap_y <= 332) {"""

if old_tap in s:
    s = s.replace(old_tap, new_tap, 1)

open(p, "w", encoding="utf-8").write(s)

# 4) удалить draw_progress, если больше не используется
if s.count("draw_progress(") == 1:
    ps = s.find("static void draw_progress(")
    if ps >= 0:
        pe = s.find("/* ------------------------------- стики", ps)
        if pe > ps:
            s = s[:ps] + s[pe:]
            open(p, "w", encoding="utf-8").write(s)

print("ok")
