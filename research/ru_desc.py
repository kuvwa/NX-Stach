import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:150])
    s = s.replace(old, new, 1)


helper = r'''// Подменяет описания достижений на русские (имена остаются английскими).
static void apply_russian_descriptions(const char *appid,
                                       SteamAchievement *achievements,
                                       int count)
{
    if (!appid || count <= 0)
        return;

    const char *paths[2];
    char p1[192], p2[192];

    snprintf(p1, sizeof(p1), "sdmc:/switch/NX-Stach/catalog/%.32s_ru.json", appid);
    snprintf(p2, sizeof(p2), "romfs:/catalog/%.32s_ru.json", appid);

    paths[0] = p1;
    paths[1] = p2;

    for (int k = 0; k < 2; k++) {
        FILE *f = fopen(paths[k], "rb");

        if (!f) continue;

        fseek(f, 0, SEEK_END);
        long size = ftell(f);
        rewind(f);

        if (size <= 0 || size > 262144) {
            fclose(f);
            continue;
        }

        char *buf = malloc((size_t)size + 1);

        if (!buf) {
            fclose(f);
            return;
        }

        size_t got = fread(buf, 1, (size_t)size, f);
        fclose(f);

        if (got != (size_t)size) {
            free(buf);
            continue;
        }

        buf[size] = '\0';

        json_error_t err;
        json_t *root = json_loads(buf, 0, &err);
        free(buf);

        if (!root) continue;

        json_t *resp = json_object_get(root, "response");
        json_t *arr = resp ? json_object_get(resp, "achievements")
                           : json_object_get(root, "achievements");

        int replaced = 0;

        if (json_is_array(arr)) {
            size_t idx;
            json_t *item;

            json_array_foreach(arr, idx, item) {
                const char *id = json_string_value(
                    json_object_get(item, "internal_name"));
                const char *desc = json_string_value(
                    json_object_get(item, "localized_desc"));

                if (!id || !desc || !desc[0])
                    continue;

                for (int i = 0; i < count; i++) {
                    if (strcmp(achievements[i].id, id) != 0)
                        continue;

                    size_t len = strlen(desc);
                    if (len >= sizeof(achievements[i].description))
                        len = sizeof(achievements[i].description) - 1;

                    memcpy(achievements[i].description, desc, len);
                    achievements[i].description[len] = '\0';
                    replaced++;
                    break;
                }
            }
        }

        json_decref(root);

        if (replaced > 0)
            return;
    }
}

'''

rep("/* --------------------------------- main --------------------------------- */",
    helper + "/* --------------------------------- main --------------------------------- */")

# вызывать после загрузки каталога на экране игры и после импорта
rep("""                achievement_count = load_catalog(game->steam_appid, achievements,
                                                 MAX_ACHIEVEMENTS);
                fill_ach_names(achievements, achievement_count);""",
    """                achievement_count = load_catalog(game->steam_appid, achievements,
                                                 MAX_ACHIEVEMENTS);
                fill_ach_names(achievements, achievement_count);

                if (lang == 1)
                    apply_russian_descriptions(game->steam_appid, achievements,
                                               achievement_count);""")

rep("""                achievement_count = load_catalog(g->steam_appid, achievements,
                                                 MAX_ACHIEVEMENTS);
                fill_ach_names(achievements, achievement_count);""",
    """                achievement_count = load_catalog(g->steam_appid, achievements,
                                                 MAX_ACHIEVEMENTS);
                fill_ach_names(achievements, achievement_count);

                if (lang == 1)
                    apply_russian_descriptions(g->steam_appid, achievements,
                                               achievement_count);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
