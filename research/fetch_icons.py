import json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for appid in ("219150", "274170"):
    cat = json.load(open(os.path.join(ROOT, "romfs", "catalog", appid + ".json"), encoding="utf-8"))
    out_dir = os.path.join(ROOT, "romfs", "catalog", "icons", appid)
    os.makedirs(out_dir, exist_ok=True)

    ok = 0
    for a in cat["achievements"]:
        icon = a.get("icon") or ""
        if not icon.startswith("http"):
            continue
        path = os.path.join(out_dir, a["id"] + ".jpg")
        if os.path.exists(path) and os.path.getsize(path) > 200:
            ok += 1
            continue
        subprocess.run(["curl.exe", "-s", "--max-time", "30", "-o", path, icon], check=False)
        if os.path.exists(path) and os.path.getsize(path) > 200:
            ok += 1
        else:
            print("FAIL", a["id"])

    total = sum(os.path.getsize(os.path.join(out_dir, f)) for f in os.listdir(out_dir))
    print(appid, "icons:", ok, "/", len(cat["achievements"]), "bytes:", total)
