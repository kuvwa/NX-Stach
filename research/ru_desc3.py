import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s: %s" % (path, old[:100]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


patch("source/steamsearch.h", [
("int steam_fetch_achievements(int appid, char *buffer, size_t size);",
 "int steam_fetch_achievements(int appid, char *buffer, size_t size);\n"
 "int steam_fetch_achievements_lang(int appid, const char *language,\n"
 "                                  char *buffer, size_t size);"),
])

patch("source/steamsearch.c", [
("""int steam_fetch_achievements(int appid, char *buffer, size_t size)
{
    char path[192];
    snprintf(path, sizeof(path),
             "/IPlayerService/GetGameAchievements/v1/?appid=%d&language=english",
             appid);""",
 """int steam_fetch_achievements(int appid, char *buffer, size_t size)
{
    return steam_fetch_achievements_lang(appid, "english", buffer, size);
}

int steam_fetch_achievements_lang(int appid, const char *language,
                                  char *buffer, size_t size)
{
    char path[192];
    snprintf(path, sizeof(path),
             "/IPlayerService/GetGameAchievements/v1/?appid=%d&language=%s",
             appid, language ? language : "english");"""),
])

# main: при импорте скачать и русский каталог
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                tmp_count = steam_parse_achievements(json_buf, tmp, MAX_ACHIEVEMENTS);
            }

            free(json_buf);"""

new = """                tmp_count = steam_parse_achievements(json_buf, tmp, MAX_ACHIEVEMENTS);

                // отдельно тянем русские описания
                char *ru_buf = malloc(512 * 1024);

                if (ru_buf) {
                    int ru_len = steam_fetch_achievements_lang(appid, "russian",
                                                               ru_buf, 512 * 1024);

                    if (ru_len > 0) {
                        char rpath[240];
                        snprintf(rpath, sizeof(rpath),
                                 "sdmc:/switch/NX-Stach/catalog/%s_ru.json",
                                 appid_text);

                        FILE *rf = fopen(rpath, "wb");
                        if (rf) {
                            fwrite(ru_buf, 1, (size_t)ru_len, rf);
                            fclose(rf);
                        }
                    }

                    free(ru_buf);
                }
            }

            free(json_buf);"""

if old in s:
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("main ok")
else:
    raise SystemExit("import block not found")
