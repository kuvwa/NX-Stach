#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

static u8 *read_whole_file(FsFileSystem *fs, const char *path, size_t *out_size)
{
    FsFile file;

    if (R_FAILED(fsFsOpenFile(fs, path, FsOpenMode_Read, &file))) {
        last_error = "VFS_OPEN";
        return NULL;
    }

    s64 file_size = 0;

    if (R_FAILED(fsFileGetSize(&file, &file_size)) || file_size <= 0 ||
        file_size > MAX_VFS_SIZE) {
        last_error = "VFS_SIZE";
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
            last_error = "VFS_READ";
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

static int parse_flags(const u8 *data, size_t size, u8 *flags, int max_flags)
{
    int count = 0;

    for (size_t i = 0; i < size && count < max_flags; i++) {
        if (data[i] == '0' || data[i] == '1') {
            flags[count++] = (u8)(data[i] - '0');
        } else if (data[i] == '\n' || data[i] == '\r' || data[i] == 0) {
            continue;
        } else {
            break;
        }
    }

    return count;
}

int gamesave_read_unlocked(u64 title_id, const char *base_path,
                           u8 *flags, int max_flags)
{
    last_error = "NOT_STARTED";

    if (!flags || max_flags <= 0 || !base_path) {
        last_error = "ARGUMENT";
        return -1;
    }

    FsSaveDataSpaceId space;
    FsSaveDataAttribute attr;

    if (!find_save_attributes(title_id, &space, &attr))
        return -1;

    FsFileSystem save_fs;

    if (R_FAILED(fsOpenReadOnlySaveDataFileSystem(&save_fs, space, &attr))) {
        last_error = "SAVE_OPEN";
        return -1;
    }

    char path[256];
    snprintf(path, sizeof(path), "%s/savedata.vfs", base_path);

    size_t vfs_size = 0;
    u8 *vfs = read_whole_file(&save_fs, path, &vfs_size);

    fsFsClose(&save_fs);

    if (!vfs)
        return -1;

    const char *marker = "unlocked_achievements.dat";
    const size_t marker_len = strlen(marker);
    u8 *found = NULL;

    for (size_t i = 0; i + marker_len < vfs_size; i++) {
        if (memcmp(vfs + i, marker, marker_len) == 0) {
            found = vfs + i + marker_len;
            break;
        }
    }

    if (!found) {
        last_error = "MARKER_NOT_FOUND";
        free(vfs);
        return -1;
    }

    size_t offset = (size_t)(found - vfs);

    if (offset + 4 > vfs_size) {
        last_error = "TRUNCATED";
        free(vfs);
        return -1;
    }

    u32 data_size = 0;
    memcpy(&data_size, vfs + offset, sizeof(data_size));

    if ((size_t)data_size > vfs_size - offset - 4 || data_size == 0) {
        last_error = "BAD_SIZE";
        free(vfs);
        return -1;
    }

    int count = parse_flags(vfs + offset + 4, data_size, flags, max_flags);

    free(vfs);

    if (count <= 0) {
        last_error = "PARSE";
        return -1;
    }

    last_error = "OK";
    return count;
}
