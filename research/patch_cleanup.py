import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# 1) убрать весь отладочный «чёрный ящик» (он тормозил меню)
s = re.sub(r"[ \t]*beat\([^;]*\);[ \t]*\n", "", s)
s = re.sub(r"[ \t]*beat_flush\(\);[ \t]*\n", "", s)
s = re.sub(r"[ \t]*if \(\(i % 3\) == 0\)[ \t]*\n[ \t]*beat_flush\(\);[ \t]*\n", "", s)
s = re.sub(r"[ \t]*if \(\(i % 2\) == 0\)[ \t]*\n[ \t]*beat_flush\(\);[ \t]*\n", "", s)
s = re.sub(r"[ \t]*if \(\(i % 3\) == 0 \|\| i == selected\)[ \t]*\n[ \t]*beat_flush\(\);[ \t]*\n", "", s)

# сами функции и глобалы
start = s.find("static const char *g_stage = \"init\";")
if start >= 0:
    end = s.find("/* --------------------------------- main --------------------------------- */", start)
    if end > start:
        s = s[:start] + s[end:]

# 2) пропускать обложки известных «битых» игр
old = """    for (int i = 0; i < game_count; i++) {
        g_detail_id = (unsigned long long)games[i].title_id;
"""

new = """    for (int i = 0; i < game_count; i++) {
        // у этой игры битый образ-иконка, покрытие пропускаем
        if (games[i].title_id == 0x010021C000B6A000ULL)
            continue;

"""

if old in s:
    s = s.replace(old, new, 1)

# g_detail_id больше не нужен в предзагрузке
s = s.replace("""            draw_cover_loading(&fb, face, face_small, i, game_count);""",
              """        draw_cover_loading(&fb, face, face_small, i, game_count);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
