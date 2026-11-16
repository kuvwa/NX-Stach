import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- save.h ----------
p = os.path.join(ROOT, "source", "save.h")
s = open(p, encoding="utf-8").read()
if "save_lock" not in s:
    s = s.replace("bool save_unlock(const char *appid, const char *achievement_id);",
                  "bool save_unlock(const char *appid, const char *achievement_id);\n"
                  "bool save_lock(const char *appid, const char *achievement_id);")
    open(p, "w", encoding="utf-8").write(s)
    print("save.h ok")

# ---------- save.c ----------
p = os.path.join(ROOT, "source", "save.c")
s = open(p, encoding="utf-8").read()

if "bool save_lock(" not in s:
    # добавить реализацию перед save_status
    anchor = "const char *save_status(void)"
    impl = '''bool save_lock(const char *appid, const char *achievement_id)
{
    if (!root || !appid || !achievement_id)
        return false;

    json_t *games = json_object_get(root, "games");
    json_t *game = json_object_get(games, appid);

    if (!json_is_object(game))
        return false;

    json_t *achievements = json_object_get(game, "achievements");

    if (json_is_object(achievements))
        json_object_del(achievements, achievement_id);

    return save_flush();
}

'''
    if anchor not in s:
        raise SystemExit("save_status not found")
    s = s.replace(anchor, impl + anchor, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("save.c ok")
