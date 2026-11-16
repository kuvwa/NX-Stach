import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """            build_list(game->steam_appid, achievements, achievement_count,
                       flags, flag_count, only_locked != 0);
"""

new = """            build_list(game->steam_appid, achievements, achievement_count,
                       flags, flag_count, only_locked != 0);

            if (achievement_count <= 0) {
                set_text_color(150, 155, 165);
                draw_text(face_small, pixels, 55, 380, "Нет каталога достижений");
                draw_text(face_small, pixels, 55, 410,
                          game->steam_appid[0]
                          ? "Проверь romfs:/catalog/ и Steam AppID"
                          : "У игры не указан Steam AppID");
                reset_text_color();
            }
"""

if old not in s:
    raise SystemExit("build_list call not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
