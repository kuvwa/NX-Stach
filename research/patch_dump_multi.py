import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

old_start = s.find("int gamesave_dump_to_sd(u64 title_id)")
if old_start < 0:
    raise SystemExit("dump function not found")

new_impl = r'''// Перечисляет ВСЕ сейв-контейнеры игры и копирует каждый на SD.
int gamesave_dump_to_sd(u64 title_id)
{
    FsSaveDataInfoReader reader;

    if (R_FAILED(fsOpenSaveDataInfoReader(&reader, FsSaveDataSpaceId_All))) {
        last_error = "INFO_READER";
        return -1;
    }

    mkdir("sdmc:/switch/NX-Stach", 0777);
    mkdir("sdmc:/switch/NX-Stach/dumps", 0777);

    char root[220];
    snprintf(root, sizeof(root), "sdmc:/switch/NX-Stach/dumps/%016llX",
             (unsigned long long)title_id);

    mkdir(root, 0777);

    FsSaveDataInfo entries[64];
    int count = 0;
    int containers = 0;

    for (int page = 0; page < 64; page++) {
        s64 got = 0;

        if (R_FAILED(fsSaveDataInfoReaderRead(&reader, entries, 64, &got)) || got <= 0)
            break;

        for (s64 i = 0; i < got; i++) {
            if (entries[i].application_id != title_id)
                continue;

            FsSaveDataAttribute attr;
            memset(&attr, 0, sizeof(attr));

            attr.application_id = entries[i].application_id;
            attr.uid = entries[i].uid;
            attr.save_data_type = entries[i].save_data_type;
            attr.save_data_rank = entries[i].save_data_rank;
            attr.save_data_index = entries[i].save_data_index;
            attr.system_save_data_id = entries[i].system_save_data_id;

            FsFileSystem fs;

            if (R_FAILED(fsOpenReadOnlySaveDataFileSystem(
                    &fs, (FsSaveDataSpaceId)entries[i].save_data_space_id, &attr)))
                continue;

            char dir[280];
            snprintf(dir, sizeof(dir), "%s/%016llX", root,
                     (unsigned long long)entries[i].save_data_id);

            mkdir(dir, 0777);

            dump_copy(&fs, "", dir, 0, &count);

            fsFsClose(&fs);
            containers++;
        }

        if (got < 64) break;
    }

    fsSaveDataInfoReaderClose(&reader);

    last_error = count > 0 ? "OK" : "EMPTY";

    if (count == 0) return -1;

    return count;
}
'''

s = s[:old_start] + new_impl
open(p, "w", encoding="utf-8").write(s)
print("ok")
