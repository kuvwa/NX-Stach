import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s:\n%s" % (path, old[:160]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


# ---------- scanner.h ----------
patch("source/scanner.h", [
("""ScanResult scan_save_for_achievements(u64 title_id, int expected_count);""",
 """ScanResult scan_save_for_achievements(u64 title_id, int expected_count,
                                      const char **names, int name_count);"""),
])

# ---------- recipe.h ----------
patch("source/recipe.h", [
("""// Читает флаги по рецепту. Возвращает число флагов или -1.
int recipe_read_flags(const Recipe *r, u8 *flags, int max_flags);""",
 """// Читает флаги по рецепту. names — внутренние имена достижений
// (нужны для формата 2 «по именам»). Возвращает число флагов или -1.
int recipe_read_flags(const Recipe *r, const char **names, int name_count,
                      u8 *flags, int max_flags);"""),
])

# ---------- recipe.c ----------
patch("source/recipe.c", [
("""int recipe_read_flags(const Recipe *r, u8 *flags, int max_flags)
{
    if (!r || !r->valid)
        return -1;

    return gamesave_read_block(r->title_id, r->file_path, r->marker,
                               r->offset, r->skip, r->format,
                               flags, max_flags);
}""",
 """int recipe_read_flags(const Recipe *r, const char **names, int name_count,
                      u8 *flags, int max_flags)
{
    if (!r || !r->valid)
        return -1;

    if (r->format == 2)
        return gamesave_read_named(r->title_id, r->file_path, names, name_count,
                                   r->offset, flags, max_flags);

    return gamesave_read_block(r->title_id, r->file_path, r->marker,
                               r->offset, r->skip, r->format,
                               flags, max_flags);
}"""),
])

# ---------- gamesave.h: чтение «по именам» ----------
patch("source/gamesave.h", [
("""// Старое поведение (Hotline Miami), оставлено для совместимости.""",
 """// Формат «по именам»: ищет название достижения и рядом байт 0/1.
// offset — окно поиска после имени.
int gamesave_read_named(u64 title_id, const char *file_path,
                        const char **names, int name_count,
                        int window, u8 *flags, int max_flags);

// Старое поведение (Hotline Miami), оставлено для совместимости."""),
])

# ---------- gamesave.c: реализация ----------
patch("source/gamesave.c", [
("""int gamesave_read_unlocked(u64 title_id, const char *base_path,""",
 """int gamesave_read_named(u64 title_id, const char *file_path,
                        const char **names, int name_count,
                        int window, u8 *flags, int max_flags)
{
    last_error = "NOT_STARTED";

    if (!file_path || !names || name_count <= 0 || !flags)
        return -1;

    if (window <= 0) window = 96;

    FsFileSystem fs;

    if (!gamesave_open(title_id, &fs))
        return -1;

    size_t size = 0;
    u8 *data = gamesave_read_file(&fs, file_path, &size);

    gamesave_close(&fs);

    if (!data)
        return -1;

    int found = 0;

    for (int i = 0; i < name_count && i < max_flags; i++) {
        const char *name = names[i];

        if (!name || !name[0]) continue;

        size_t nlen = strlen(name);
        size_t pos = (size_t)-1;

        for (size_t k = 0; k + nlen < size; k++) {
            if (memcmp(data + k, name, nlen) == 0) {
                pos = k + nlen;
                break;
            }
        }

        if (pos == (size_t)-1) {
            flags[i] = 0;
            continue;
        }

        int value = 0;

        for (size_t k = pos; k < pos + (size_t)window && k < size; k++) {
            if (data[k] == 1 || data[k] == '1') { value = 1; break; }
            if (data[k] == 0 || data[k] == '0') { value = 0; break; }
        }

        flags[i] = (u8)value;
        found++;
    }

    free(data);

    last_error = found > 0 ? "OK" : "PARSE";
    return found > 0 ? name_count : -1;
}

int gamesave_read_unlocked(u64 title_id, const char *base_path,"""),
])
