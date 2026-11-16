import re, json, os, html

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotline_achievements.html")
s = open(p, encoding="utf-8", errors="replace").read()

# режем по data-tableindex блоки
parts = re.split(r'data-tableindex="(\d+)"', s)
# parts[0] - префикс, дальше пары (index, block)
items = []
for i in range(1, len(parts) - 1, 2):
    idx = int(parts[i])
    block = parts[i + 1][:6000]
    name = None
    m = re.search(r'<h1[^>]*>(.*?)</h1>', block, re.S)
    if m:
        name = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    icon = None
    m = re.search(r'src="(https://[^"]*images/apps/219150/[^"]+)"', block)
    if m:
        icon = m.group(1)
    # описание: ищем текст после h1 в этом же блоке
    desc = None
    if m:
        pass
    items.append({"index": idx, "name": name, "icon": icon, "block": block})

print("items:", len(items))
for it in items[:6]:
    print(it["index"], "|", it["name"])
    # вытащим видимые тексты блока
    texts = re.findall(r'>([^<>{}]{2,120})<', it["block"])
    texts = [html.unescape(t).strip() for t in texts if t.strip() and not t.strip().startswith('var')]
    print("   texts:", texts[:8])
