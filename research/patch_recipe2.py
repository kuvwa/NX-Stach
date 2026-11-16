import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s:\n%s" % (path, old[:160]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


# --- recipe.h: ключ = title_id + appid ---
patch("source/recipe.h", [
("""bool recipe_load(u64 title_id, Recipe *out);
bool recipe_save(const Recipe *r);
void recipe_delete(u64 title_id);""",
 """bool recipe_load(u64 title_id, const char *appid, Recipe *out);
bool recipe_save(const Recipe *r);
void recipe_delete(u64 title_id, const char *appid);"""),
])

# --- recipe.c ---
patch("source/recipe.c", [
("""static void path_for(u64 title_id, const char *prefix, char *out, size_t size)
{
    snprintf(out, size, "%s/recipes/%016llX.json", prefix,
             (unsigned long long)title_id);
}""",
 """static void path_for(u64 title_id, const char *appid, const char *prefix,
                     char *out, size_t size)
{
    snprintf(out, size, "%s/recipes/%016llX_%s.json", prefix,
             (unsigned long long)title_id, (appid && appid[0]) ? appid : "0");
}"""),

("""bool recipe_load(u64 title_id, Recipe *out)
{
    char path[192];

    out->valid = false;
    out->from_sd = false;

    path_for(title_id, "sdmc:/switch/NX-Stach", path, sizeof(path));""",
 """bool recipe_load(u64 title_id, const char *appid, Recipe *out)
{
    char path[220];

    out->valid = false;
    out->from_sd = false;

    path_for(title_id, appid, "sdmc:/switch/NX-Stach", path, sizeof(path));"""),

("""    // встроенные рецепты: romfs:/recipes/<id>.json
    snprintf(path, sizeof(path), "romfs:/recipes/%016llX.json",
             (unsigned long long)title_id);""",
 """    // встроенные рецепты: romfs:/recipes/<id>_<appid>.json
    snprintf(path, sizeof(path), "romfs:/recipes/%016llX_%s.json",
             (unsigned long long)title_id, (appid && appid[0]) ? appid : "0");"""),

("""    char path[192];
    path_for(r->title_id, "sdmc:/switch/NX-Stach", path, sizeof(path));""",
 """    char path[220];
    path_for(r->title_id, r->steam_appid, "sdmc:/switch/NX-Stach", path,
             sizeof(path));"""),

("""void recipe_delete(u64 title_id)
{
    char path[192];
    path_for(title_id, "sdmc:/switch/NX-Stach", path, sizeof(path));
    remove(path);
}""",
 """void recipe_delete(u64 title_id, const char *appid)
{
    char path[220];
    path_for(title_id, appid, "sdmc:/switch/NX-Stach", path, sizeof(path));
    remove(path);
}"""),
])

# --- main.c: передаём appid ---
patch("source/main.c", [
("""static int load_save_flags(u64 title_id, u8 *flags, int max_flags)
{
    Recipe recipe;

    if (!recipe_load(title_id, &recipe))
        return -1;

    return recipe_read_flags(&recipe, flags, max_flags);
}""",
 """static int load_save_flags(u64 title_id, const char *appid,
                           u8 *flags, int max_flags)
{
    Recipe recipe;

    if (!recipe_load(title_id, appid, &recipe))
        return -1;

    return recipe_read_flags(&recipe, flags, max_flags);
}"""),

("""flag_count = load_save_flags(game->title_id, flags,
                                                     MAX_ACHIEVEMENTS);""",
 """flag_count = load_save_flags(game->title_id, game->steam_appid,
                                                     flags, MAX_ACHIEVEMENTS);"""),

("""                        flag_count = load_save_flags(g->title_id, flags,
                                                     MAX_ACHIEVEMENTS);""",
 """                        flag_count = load_save_flags(g->title_id,
                                                     g->steam_appid, flags,
                                                     MAX_ACHIEVEMENTS);"""),
])
