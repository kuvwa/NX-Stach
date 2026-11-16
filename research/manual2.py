import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "save.c")
s = open(p, encoding="utf-8").read()

start = s.find("bool save_lock(const char *appid, const char *achievement_id)")
if start < 0:
    raise SystemExit("save_lock not found")

end = s.find("const char *save_status(void)", start)
if end < 0:
    raise SystemExit("save_status not found")

impl = '''bool save_lock(const char *appid, const char *achievement_id)
{
    if (!root || !appid || !achievement_id) {
        snprintf(status_text, sizeof(status_text), "Save not initialized");
        return false;
    }

    json_t *games = json_object_get(root, "games");
    json_t *game = json_object_get(games, appid);

    if (!json_is_object(game))
        return false;

    json_t *achievements = json_object_get(game, "achievements");

    if (json_is_object(achievements))
        json_object_del(achievements, achievement_id);

    if (json_dump_file(root, TEMP_FILE, JSON_INDENT(2)) != 0) {
        snprintf(status_text, sizeof(status_text), "Write failed");
        return false;
    }

    remove(SAVE_FILE);

    if (rename(TEMP_FILE, SAVE_FILE) != 0) {
        snprintf(status_text, sizeof(status_text), "Rename failed");
        return false;
    }

    snprintf(status_text, sizeof(status_text), "Achievement saved OK");
    return true;
}

'''

s = s[:start] + impl + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
