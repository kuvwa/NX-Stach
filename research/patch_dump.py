import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- gamesave.h ----------
p = os.path.join(ROOT, "source", "gamesave.h")
s = open(p, encoding="utf-8").read()
if "gamesave_dump_to_sd" not in s:
    s = s.rstrip() + """

// Копирует сейв игры на SD: sdmc:/switch/NX-Stach/dumps/<titleid>/
// Возвращает число скопированных файлов.
int gamesave_dump_to_sd(u64 title_id);
"""
    open(p, "w", encoding="utf-8").write(s)
    print("gamesave.h ok")

# ---------- gamesave.c ----------
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

if "gamesave_dump_to_sd" not in s:
    s = s.replace("#include <string.h>", "#include <string.h>\n#include <sys/stat.h>", 1)

    s = s.rstrip() + r'''

static int dump_copy(FsFileSystem *fs, const char *src_dir, const char *dst_dir,
                     int depth, int *count)
{
    if (depth > 2) return 0;

    mkdir(dst_dir, 0777);

    FsDir dir;

    if (R_FAILED(fsFsOpenDirectory(fs, src_dir,
            FsDirOpenMode_ReadDirs | FsDirOpenMode_ReadFiles, &dir)))
        return 0;

    FsDirectoryEntry entries[64];
    int files = 0;

    while (true) {
        s64 got = 0;

        if (R_FAILED(fsDirRead(&dir, &got, 64, entries)) || got <= 0)
            break;

        for (s64 i = 0; i < got; i++) {
            char src[400];
            char dst[400];

            if (entries[i].type == FsDirEntryType_Dir) {
                snprintf(src, sizeof(src), "%.180s/%.60s", src_dir, entries[i].name);
                snprintf(dst, sizeof(dst), "%.180s/%.60s", dst_dir, entries[i].name);
                files += dump_copy(fs, src, dst, depth + 1, count);
                continue;
            }

            if (entries[i].file_size <= 0 ||
                entries[i].file_size > (4 * 1024 * 1024))
                continue;

            snprintf(src, sizeof(src), "%.180s/%.60s", src_dir, entries[i].name);
            snprintf(dst, sizeof(dst), "%.180s/%.60s", dst_dir, entries[i].name);

            size_t size = 0;
            u8 *data = gamesave_read_file(fs, src, &size);

            if (!data) continue;

            FILE *out = fopen(dst, "wb");

            if (out) {
                fwrite(data, 1, size, out);
                fclose(out);
                (*count)++;
                files++;
            }

            free(data);

            if (*count > 200) break;
        }

        if (got < 64) break;
    }

    fsDirClose(&dir);
    return files;
}

int gamesave_dump_to_sd(u64 title_id)
{
    FsFileSystem fs;

    if (!gamesave_open(title_id, &fs)) {
        last_error = "SAVE_OPEN";
        return -1;
    }

    mkdir("sdmc:/switch/NX-Stach", 0777);
    mkdir("sdmc:/switch/NX-Stach/dumps", 0777);

    char root[220];
    snprintf(root, sizeof(root), "sdmc:/switch/NX-Stach/dumps/%016llX",
             (unsigned long long)title_id);

    mkdir(root, 0777);

    int count = 0;
    dump_copy(&fs, "", root, 0, &count);

    gamesave_close(&fs);

    last_error = count > 0 ? "OK" : "EMPTY";
    return count;
}
'''
    open(p, "w", encoding="utf-8").write(s)
    print("gamesave.c ok")
