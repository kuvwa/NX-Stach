#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "gamesave.h"

#define MAX_VFS_SIZE (4 * 1024 * 1024)

static const char *last_error = "NOT_STARTED";
const char *gamesave_last_error(void) { return last_error; }

static bool find_save_attributes(u64 title_id, FsSaveDataSpaceId *space,
                                 FsSaveDataAttribute *attr)
{
    FsSaveDataInfoReader reader;
    Result rc = fsOpenSaveDataInfoReader(&reader, FsSaveDataSpaceId_All);
    if (R_FAILED(rc)) {
        last_error = "INFO_READER";
        return false;
    }

    FsSaveDataInfo entries[64];
    bool found = false;

    for (int page = 0; page < 256 && !found; page++) {
        s64 count = 0;

        rc = fsSaveDataInfoReaderRead(&reader, entries, 64, &count);
        if (R_FAILED(rc) || count <= 0)
            break;

        if (count > 64) count = 64;

        for (s64 i = 0; i < count; i++) {
            if (entries[i].application_id != title_id)
                continue;

            *space = (FsSaveDataSpaceId)entries[i].save_data_space_id;

            memset(attr, 0, sizeof(*attr));
            attr->application_id = entries[i].application_id;
            attr->uid = entries[i].uid;
            attr->save_data_type = entries[i].save_data_type;
            attr->save_data_rank = entries[i].save_data_rank;
            attr->save_data_index = entries[i].save_data_index;
            attr->system_save_data_id = entries[i].system_save_data_id;

            found = true;
            break;
        }

        if (count < 64)
            break;
    }

    fsSaveDataInfoReaderClose(&reader);

    if (!found)
        last_error = "SAVE_NOT_FOUND";

    return found;
}

bool gamesave_open(u64 title_id, FsFileSystem *fs)
{
    last_error = "NOT_STARTED";

    FsSaveDataSpaceId space;
    FsSaveDataAttribute attr;

    if (!find_save_attributes(title_id, &space, &attr))
        return false;

    if (R_FAILED(fsOpenReadOnlySaveDataFileSystem(fs, space, &attr))) {
        last_error = "SAVE_OPEN";
        return false;
    }

    return true;
}

void gamesave_close(FsFileSystem *fs)
{
    fsFsClose(fs);
}

u8 *gamesave_read_file(FsFileSystem *fs, const char *path, size_t *out_size)
{
    FsFile file;

    if (R_FAILED(fsFsOpenFile(fs, path, FsOpenMode_Read, &file))) {
        last_error = "FILE_OPEN";
        return NULL;
    }

    s64 file_size = 0;

    if (R_FAILED(fsFileGetSize(&file, &file_size)) || file_size <= 0 ||
        file_size > MAX_VFS_SIZE) {
        last_error = "FILE_SIZE";
        fsFileClose(&file);
        return NULL;
    }

    u8 *buffer = malloc((size_t)file_size);

    if (!buffer) {
        last_error = "OUT_OF_MEMORY";
        fsFileClose(&file);
        return NULL;
    }

    u64 offset = 0;

    while (offset < (u64)file_size) {
        u64 chunk = (u64)file_size - offset;
        if (chunk > 0x8000) chunk = 0x8000;

        u64 got = 0;

        if (R_FAILED(fsFileRead(&file, offset, buffer + offset,
                                chunk, 0, &got)) || got == 0) {
            last_error = "FILE_READ";
            free(buffer);
            fsFileClose(&file);
            return NULL;
        }

        offset += got;
    }

    fsFileClose(&file);

    *out_size = (size_t)file_size;
    return buffer;
}

static int parse_flags(const u8 *data, size_t size, int skip, int format,
                       u8 *flags, int max_flags)
{
    int count = 0;
    int seen = 0;

    if (format == 0) {
        for (size_t i = 0; i < size; i++) {
            if (data[i] != '0' && data[i] != '1')
                continue;

            if (seen++ < skip)
                continue;

            if (count >= max_flags)
                break;

            flags[count++] = (u8)(data[i] - '0');
        }
    } else {
        for (size_t i = 0; i < size; i++) {
            if (data[i] != 0 && data[i] != 1)
                continue;

            if (seen++ < skip)
                continue;

            if (count >= max_flags)
                break;

            flags[count++] = data[i];
        }
    }

    return count;
}

