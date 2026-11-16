import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "scanner.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:160])
    s = s.replace(old, new, 1)


rep("""ScanResult scan_save_for_achievements(u64 title_id, int expected_count)
{""",
    """ScanResult scan_save_for_achievements(u64 title_id, int expected_count,
                                      const char **names, int name_count)
{""")

# детектор «по именам достижений» + вызов
rep("""        // 3) блок байтов 0/1""",
    """        // 2б) имена достижений прямо в файле (Unity / JSON сейвы)
        if (names && name_count > 0) {
            int found_names = 0;

            for (int n = 0; n < name_count; n++) {
                if (!names[n] || !names[n][0]) continue;

                size_t nlen = strlen(names[n]);
                if (nlen < 4) continue;

                for (size_t k = 0; k + nlen < size; k++) {
                    if (memcmp(data + k, names[n], nlen) == 0) {
                        found_names++;
                        break;
                    }
                }
            }

            if (found_names >= 4 &&
                found_names * 100 >= expected_count * 55) {
                int score = found_names * 100 / expected_count;

                if (score > 90) score = 90;

                if (score > best_score) {
                    best_score = score;
                    res.found = true;
                    res.confidence = score;
                    snprintf(res.file_path, sizeof(res.file_path), "%s",
                             files[f].path);
                    res.marker[0] = '\\0';
                    res.offset = 96;
                    res.skip = 0;
                    res.format = 2;
                    res.count = expected_count;
                    res.unlocked = 0;
                    snprintf(res.note, sizeof(res.note),
                             "Имена достижений в сейве: %d из %d",
                             found_names, expected_count);
                }
            }
        }

        // 3) блок байтов 0/1""")

open(p, "w", encoding="utf-8").write(s)
print("scanner ok")
