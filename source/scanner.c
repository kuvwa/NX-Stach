#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "scanner.h"
#include "gamesave.h"
#include "recipe.h"

#define MAX_FILES 96
#define MAX_FILE_SIZE (2 * 1024 * 1024)

typedef struct {
    char path[128];
    int size;
} FileEntry;

static int collect_files(FsFileSystem *fs, const char *dir_path,
                         FileEntry *out, int max, int depth)
{
    if (depth > 2) return 0;

    FsDir dir;

    if (R_FAILED(fsFsOpenDirectory(fs, dir_path,
            FsDirOpenMode_ReadDirs | FsDirOpenMode_ReadFiles, &dir)))
        return 0;

    FsDirectoryEntry entries[64];
    int count = 0;
    s64 total = 0;

    while (true) {
        s64 got = 0;

        if (R_FAILED(fsDirRead(&dir, &got, 64, entries)) || got <= 0)
            break;

        total += got;
        if (total > 256) break;

        for (s64 i = 0; i < got; i++) {
            char full[160];

            if (entries[i].type == FsDirEntryType_Dir) {
                snprintf(full, sizeof(full), "%.100s/%.40s", dir_path, entries[i].name);
                count += collect_files(fs, full, out + count, max - count, depth + 1);
                if (count >= max) break;
            } else {
                if (entries[i].file_size <= 0 ||
                    entries[i].file_size > MAX_FILE_SIZE)
                    continue;

                if (count >= max) break;

                snprintf(out[count].path, sizeof(out[count].path), "%.100s/%.40s",
                         dir_path, entries[i].name);
                out[count].size = (int)entries[i].file_size;
                count++;
            }
        }

        if (got < 64) break;
    }

    fsDirClose(&dir);
    return count;
}

// Ищем блок из ожидаемого числа «0»/«1» (с переводами строк между ними).
static bool find_ascii01(const u8 *data, size_t size, int expected,
                         int *out_offset, int *out_count, int *out_unlocked)
{
    size_t i = 0;
    bool best_found = false;
    int best_count = 0;
    int best_offset = 0;
    int best_unlocked = 0;

    while (i < size) {
        if (data[i] != '0' && data[i] != '1') {
            i++;
            continue;
        }

        size_t start = i;
        int digits = 0;
        int unlocked = 0;

        while (i < size) {
            if (data[i] == '0' || data[i] == '1') {
                if (data[i] == '1') unlocked++;
                digits++;
                i++;

                while (i < size && (data[i] == '\n' || data[i] == '\r' ||
                                    data[i] == ' ' || data[i] == ','))
                    i++;
            } else {
                break;
            }
        }

        if (digits > best_count) {
            best_count = digits;
            best_offset = (int)start;
            best_unlocked = unlocked;
            best_found = true;
        }
    }

    if (!best_found || best_count < 4)
        return false;

    if (best_count < expected - 2 || best_count > expected + 2)
        return false;

    *out_offset = best_offset;
    *out_count = best_count;
    *out_unlocked = best_unlocked;
    return true;
}

// Ищем блок байтов 0/1.
static bool find_raw01(const u8 *data, size_t size, int expected,
                       int *out_offset, int *out_count, int *out_unlocked)
{
    size_t i = 0;
    int best_count = 0, best_offset = 0, best_unlocked = 0;
    bool found = false;

    while (i < size) {
        if (data[i] > 1) {
            i++;
            continue;
        }

        size_t start = i;
        int count = 0, unlocked = 0;

        while (i < size && data[i] <= 1) {
            if (data[i]) unlocked++;
            count++;
            i++;
        }

        if (count > best_count) {
            best_count = count;
            best_offset = (int)start;
            best_unlocked = unlocked;
            found = true;
        }
    }

    if (!found || best_count < 4)
        return false;

    if (best_count < expected - 2 || best_count > expected + 2)
        return false;

    *out_offset = best_offset;
    *out_count = best_count;
    *out_unlocked = best_unlocked;
    return true;
}

