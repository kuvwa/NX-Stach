import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


rep("""    FsSaveDataInfo entries[64];
    int count = 0;
    int containers = 0;""",
    """    FsSaveDataInfo entries[64];
    int count = 0;
    int containers = 0;
    int matched = 0;

    char rpath[300];
    snprintf(rpath, sizeof(rpath), "%s/report.txt", root);
    FILE *report = fopen(rpath, "w");""")

rep("""            if (entries[i].application_id != title_id)
                continue;""",
    """            if (entries[i].application_id != title_id)
                continue;

            matched++;

            if (report)
                fprintf(report, "container app=%016llX save_id=%016llX idx=%u type=%u\\n",
                        (unsigned long long)entries[i].application_id,
                        (unsigned long long)entries[i].save_data_id,
                        (unsigned)entries[i].save_data_index,
                        (unsigned)entries[i].save_data_type);""")

rep("""            if (R_FAILED(fsOpenReadOnlySaveDataFileSystem(
                    &fs, (FsSaveDataSpaceId)entries[i].save_data_space_id, &attr)))
                continue;""",
    """            Result open_rc = fsOpenReadOnlySaveDataFileSystem(
                    &fs, (FsSaveDataSpaceId)entries[i].save_data_space_id, &attr);

            if (R_FAILED(open_rc)) {
                if (report)
                    fprintf(report, "  open failed: 0x%08X\\n", (unsigned)open_rc);
                continue;
            }""")

rep("""            dump_copy(&fs, "/", dir, 0, &count);""",
    """            int before = count;
            dump_copy(&fs, "/", dir, 0, &count);

            if (report)
                fprintf(report, "  dir=%s files=%d\\n", dir, count - before);""")

rep("""    fsSaveDataInfoReaderClose(&reader);

    last_error = count > 0 ? "OK" : "EMPTY";""",
    """    fsSaveDataInfoReaderClose(&reader);

    if (report) {
        fprintf(report, "title=%016llX matched=%d containers=%d files=%d\\n",
                (unsigned long long)title_id, matched, containers, count);
        fclose(report);
    }

    last_error = count > 0 ? "OK" : "EMPTY";""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
