import os

ROOT = r"C:\Users\kuvwa\NX-Stach\inbox\dumps"

def strings(data, minlen=5, limit=60):
    out, cur = [], bytearray()
    for b in data:
        if 32 <= b < 127:
            cur.append(b)
        else:
            if len(cur) >= minlen:
                out.append(cur.decode("ascii"))
            cur = bytearray()
    if len(cur) >= minlen:
        out.append(cur.decode("ascii"))
    return out[:limit]

def runs(data):
    # ASCII 0/1 с разделителями
    best_a = (0, 0)
    i = 0
    n = len(data)
    while i < n:
        if data[i] in (0x30, 0x31):
            st = i
            d = 0
            while i < n and (data[i] in (0x30, 0x31) or data[i] in (0x0A, 0x0D)):
                if data[i] in (0x30, 0x31):
                    d += 1
                i += 1
            if d > best_a[1]:
                best_a = (st, d)
        else:
            i += 1

    # байты 0/1
    best_r = (0, 0)
    i = 0
    while i < n:
        if data[i] <= 1:
            st = i
            c = 0
            while i < n and data[i] <= 1:
                c += 1
                i += 1
            if c > best_r[1]:
                best_r = (st, c)
        else:
            i += 1

    return best_a, best_r

targets = [
    "010031200B94C000/000000000000008B/Pedro",
    "01004D300C5AE000/0000000000000088/file0",
    "01004D300C5AE000/0000000000000088/system",
    "010099A00BC1E000/0000000000000071/SAVEDATA000/savegame00.sav",
    "010021C000B6A000/0000000000000095/rep_gamestate1.dat",
    "010021C000B6A000/0000000000000095/rep_gamedata1.dat",
    "0100E2F014F46000/0000000000000074/SYSTEM/SURVIVAL_SAVE.DAT",
    "0100E2F014F46000/0000000000000074/SYSTEM/SYS_SAVE.DAT",
    "0100E2F014F46000/0000000000000074/SAVEPOINT/000_SAVEDATA.DAT",
    "01007B600D5BC000/0000000000000093/SAVEDATA000/DMC3_SAVEDATA",
]

for t in targets:
    p = os.path.join(ROOT, t.replace("/", os.sep))
    if not os.path.exists(p):
        print("missing", t)
        continue
    d = open(p, "rb").read()
    a, r = runs(d)
    print("=" * 70)
    print(t, len(d), "| ascii01", a, "| raw01", r)
    for s in strings(d, 5, 12):
        print("   ", s[:80])
