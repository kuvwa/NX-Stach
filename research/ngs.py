import os

ROOT = r"C:\Users\kuvwa\NX-Stach\inbox\dumps\0100E2F014F46000"

def find01(data, want, tol=2):
    res = []
    n = len(data)
    i = 0
    while i < n:
        if data[i] <= 1:
            st = i
            c = 0
            ones = 0
            while i < n and data[i] <= 1:
                if data[i]:
                    ones += 1
                c += 1
                i += 1
            if abs(c - want) <= tol:
                res.append((st, c, ones))
        else:
            i += 1
    return res

for base, _, names in os.walk(ROOT):
    for n in names:
        if n == "report.txt":
            continue
        p = os.path.join(base, n)
        d = open(p, "rb").read()

        has_ngs = b"NGS_" in d or b"ACHIEV" in d
        runs = find01(d, 51, 1)
        runs32 = find01(d, 4, 0)  # мусор, не нужно

        print("%-45s %8d  NGS=%s  51-run=%s" % (
            os.path.relpath(p, ROOT), len(d), has_ngs, runs[:3]))
