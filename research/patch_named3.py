import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# имена достижений для рецептов/сканера
rep("""static int load_save_flags(u64 title_id, const char *appid,
                           u8 *flags, int max_flags)
{
    Recipe recipe;

    if (!recipe_load(title_id, appid, &recipe))
        return -1;

    return recipe_read_flags(&recipe, flags, max_flags);
}""",
    """static const char *g_ach_names[MAX_ACHIEVEMENTS];
static int g_ach_name_count = 0;

static void fill_ach_names(const SteamAchievement *achievements, int count)
{
    g_ach_name_count = 0;

    for (int i = 0; i < count && i < MAX_ACHIEVEMENTS; i++) {
        g_ach_names[i] = achievements[i].id;
        g_ach_name_count = i + 1;
    }
}

static int load_save_flags(u64 title_id, const char *appid,
                           u8 *flags, int max_flags)
{
    Recipe recipe;

    if (!recipe_load(title_id, appid, &recipe))
        return -1;

    return recipe_read_flags(&recipe, g_ach_names, g_ach_name_count,
                             flags, max_flags);
}""")

# заполняем имена после загрузки каталога
rep("""                    ach_icons_load(game->steam_appid, achievement_count, achievements);""",
    """                    fill_ach_names(achievements, achievement_count);
                    ach_icons_load(game->steam_appid, achievement_count, achievements);""")

open(p, "w", encoding="utf-8").write(s)
print("names ok")
