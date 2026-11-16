import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

# вырезаем блок формата 3 из старого места
start = s.find("    if (format == 3) {")
end = s.find("    if (start >= size) {", start)

if start < 0 or end < 0:
    raise SystemExit("format3 block not found")

s = s[:start] + s[end:]

# вставляем сразу после чтения файла — до разбора маркера
anchor = """    gamesave_close(&fs);

    if (!data)
        return -1;
"""

new = anchor + """
    if (format == 3) {
        size_t mlen = marker ? strlen(marker) : 0;
        size_t pos = (size_t)-1;

        if (mlen == 0) {
            last_error = "ARGUMENT";
            free(data);
            return -1;
        }

        for (size_t i = 0; i + mlen < size; i++) {
            if (memcmp(data + i, marker, mlen) == 0) {
                pos = i + mlen;
                break;
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
        int bits = max_flags < 32 ? max_flags : 32;

        for (int i = 0; i < bits; i++)
            flags[i] = (u8)((mask >> i) & 1);

        free(data);
        last_error = "OK";
        return bits;
    }
"""

if anchor not in s:
    raise SystemExit("anchor not found")

s = s.replace(anchor, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
