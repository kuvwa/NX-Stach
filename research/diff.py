import sys, struct

d1 = open(sys.argv[1], 'rb').read()
d2 = open(sys.argv[2], 'rb').read()

print(f"Размер: {len(d1)} vs {len(d2)} байт")
print("Измененные блоки (Offset | Было | Стало):")

changes = 0
for i in range(0, min(len(d1), len(d2)), 4):
    v1 = struct.unpack_from('<I', d1, i)[0]
    v2 = struct.unpack_from('<I', d2, i)[0]
    if v1 != v2:
        changes += 1
        print(f"Offset 0x{i:06X} ({i}): {v1} -> {v2} (Hex: 0x{v1:08X} -> 0x{v2:08X})")

print(f"\nВсего измененных блоков: {changes}")
