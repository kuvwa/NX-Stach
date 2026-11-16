import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:150])
    s = s.replace(old, new, 1)


# --- helper: русские описания ---
helper = (
"// Подменяет описания на русские (имена остаются английскими).\n"
"static void apply_russian_descriptions(const char *appid,\n"
"                                       SteamAchievement *achievements,\n"
"                                       int count)\n"
"{\n"
"    if (!appid || count <= 0)\n"
"        return;\n"
"\n"
"    char p1[192], p2[192];\n"
"\n"
"    snprintf(p1, sizeof(p1), \"sdmc:/switch/NX-Stach/catalog/%.32s_ru.json\", appid);\n"
"    snprintf(p2, sizeof(p2), \"romfs:/catalog/%.32s_ru.json\", appid);\n"
"\n"
"    const char *paths[2] = { p1, p2 };\n"
"\n"
"    for (int k = 0; k < 2; k++) {\n"
"        FILE *f = fopen(paths[k], \"rb\");\n"
"\n"
"        if (!f) continue;\n"
"\n"
"        fseek(f, 0, SEEK_END);\n"
"        long size = ftell(f);\n"
"        rewind(f);\n"
"\n"
"        if (size <= 0 || size > 262144) { fclose(f); continue; }\n"
"\n"
"        char *buf = malloc((size_t)size + 1);\n"
"\n"
"        if (!buf) { fclose(f); return; }\n"
"\n"
"        size_t got = fread(buf, 1, (size_t)size, f);\n"
"        fclose(f);\n"
"\n"
"        if (got != (size_t)size) { free(buf); continue; }\n"
"\n"
"        buf[size] = '\\0';\n"
"\n"
"        json_error_t err;\n"
"        json_t *root = json_loads(buf, 0, &err);\n"
"        free(buf);\n"
"\n"
"        if (!root) continue;\n"
"\n"
"        json_t *resp = json_object_get(root, \"response\");\n"
"        json_t *arr = resp ? json_object_get(resp, \"achievements\")\n"
"                           : json_object_get(root, \"achievements\");\n"
"\n"
"        int replaced = 0;\n"
"\n"
"        if (json_is_array(arr)) {\n"
"            size_t idx;\n"
"            json_t *item;\n"
"\n"
"            json_array_foreach(arr, idx, item) {\n"
"                const char *id = json_string_value(\n"
"                    json_object_get(item, \"internal_name\"));\n"
"                const char *desc = json_string_value(\n"
"                    json_object_get(item, \"localized_desc\"));\n"
"\n"
"                if (!id || !desc || !desc[0])\n"
"                    continue;\n"
"\n"
"                for (int i = 0; i < count; i++) {\n"
"                    if (strcmp(achievements[i].id, id) != 0)\n"
"                        continue;\n"
"\n"
"                    size_t len = strlen(desc);\n"
"                    if (len >= sizeof(achievements[i].description))\n"
"                        len = sizeof(achievements[i].description) - 1;\n"
"\n"
"                    memcpy(achievements[i].description, desc, len);\n"
"                    achievements[i].description[len] = '\\0';\n"
"                    replaced++;\n"
"                    break;\n"
"                }\n"
"            }\n"
"        }\n"
"\n"
"        json_decref(root);\n"
"\n"
"        if (replaced > 0)\n"
"            return;\n"
"    }\n"
"}\n"
"\n")

rep("/* --------------------------------- main --------------------------------- */",
    helper + "/* --------------------------------- main --------------------------------- */")

# A-обработчик: сразу после выбора каталога
rep("""                    if (game->steam_appid[0]) {
                        achievement_count = romfs_ready
                            ? load_catalog(game->steam_appid, achievements,
                                           MAX_ACHIEVEMENTS)
                            : 0;""",
    """                    if (game->steam_appid[0]) {
                        achievement_count = romfs_ready
                            ? load_catalog(game->steam_appid, achievements,
                                           MAX_ACHIEVEMENTS)
                            : 0;

                        if (lang == 1 && achievement_count > 0)
                            apply_russian_descriptions(game->steam_appid,
                                                       achievements,
                                                       achievement_count);""")

# импорт: после fill_ach_names
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
