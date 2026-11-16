import os, json, subprocess, re

ROOT = r"C:\Users\kuvwa\NX-Stach"
APPID = "557340"

raw = os.path.join(ROOT, "research", "api_557340.json")
if not os.path.exists(raw):
    subprocess.run(["curl.exe", "-s", "--max-time", "60", "-o", raw,
                    "https://api.steampowered.com/IPlayerService/GetGameAchievements/v1/?appid=%s&language=english" % APPID])

d = json.load(open(raw, encoding="utf-8"))
items = d["response"]["achievements"]
items.sort(key=lambda x: x.get("internal_key", 0))
names = [it["internal_name"] for it in items]
print("achievements:", len(names), names[:6])

save = os.path.join(ROOT, "inbox", "dumps", "010031200B94C000",
                    "000000000000008B", "Pedro")
data = open(save, "rb").read()

found = 0
for n in names:
    b = n.encode()
    if b in data:
        found += 1
print("names found in save:", found, "/", len(names))

# показать контекст вокруг пары имён
shown = 0
for n in names:
    b = n.encode()
    i = data.find(b)
    if i < 0:
        continue
    print("---", n, "at", i)
    print("   ", data[i:i+40].hex(" "))
    shown += 1
    if shown >= 4:
        break
