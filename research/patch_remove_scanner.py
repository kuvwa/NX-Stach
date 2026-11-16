import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# 1) убрать include
s = s.replace('#include "scanner.h"\n', "", 1)

# 2) вырезать шаг сканирования из Y-флоу
start = s.find("                    // --- 2. ищем, как читать прогресс из сейва ---")
end = s.find("                }\n\n                if (kDown & HidNpadButton_B) {", start)

if start < 0 or end < 0:
    raise SystemExit("scan step not found")

s = s[:start] + s[end:]

# 3) кнопка теперь про Steam
s = s.replace('const char *label = "Сканировать сейв";',
              'const char *label = "Достижения из Steam";', 1)

open(p, "w", encoding="utf-8").write(s)
print("main patched")
