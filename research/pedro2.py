import os, json

ROOT = r"C:\Users\kuvwa\NX-Stach"
save = os.path.join(ROOT, "inbox", "dumps", "010031200B94C000", "000000000000008B", "Pedro")
d = open(save, "rb").read()

print("values by key:")
unlocked = []
for i in range(30):
    key = ("achievementUnlocked%d" % i).encode()
    pos = d.find(key)
    if pos < 0:
        print(i, "key not found")
        continue
    after = pos + len(key)
    rec = d[after:after + 10]
    # 06 + u32 id, затем 01 (bool) + '0'/'1'
    ok = rec[0] == 0x06 and rec[5] == 0x01
    val = chr(rec[6]) if ok else None
    if val == '1':
        unlocked.append(i)
    print("%2d  %s  %s" % (i, rec.hex(" "), val))

print("unlocked:", unlocked)

cat = json.load(open(os.path.join(ROOT, "research", "api_557340.json"), encoding="utf-8"))
items = cat["response"]["achievements"]
items.sort(key=lambda x: x.get("internal_key", 0))
names = [x["localized_name"] for x in items]
for i in unlocked:
    print("  ->", i, names[i] if i < len(names) else "?")
