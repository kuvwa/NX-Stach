import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# 1) убрать подвал модального окна
start = s.find("            char foot[96];")
if start >= 0:
    end = s.find("        }\n\n        if (toast_frames > 0) {", start)
    if end > start:
        s = s[:start] + s[end:]

# 2) убрать подсказку про тап
start = s.find("            if (achievement_count > 0 && flag_count <= 0) {")
if start >= 0:
    end = s.find("            }\n", s.find("reset_text_color();", start))
    if end > start:
        s = s[:start] + s[end + len("            }\n"):]

open(p, "w", encoding="utf-8").write(s)
print("ok")
