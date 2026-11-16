import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# ---------- Y-флоу: выгрузка сейва вместо Steam ----------
start = s.find("                if (kDown & HidNpadButton_Y) {")
end = s.find("                if (kDown & HidNpadButton_B) {", start)

if start < 0 or end < 0:
    raise SystemExit("Y block not found")

BLOCK = r'''                if (kDown & HidNpadButton_Y) {
                    Game *g = &games[view[selected]];

                    draw_progress(&fb, face, face_small, g->name,
                                  "Выгружаем сейв на карту...", 40);

                    int copied = gamesave_dump_to_sd(g->title_id);

                    if (copied > 0) {
                        snprintf(toast, sizeof(toast),
                                 "Сейв выгружен: %d файлов (dumps/%016llX)",
                                 copied, (unsigned long long)g->title_id);
                    } else {
                        snprintf(toast, sizeof(toast), "Сейв не найден или пуст");
                    }

                    toast_frames = 260;
                }

'''

s = s[:start] + BLOCK + s[end:]

# ---------- кнопка ----------
s = s.replace('const char *label = "Достижения из Steam";',
              'const char *label = "Выгрузить сейв";', 1)

# ---------- убрать импорты Steam/GitHub ----------
for inc in ('#include "steamsearch.h"\n', '#include "upload.h"\n'):
    s = s.replace(inc, "", 1)

open(p, "w", encoding="utf-8").write(s)
print("main ok")
