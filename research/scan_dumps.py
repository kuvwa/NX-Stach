import os, re, struct, zlib

ROOT = r"C:\Users\kuvwa\NX-Stach\inbox\dumps"

def strings(data, minlen=4):
    out = []
    cur = bytearray()
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

def ascii01_runs(data):
    best = (0, 0)
    i = 0
    n = len(data)
    while i < n:
        if data[i] in (0x30, 0x31):
            start = i
            digits = 0
            while i < n and (data[i] in (0x30, 0x31) or data[i] in (0x0A, 0x0D)):
                if data[i] in (0x30, 0x31):
                    digits += 1
                i += 1
            if digits > best[1]:
                best = (start, digits)
        else:
            i += 1
    return best

def raw01_runs(data):
    best = (0, 0)
    i = 0
    n = len(data)
    while i < n:
        if data[i] <= 1:
            start = i
            c = 0
            while i < n and data[i] <= 1:
                c += 1
                i += 1
            if c > best[1]:
                best = (start, c)
        else:
            i += 1
    return best

for title in sorted(os.listdir(ROOT)):
    tdir = os.path.join(ROOT, title)
    if not os.path.isdir(tdir):
        continue
    files = []
    for base, _, names in os.walk(tdir):
        for n in names:
            if n == "report.txt":
                continue
            p = os.path.join(base, n)
            files.append((os.path.relpath(p, tdir), os.path.getsize(p)))

    print("=" * 70)
    print(title, "files:", len(files))

    for rel, size in files:
        if size > 3_000_000:
            print("  ", rel, size, "(skip large)")
            continue
        data = open(os.path.join(tdir, rel), "rb").read()
        a = ascii01_runs(data)
        r = raw01_runs(data)
        todo = []
        if a[1] >= 8:
            todo.append("ascii01@%d x%d" % a)
        if r[1] >= 8:
            todo.append("raw01@%d x%d" % r)
        txt = " ".join(todo)
        low = data.lower()
        marks = []
        for m in (b"unlock", b"achiev", b"trophy", b"saveversion", b"progress"):
            if m in low:
                marks.append(m.decode())
        print("   %-45s %8d  %s %s" % (rel, size, txt, ",".join(marks)))
