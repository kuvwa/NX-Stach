import os, struct, json

ROOT = r"C:\Users\kuvwa\NX-Stach"

def hm2():
    p = os.path.join(ROOT, "inbox", "dumps", "0100D0E00E51E000", "0000000000000070",
                     "HotlineMiami2", "savedata.vfs")
    d = open(p, "rb").read()
    m = b"achievements.dat"
    i = d.find(m)
    off = i + len(m)
    n = struct.unpack_from("<I", d, off)[0]
    data = d[off + 4: off + 4 + n]
    vals = [1 if c == 0x31 else 0 for c in data if c in (0x30, 0x31)]
    cat = json.load(open(os.path.join(ROOT, "romfs", "catalog", "274170.json"), encoding="utf-8"))
    names = [a["localized_name"] for a in cat["achievements"]]
    print("HM2: digits", len(vals), "unlocked idx", [i for i, v in enumerate(vals) if v])
    for i, v in enumerate(vals):
        if v:
            print("   ->", i, names[i] if i < len(names) else "?")

def downwell():
    p = os.path.join(ROOT, "inbox", "dumps", "010093D00C726000", "000000000000009A",
                     "default", "Downwell.sav")
    d = open(p, "rb").read()
    m = b'trophyFlag="'
    i = d.find(m)
    start = i + len(m)
    end = d.find(b'"', start)
    val = d[start:end].decode()
    mask = int(float(val))
    cat = json.load(open(os.path.join(ROOT, "romfs", "catalog", "360740.json"), encoding="utf-8"))
    names = [a["localized_name"] for a in cat["achievements"]]
    print("Downwell: trophyFlag", val, "mask", mask, "bin", bin(mask))
    for i in range(len(names)):
        if (mask >> i) & 1:
            print("   bit", i, "->", names[i])

hm2()
downwell()
