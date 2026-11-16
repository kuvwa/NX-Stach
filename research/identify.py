import os, re

ROOT = r"C:\Users\kuvwa\NX-Stach\inbox\dumps"

def strings(data, minlen=4):
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
    return out

targets = [
    "010021C000B6A000/0000000000000095/options.ini",
    "010093D00C726000/000000000000009A/default/Downwell.sav",
    "01007B600D5BC000/0000000000000093/SAVEDATA000/DMC3_SAVEDATA",
    "0100E2F014F46000/0000000000000074/SYSTEM/SURVIVAL_SAVE.DAT",
    "0100E2F014F46000/0000000000000074/SYSTEM/SYS_SAVE.DAT",
    "0100E2F014F46000/0000000000000074/SAVEPOINT/000_SAVEDATA.DAT",
    "010099A00BC1E000/0000000000000071/SAVEDATA000/savegame00.sav",
    "0100D0E00E51E000/0000000000000070/HotlineMiami2/savedata.vfs",
]

for t in targets:
    p = os.path.join(ROOT, t.replace("/", os.sep))
    if not os.path.exists(p):
        print("missing", t)
        continue
    data = open(p, "rb").read()
    st = strings(data, 5)
    print("=" * 70)
    print(t, len(data), "strings:", len(st))
    for s in st[:40]:
        print("   ", s[:90])
