import os, json, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = ["219150", "274170", "360740", "557340"]

for appid in APPS:
    url = ("https://api.steampowered.com/IPlayerService/GetGameAchievements/v1/"
           "?appid=%s&language=russian" % appid)
    raw = os.path.join(ROOT, "research", "api_%s_ru.json" % appid)
    subprocess.run(["curl.exe", "-s", "--max-time", "60", "-o", raw, url], check=False)

    if not os.path.exists(raw) or os.path.getsize(raw) < 100:
        print(appid, "FAILED")
        continue

    d = json.load(open(raw, encoding="utf-8"))
    items = d.get("response", {}).get("achievements", []) or []

    out = {"appid": appid, "achievements": []}
    for it in items:
        out["achievements"].append({
            "internal_name": it.get("internal_name", ""),
            "localized_name": it.get("localized_name", ""),
            "localized_desc": it.get("localized_desc", ""),
        })

    path = os.path.join(ROOT, "romfs", "catalog", appid + "_ru.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(appid, len(items), "->", os.path.basename(path))
