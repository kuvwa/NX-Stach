import os, struct

ROOT = r"C:\Users\kuvwa\NX-Stach\inbox\dumps"
p = os.path.join(ROOT, "0100D0E00E51E000", "0000000000000070", "HotlineMiami2", "savedata.vfs")
d = open(p, "rb").read()
print("size", len(d))
print("first 64:", d[:64].hex(" "))

# ищем все вхождения читаемых имён и что после них
i = 0
while i < len(d) - 8:
    if 32 <= d[i] < 127:
        j = i
        while j < len(d) and 32 <= d[j] < 127:
            j += 1
        name = d[i:j].decode("ascii")
        if len(name) >= 4:
            after = d[j:j+8]
            nxt = struct.unpack_from("<I", d, j)[0] if j + 4 <= len(d) else 0
            print("%6d  %-40s next_u32=%d (0x%X) bytes=%s" % (i, name, nxt, nxt, after.hex(" ")))
        i = j
    else:
        i += 1
