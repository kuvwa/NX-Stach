import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "research")
ICON_BASE = "https://shared.akamai.steamstatic.com/community_assets/images/apps/%s/%s"

for appid in ("219150", "274170"):
    raw_path = os.path.join(RES, "api_%s.json" % appid)
    url = ("https://api.steampowered.com/IPlayerService/GetGameAchievements/v1/"
           "?appid=%s&language=english" % appid)
    subprocess.run(["curl.exe", "-s", "--max-time", "60", "-A", "NX-Stach/1.0",
                    "-o", raw_path, url], check=False)
    d = json.load(open(raw_path, encoding="utf-8"))
    items = d.get("response", {}).get("achievements", []) or []
    items.sort(key=lambda x: x.get("internal_key", 0))

    out = {"appid": appid, "achievements": []}
    print("\n=== %s : %d achievements ===" % (appid, len(items)))
    for i, it in enumerate(items):
        icon = it.get("icon") or ""
        if icon and not icon.startswith("http"):
            icon = ICON_BASE % (appid, icon)
        out["achievements"].append({
            "id": it.get("internal_name", ""),
            "name": it.get("localized_name", ""),
            "description": it.get("localized_desc", ""),
            "icon": icon,
        })
        print("%2d  key=%3s  %-28s %s" % (i, it.get("internal_key"), it.get("internal_name"), it.get("localized_name")))

    for target in (os.path.join(ROOT, "romfs", "catalog"), os.path.join(ROOT, "data")):
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, appid + ".json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    print("written: romfs/catalog/%s.json" % appid)
