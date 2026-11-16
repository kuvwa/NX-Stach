import struct, os, re

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savedata.vfs")
s = open(p, "rb").read()
print("size:", len(s))

# 1) есть ли в сейве internal_key достижений (257..287, 768..771) как LE u32
keys = list(range(257, 288)) + list(range(768, 772))
hits = {}
for k in keys:
    pos = []
    start = 0
    pat = struct.pack("<I", k)
    while True:
        i = s.find(pat, start)
        if i < 0:
            break
        pos.append(i)
        start = i + 1
    if pos:
        hits[k] = pos

print("\nключи найденные в файле:")
for k in sorted(hits):
    print("  key", k, "offsets", hits[k][:8], "count", len(hits[k]))

# 2) ищем последовательность подряд идущих ключей
seq = struct.calcsize("<I")
best = None
for k in range(257, 288):
    for off in hits.get(k, [])[:4]:
        n = 1
        while struct.unpack_from("<I", s, off + n * seq)[0] == k + n:
            n += 1
        if n >= 3 and (best is None or n > best[2]):
            best = (off, k, n)
print("\nсамая длинная последовательность ключей:", best)

# 3) где находятся 35 флагов (ASCII '0'/'1' + \n)
for m in re.finditer(rb"(?:[01]\n){30,}", s):
    print("\nflag-block at", m.start(), "len", len(m.group(0)))
    print("  values:", [chr(c) for c in m.group(0) if c in (0x30, 0x31)])
