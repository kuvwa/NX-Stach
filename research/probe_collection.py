import re, os, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for name in ("research/savedata.vfs", "inbox/savedata.vfs"):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        continue
    s = open(p, "rb").read()
    print("=" * 60)
    print(name, len(s))

    strings = []
    cur = bytearray()
    for b in s:
        if 32 <= b < 127:
            cur.append(b)
        else:
            if len(cur) >= 4:
                strings.append((len(cur), bytes(cur).decode("ascii")))
            cur = bytearray()
    if len(cur) >= 4:
        strings.append((len(cur), bytes(cur).decode("ascii")))

    for n, t in strings:
        low = t.lower()
        if any(k in low for k in ("miami", "hotline", "unlocked", "achiev", "savedata", "stat", "silverware", ".dat", ".sav", ".nfo", ".vfs")):
            print("  ", n, t[:90])

    print("  counts: unlocked_achievements.dat =", s.count(b"unlocked_achievements.dat"),
          " achievements.dat =", s.count(b"achievements.dat"),
          " savedata.vfs =", s.count(b"savedata.vfs"))
