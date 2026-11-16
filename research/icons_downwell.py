import json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
appid = "360740"

cat = json.load(open(os.path.join(ROOT, "romfs", "catalog", appid + ".json"), encoding="utf-8"))
out_dir = os.path.join(ROOT, "romfs", "catalog", "icons", appid)
os.makedirs(out_dir, exist_ok=True)

ok = 0
for a in cat["achievements"]:
    icon = a.get("icon") or ""
    if not icon:
        continue

    url = "https://shared.akamai.steamstatic.com/community_assets/images/apps/%s/%s" % (appid, icon)
    path = os.path.join(out_dir, a["internal_name"] + ".jpg")

    if os.path.exists(path) and os.path.getsize(path) > 200:
        ok += 1
        continue

    subprocess.run(["curl.exe", "-s", "--max-time", "30", "-o", path, url], check=False)

    if os.path.exists(path) and os.path.getsize(path) > 200:
        ok += 1
    else:
        print("FAIL", a["internal_name"])

print(appid, "icons:", ok, "/", len(cat["achievements"]))