// Ищем «имя файла + u32 длина + блок флагов» (как в Hotline Miami).
static bool find_marker_block(const u8 *data, size_t size, int expected,
                              char *out_marker, size_t marker_size,
                              int *out_count, int *out_unlocked)
{
    for (size_t i = 0; i + 8 < size; i++) {
        if (!isprint(data[i]))
            continue;

        // длина имени
        size_t len = 0;
        while (i + len < size && len < 63 && isprint(data[i + len]) &&
               data[i + len] != ' ')
            len++;

        if (len < 4)
            continue;

        if (memchr(data + i, '.', len) == NULL)
            continue;

        size_t after = i + len;

        if (after + 4 > size)
            continue;

        u32 block = 0;
        memcpy(&block, data + after, 4);

        if (block < (u32)expected - 2 || block > (u32)expected * 2 + 64)
            continue;

        if (after + 4 + block > size)
            continue;

        int offset = 0, count = 0, unlocked = 0;

        if (find_ascii01(data + after + 4, block, expected,
                         &offset, &count, &unlocked)) {
            snprintf(out_marker, marker_size, "%.*s", (int)len, (const char *)(data + i));
            *out_count = count;
            *out_unlocked = unlocked;
            return true;
        }
    }

    return false;
}

ScanResult scan_save_for_achievements(u64 title_id, int expected_count,
                                      const char **names, int name_count)
{
    ScanResult res;
    memset(&res, 0, sizeof(res));

    if (expected_count <= 0) {
        snprintf(res.note, sizeof(res.note), "Нет каталога достижений");
        return res;
    }

    FsFileSystem fs;

    if (!gamesave_open(title_id, &fs)) {
        snprintf(res.note, sizeof(res.note), "Сейв не найден: %s",
                 gamesave_last_error());
        return res;
    }

    FileEntry *files = calloc(MAX_FILES, sizeof(FileEntry));
    int count = files ? collect_files(&fs, "", files, MAX_FILES, 0) : 0;

    int best_score = 0;

    for (int f = 0; f < count; f++) {
        size_t size = 0;
        u8 *data = gamesave_read_file(&fs, files[f].path, &size);

        if (!data) continue;

        int offset = 0, digits = 0, unlocked = 0;
        char marker[64] = "";

        // 1) контейнер: имя + длина + флаги
        if (find_marker_block(data, size, expected_count, marker,
                              sizeof(marker), &digits, &unlocked)) {
            int score = 90;

            if (digits == expected_count || digits == expected_count + 1)
                score = 100;

            if (score > best_score) {
                best_score = score;
                res.found = true;
                res.confidence = score;
                snprintf(res.file_path, sizeof(res.file_path), "%s", files[f].path);
                snprintf(res.marker, sizeof(res.marker), "%s", marker);
                res.offset = 0;
                res.skip = (digits == expected_count + 1) ? 1 : 0;

                {
                    char low[64];
                    size_t k = 0;

                    for (; marker[k] && k < sizeof(low) - 1; k++)
                        low[k] = (char)((marker[k] >= 'A' && marker[k] <= 'Z')
                                        ? marker[k] + 32 : marker[k]);
                    low[k] = '\0';

                    if (strstr(low, "unlock"))
                        res.skip = 1;
                }

                res.format = 0;
                res.count = digits;
                res.unlocked = unlocked;
                snprintf(res.note, sizeof(res.note),
                         "Маркер «%s», %d флагов", marker, digits);
            }
        }

        // 2) просто блок ASCII 0/1
        if (find_ascii01(data, size, expected_count, &offset, &digits, &unlocked)) {
            int score = (digits == expected_count || digits == expected_count + 1)
                        ? 80 : 60;

            if (score > best_score) {
                best_score = score;
                res.found = true;
                res.confidence = score;
                snprintf(res.file_path, sizeof(res.file_path), "%s", files[f].path);
                res.marker[0] = '\0';
                res.offset = offset;
                res.skip = (digits == expected_count + 1) ? 1 : 0;
                res.format = 0;
                res.count = digits;
                res.unlocked = unlocked;
                snprintf(res.note, sizeof(res.note),
                         "ASCII-флаги, %d штук", digits);
            }
        }

        // 2б) имена достижений прямо в файле (Unity / JSON сейвы)
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
                    res.marker[0] = '\0';
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

        // 3) блок байтов 0/1
        if (find_raw01(data, size, expected_count, &offset, &digits, &unlocked)) {
            int score = (digits == expected_count) ? 70 : 50;

            if (score > best_score) {
                best_score = score;
                res.found = true;
                res.confidence = score;
                snprintf(res.file_path, sizeof(res.file_path), "%s", files[f].path);
                res.marker[0] = '\0';
                res.offset = offset;
                res.skip = 0;
                res.format = 1;
                res.count = digits;
                res.unlocked = unlocked;
                snprintf(res.note, sizeof(res.note),
                         "Байтовые флаги, %d штук", digits);
            }
        }

        free(data);
    }

    free(files);
    gamesave_close(&fs);

    if (!res.found)
        snprintf(res.note, sizeof(res.note), "Флаги достижений не найдены");

    return res;
}