int gamesave_read_block(u64 title_id, const char *file_path, const char *marker,
                        int offset, int skip, int format,
                        u8 *flags, int max_flags)
{
    last_error = "NOT_STARTED";

    if (!file_path || !flags || max_flags <= 0) {
        last_error = "ARGUMENT";
        return -1;
    }

    FsFileSystem fs;

    if (!gamesave_open(title_id, &fs))
        return -1;

    size_t size = 0;
    u8 *data = gamesave_read_file(&fs, file_path, &size);

    gamesave_close(&fs);

    if (!data)
        return -1;

    size_t start = (size_t)offset;

    if (marker && marker[0]) {
        size_t mlen = strlen(marker);
        size_t pos = (size_t)-1;

        for (size_t i = 0; i + mlen < size; i++) {
            if (memcmp(data + i, marker, mlen) == 0) {
                pos = i;
                break;
            }
        }

        if (pos == (size_t)-1) {
            last_error = "MARKER_NOT_FOUND";
            free(data);
            return -1;
        }

        start = pos + mlen;

        if (start + 4 > size) {
            last_error = "TRUNCATED";
            free(data);
            return -1;
        }

        u32 block_size = 0;
        memcpy(&block_size, data + start, sizeof(block_size));

        if ((size_t)block_size > size - start - 4 || block_size == 0) {
            last_error = "BAD_SIZE";
            free(data);
            return -1;
        }

        start += 4;
        size = start + block_size;
    }

    if (start >= size) {
        last_error = "OFFSET";
        free(data);
        return -1;
    }

    int count = parse_flags(data + start, size - start, skip, format,
                            flags, max_flags);

    free(data);

    last_error = count > 0 ? "OK" : "PARSE";
    return count > 0 ? count : -1;
}

int gamesave_read_named(u64 title_id, const char *file_path,
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

int gamesave_read_unlocked(u64 title_id, const char *base_path,
                           u8 *flags, int max_flags)
{
    char path[256];
    snprintf(path, sizeof(path), "%s/savedata.vfs", base_path);

    return gamesave_read_block(title_id, path, "unlocked_achievements.dat",
                               0, 1, 0, flags, max_flags);
}

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
                snprintf(child, sizeof(child), "%.200s/%.200s", path, entries[i].name);
                dump_dir(fs, child, depth + 1, out);
            }
        }

        if (got < 64) break;
    }

    fsDirClose(&dir);
}

void gamesave_dump_tree(u64 title_id)
{
    FsFileSystem fs;

    if (!gamesave_open(title_id, &fs))
        return;

    FILE *out = fopen("sdmc:/switch/NX-Stach/save_tree.txt", "w");

    if (out) {
        fprintf(out, "TITLE %016llX\n", (unsigned long long)title_id);
        dump_dir(&fs, "/", 0, out);
        fclose(out);
    }

    gamesave_close(&fs);
}

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

            if (strcmp(src_dir, "/") == 0)
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
                continue;

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

// Перечисляет ВСЕ сейв-контейнеры игры и копирует каждый на SD.
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
    int matched = 0;

    char rpath[300];
    snprintf(rpath, sizeof(rpath), "%s/report.txt", root);
    FILE *report = fopen(rpath, "w");

    for (int page = 0; page < 64; page++) {
        s64 got = 0;

        if (R_FAILED(fsSaveDataInfoReaderRead(&reader, entries, 64, &got)) || got <= 0)
            break;

        for (s64 i = 0; i < got; i++) {
            if (entries[i].application_id != title_id)
                continue;

            matched++;

            if (report)
                fprintf(report, "container save_id=%016llX idx=%u type=%u\n",
                        (unsigned long long)entries[i].save_data_id,
                        (unsigned)entries[i].save_data_index,
                        (unsigned)entries[i].save_data_type);

            FsSaveDataAttribute attr;
            memset(&attr, 0, sizeof(attr));

            attr.application_id = entries[i].application_id;
            attr.uid = entries[i].uid;
            attr.save_data_type = entries[i].save_data_type;
            attr.save_data_rank = entries[i].save_data_rank;
            attr.save_data_index = entries[i].save_data_index;
            attr.system_save_data_id = entries[i].system_save_data_id;

            FsFileSystem fs;

            Result open_rc = fsOpenReadOnlySaveDataFileSystem(
                    &fs, (FsSaveDataSpaceId)entries[i].save_data_space_id, &attr);

            if (R_FAILED(open_rc)) {
                if (report)
                    fprintf(report, "  open failed: 0x%08X\n", (unsigned)open_rc);
                continue;
            }

            char dir[280];
            snprintf(dir, sizeof(dir), "%s/%016llX", root,
                     (unsigned long long)entries[i].save_data_id);

            mkdir(dir, 0777);

            int before = count;
            dump_copy(&fs, "/", dir, 0, &count);

            if (report)
                fprintf(report, "  dir=%s files=%d\n", dir, count - before);

            fsFsClose(&fs);
            containers++;
        }

        if (got < 64) break;
    }

    fsSaveDataInfoReaderClose(&reader);

    if (report) {
        fprintf(report, "title=%016llX matched=%d containers=%d files=%d\n",
                (unsigned long long)title_id, matched, containers, count);
        fclose(report);
    }

    last_error = count > 0 ? "OK" : "EMPTY";

    if (count == 0) return -1;

    return count;
}
