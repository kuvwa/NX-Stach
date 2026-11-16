import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

addition = r'''
static void dump_dir(FsFileSystem *fs, const char *path, int depth, FILE *out)
{
    if (depth > 3) return;

    FsDir dir;

    if (R_FAILED(fsFsOpenDirectory(fs, path,
            FsDirOpenMode_ReadDirs | FsDirOpenMode_ReadFiles, &dir)))
        return;

    FsDirectoryEntry entries[64];
    s64 total = 0;

    while (true) {
        s64 got = 0;

        if (R_FAILED(fsDirRead(&dir, &got, 64, entries)) || got <= 0)
            break;

        total += got;
        if (total > 512) break;

        for (s64 i = 0; i < got; i++) {
            bool is_dir = entries[i].type == FsDirEntryType_Dir;

            for (int d = 0; d < depth; d++) fprintf(out, "  ");

            fprintf(out, "%s %s %lld\n",
                    is_dir ? "D" : "F", entries[i].name,
                    (long long)entries[i].file_size);

            if (is_dir) {
                char child[512];
                snprintf(child, sizeof(child), "%s/%s", path, entries[i].name);
                dump_dir(fs, child, depth + 1, out);
            }
        }

        if (got < 64) break;
    }

    fsDirClose(&dir);
}

void gamesave_dump_tree(u64 title_id)
{
    FsSaveDataSpaceId space;
    FsSaveDataAttribute attr;

    if (!find_save_attributes(title_id, &space, &attr))
        return;

    FsFileSystem fs;

    if (R_FAILED(fsOpenReadOnlySaveDataFileSystem(&fs, space, &attr)))
        return;

    FILE *out = fopen("sdmc:/switch/NX-Stach/save_tree.txt", "w");

    if (out) {
        fprintf(out, "TITLE %016llX\n", (unsigned long long)title_id);
        dump_dir(&fs, "/", 0, out);
        fclose(out);
    }

    fsFsClose(&fs);
}
'''

s = s.rstrip() + "\n" + addition
open(p, "w", encoding="utf-8").write(s)
print("ok")
