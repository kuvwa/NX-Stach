import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- gamesave.c: формат 3 (битовая маска из INI) ----------
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

anchor = """    if (start >= size) {
        last_error = "OFFSET";
        free(data);
        return -1;
    }"""

add = """    if (format == 3) {
        // marker = ключ, после которого число-битмаска
        size_t mlen = marker ? strlen(marker) : 0;
        size_t pos = (size_t)-1;

        if (mlen > 0) {
            for (size_t i = 0; i + mlen < size; i++) {
                if (memcmp(data + i, marker, mlen) == 0) {
                    pos = i + mlen;
                    break;
                }
            }
        }

        if (pos == (size_t)-1) {
            last_error = "MARKER_NOT_FOUND";
            free(data);
            return -1;
        }

        while (pos < size && (data[pos] == ' ' || data[pos] == '\\t'))
            pos++;

        unsigned long mask = strtoul((const char *)data + pos, NULL, 10);
        int bits = 0;

        for (int i = 0; i < max_flags; i++) {
            flags[i] = (u8)((mask >> i) & 1);
            bits++;
        }

        free(data);
        last_error = "OK";
        return bits;
    }

"""

if anchor not in s:
    raise SystemExit("anchor not found")

s = s.replace(anchor, add + anchor, 1)
open(p, "w", encoding="utf-8").write(s)
print("gamesave format3 ok")

# ---------- library.c: Downwell ----------
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

old = """static const Variant VARIANTS[] = {
    { 0x0100D0E00E51E000ULL, "Hotline Miami", "219150" },
    { 0x0100D0E00E51E000ULL, "Hotline Miami 2: Wrong Number", "274170" },
};"""

new = """static const Variant VARIANTS[] = {
    { 0x0100D0E00E51E000ULL, "Hotline Miami", "219150" },
    { 0x0100D0E00E51E000ULL, "Hotline Miami 2: Wrong Number", "274170" },
    { 0x010093D00C726000ULL, "Downwell", "360740" },
};"""

if old not in s:
    raise SystemExit("variants not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("variants ok")
