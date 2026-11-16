import os, json, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPID = "557340"

# ---------- format 4 в gamesave.c ----------
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

anchor = """    if (format == 3) {"""

add = """    if (format == 4) {
        // marker = префикс ключа; значение — '0'/'1' после записи 06+u32+01
        size_t plen = marker ? strlen(marker) : 0;

        if (plen == 0) {
            last_error = "ARGUMENT";
            free(data);
            return -1;
        }

        int bad = 0;

        for (int i = 0; i < max_flags; i++) {
            char key[96];
            snprintf(key, sizeof(key), "%s%d", marker, i);

            size_t klen = strlen(key);
            size_t pos = (size_t)-1;

            for (size_t k = 0; k + klen < size; k++) {
                if (memcmp(data + k, key, klen) == 0) {
                    pos = k + klen;
                    break;
                }
            }

            if (pos == (size_t)-1 || pos + 7 > size) {
                flags[i] = 0;
                bad++;
                continue;
            }

            // 06 <u32> 01 <'0'|'1'>
            flags[i] = (data[pos + 6] == '1') ? 1 : 0;
        }

        free(data);
        last_error = "OK";
        return max_flags;
    }

"""

if anchor not in s:
    raise SystemExit("format3 anchor not found")

s = s.replace(anchor, add + anchor, 1)
open(p, "w", encoding="utf-8").write(s)
print("format4 ok")

# ---------- variant ----------
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()
old = '    { 0x010093D00C726000ULL, "Downwell", "360740" },'
new = old + '\n    { 0x010031200B94C000ULL, "My Friend Pedro", "557340" },'
if old in s and "My Friend Pedro" not in s:
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("variant ok")

# ---------- каталог + иконки ----------
raw = os.path.join(ROOT, "research", "api_557340.json")
d = json.load(open(raw, encoding="utf-8"))
items = d["response"]["achievements"]
items.sort(key=lambda x: x.get("internal_key", 0))

out = {"appid": APPID, "achievements": []}
for it in items:
    out["achievements"].append({
        "internal_name": it["internal_name"],
        "localized_name": it["localized_name"],
        "localized_desc": it["localized_desc"],
        "icon": it["icon"],
    })

cat_path = os.path.join(ROOT, "romfs", "catalog", APPID + ".json")
json.dump(out, open(cat_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

icon_dir = os.path.join(ROOT, "romfs", "catalog", "icons", APPID)
os.makedirs(icon_dir, exist_ok=True)

ok = 0
for a in out["achievements"]:
    url = "https://shared.akamai.steamstatic.com/community_assets/images/apps/%s/%s" % (APPID, a["icon"])
    path = os.path.join(icon_dir, a["internal_name"] + ".jpg")
    if os.path.exists(path) and os.path.getsize(path) > 200:
        ok += 1
        continue
    subprocess.run(["curl.exe", "-s", "--max-time", "30", "-o", path, url], check=False)
    if os.path.exists(path) and os.path.getsize(path) > 200:
        ok += 1

print("catalog", len(out["achievements"]), "icons", ok)
