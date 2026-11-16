import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- steam.c: поддержать оба формата ключей ----------
p = os.path.join(ROOT, "source", "steam.c")
s = open(p, encoding="utf-8").read()

old = """    json_array_foreach(array, i, item) {
        if (count >= max_achievements) break;

        copy_string(achievements[count].id,
                    sizeof(achievements[count].id),
                    json_string_value(json_object_get(item, "internal_name")));

        copy_string(achievements[count].name,
                    sizeof(achievements[count].name),
                    json_string_value(json_object_get(item, "localized_name")));

        copy_string(achievements[count].description,
                    sizeof(achievements[count].description),
                    json_string_value(json_object_get(item, "localized_desc")));

        copy_string(achievements[count].icon,
                    sizeof(achievements[count].icon),
                    json_string_value(json_object_get(item, "icon")));

        count++;
    }"""

new = """    json_array_foreach(array, i, item) {
        if (count >= max_achievements) break;

        json_t *v;

        v = json_object_get(item, "internal_name");
        if (!json_is_string(v)) v = json_object_get(item, "id");
        copy_string(achievements[count].id, sizeof(achievements[count].id),
                    json_string_value(v));

        v = json_object_get(item, "localized_name");
        if (!json_is_string(v)) v = json_object_get(item, "name");
        copy_string(achievements[count].name, sizeof(achievements[count].name),
                    json_string_value(v));

        v = json_object_get(item, "localized_desc");
        if (!json_is_string(v)) v = json_object_get(item, "description");
        copy_string(achievements[count].description,
                    sizeof(achievements[count].description),
                    json_string_value(v));

        copy_string(achievements[count].icon,
                    sizeof(achievements[count].icon),
                    json_string_value(json_object_get(item, "icon")));

        count++;
    }"""

if old not in s:
    raise SystemExit("steam.c block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("steam.c patched")

# ---------- перегенерировать каталоги с правильными ключами ----------
for appid in ("219150", "274170"):
    path = os.path.join(ROOT, "romfs", "catalog", appid + ".json")
    d = json.load(open(path, encoding="utf-8"))

    fixed = []
    for a in d["achievements"]:
        fixed.append({
            "internal_name": a["id"],
            "localized_name": a["name"],
            "localized_desc": a["description"],
            "icon": a["icon"],
        })

    d["achievements"] = fixed

    for target in (os.path.join(ROOT, "romfs", "catalog"), os.path.join(ROOT, "data")):
        with open(os.path.join(target, appid + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

    print(appid, "catalog fixed:", len(fixed), "first:", fixed[0]["localized_name"])
