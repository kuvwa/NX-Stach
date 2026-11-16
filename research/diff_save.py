import struct, os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def flags(path):
    s = open(path, "rb").read()
    m = b"unlocked_achievements.dat"
    i = s.find(m)
    if i < 0:
        return None, None, len(s)
    off = i + len(m)
    n = struct.unpack_from("<I", s, off)[0]
    data = s[off + 4: off + 4 + n]
    vals = [1 if c == 0x31 else 0 for c in data if c in (0x30, 0x31)]
    return vals, data, len(s)

old_p = os.path.join(ROOT, "research", "savedata.vfs")
new_p = os.path.join(ROOT, "inbox", "savedata.vfs")

old, oldraw, oldsize = flags(old_p)
new, newraw, newsize = flags(new_p)

cat = json.load(open(os.path.join(ROOT, "romfs", "catalog", "219150.json"), encoding="utf-8"))
names = [a["name"] for a in cat["achievements"]]

print("old size", oldsize, "flags", len(old), "->", "".join(map(str, old)))
print("new size", newsize, "flags", len(new), "->", "".join(map(str, new)))

print("\nchanged indices:")
for i in range(max(len(old), len(new))):
    a = old[i] if i < len(old) else None
    b = new[i] if i < len(new) else None
    if a != b:
        print("  index %d: %s -> %s   (key order name: %s)" % (
            i, a, b, names[i] if i < len(names) else "?"))

print("\nunlocked in new:", [i for i, v in enumerate(new) if v])
print("\nall names by index:")
for i, n in enumerate(names):
    print("%2d %-8s %s" % (i, "UNLOCK" if i < len(new) and new[i] else "", n))
