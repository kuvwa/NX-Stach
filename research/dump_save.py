import struct, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savedata.vfs")
s = open(p, "rb").read()

def dump(a, b, width=16):
    for off in range(a, b, width):
        chunk = s[off:off + width]
        hexs = " ".join("%02X" % c for c in chunk)
        asci = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        u32 = " ".join("%d" % v for v in struct.unpack_from("<%dI" % (len(chunk) // 4), s, off)) if len(chunk) >= 4 else ""
        print("%06X  %-47s  %-16s  %s" % (off, hexs, asci, u32))

print("===== таблица с шагом 8 (3992..4300) =====")
dump(3960, 4300)
print()
print("===== район 768..771 (15480..15620) =====")
dump(15480, 15620)
print()
print("===== блок флагов (106240..106400) =====")
dump(106240, 106400)
