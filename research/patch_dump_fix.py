import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# корректная склейка путей внутри сейва
rep("""            if (entries[i].type == FsDirEntryType_Dir) {
                snprintf(src, sizeof(src), "%.180s/%.60s", src_dir, entries[i].name);
                snprintf(dst, sizeof(dst), "%.180s/%.60s", dst_dir, entries[i].name);
                files += dump_copy(fs, src, dst, depth + 1, count);
                continue;
            }

            if (entries[i].file_size <= 0 ||
                entries[i].file_size > (4 * 1024 * 1024))
                continue;

            snprintf(src, sizeof(src), "%.180s/%.60s", src_dir, entries[i].name);
            snprintf(dst, sizeof(dst), "%.180s/%.60s", dst_dir, entries[i].name);""",
    """            if (strcmp(src_dir, "/") == 0)
                snprintf(src, sizeof(src), "/%.120s", entries[i].name);
            else
                snprintf(src, sizeof(src), "%.180s/%.60s", src_dir, entries[i].name);

            snprintf(dst, sizeof(dst), "%.180s/%.60s", dst_dir, entries[i].name);

            if (entries[i].type == FsDirEntryType_Dir) {
                files += dump_copy(fs, src, dst, depth + 1, count);
                continue;
            }

            if (entries[i].file_size <= 0 ||
                entries[i].file_size > (4 * 1024 * 1024))
                continue;""")

# старт с корня
rep("""            dump_copy(&fs, "", dir, 0, &count);""",
    """            dump_copy(&fs, "/", dir, 0, &count);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
