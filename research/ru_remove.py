import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# 1) убрать вызовы
s = s.replace("""                        if (lang == 1 && achievement_count > 0)
                            apply_russian_descriptions(game->steam_appid,
                                                       achievements,
                                                       achievement_count);
""", "")

s = s.replace("""
                if (lang == 1)
                    apply_russian_descriptions(g->steam_appid, achievements,
                                               achievement_count);
""", "")

# 2) убрать саму функцию
start = s.find("// Подменяет описания на русские (имена остаются английскими).")
if start >= 0:
    end = s.find("/* --------------------------------- main --------------------------------- */", start)
    if end > start:
        s = s[:start] + s[end:]

# 3) убрать загрузку русского каталога при импорте
start = s.find("                // отдельно тянем русские описания")
if start >= 0:
    end = s.find("            }\n\n            free(json_buf);", start)
    if end > start:
        s = s[:start] + s[end:]

open(p, "w", encoding="utf-8").write(s)
print("main ok")

# 4) убрать _lang из steamsearch
p = os.path.join(ROOT, "source", "steamsearch.h")
s = open(p, encoding="utf-8").read()
s = s.replace("int steam_fetch_achievements_lang(int appid, const char *language,\n"
              "                                  char *buffer, size_t size);\n", "")
open(p, "w", encoding="utf-8").write(s)
print("h ok")

p = os.path.join(ROOT, "source", "steamsearch.c")
s = open(p, encoding="utf-8").read()
s = s.replace("""int steam_fetch_achievements(int appid, char *buffer, size_t size)
{
    return steam_fetch_achievements_lang(appid, "english", buffer, size);
}

int steam_fetch_achievements_lang(int appid, const char *language,
                                  char *buffer, size_t size)
{
    char path[192];
    snprintf(path, sizeof(path),
             "/IPlayerService/GetGameAchievements/v1/?appid=%d&language=%s",
             appid, language ? language : "english");""",
"""int steam_fetch_achievements(int appid, char *buffer, size_t size)
{
    char path[192];
    snprintf(path, sizeof(path),
             "/IPlayerService/GetGameAchievements/v1/?appid=%d&language=english",
             appid);""")
open(p, "w", encoding="utf-8").write(s)
print("c ok")

# 5) удалить русские каталоги из romfs
cat = os.path.join(ROOT, "romfs", "catalog")
for f in os.listdir(cat):
    if f.endswith("_ru.json"):
        os.remove(os.path.join(cat, f))
        print("removed", f)
