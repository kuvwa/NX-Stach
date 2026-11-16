#include <switch.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "steam.h"
#include "save.h"
#include "net.h"
#include "gamesave.h"
#include "library.h"
#include <ft2build.h>
#include FT_FREETYPE_H

#define W 1280
#define H 720

static u32 fb_width;
static int clip_left = 0;
static int clip_right = W;

static void rect(u32 *fb, int x, int y, int w, int h, u32 color)
{
    for (int j = y; j < y + h; j++)
        for (int i = x; i < x + w; i++)
            if (i >= 0 && i < W && j >= 0 && j < H)
                fb[j * fb_width + i] = color;
}

static void round_rect(u32 *fb, int x, int y, int w, int h, int r, u32 color)
{
    for (int j = 0; j < h; j++)
        for (int i = 0; i < w; i++) {
            int cx = i < r ? r : (i >= w-r ? w-r-1 : i);
            int cy = j < r ? r : (j >= h-r ? h-r-1 : j);
            int dx = i-cx, dy = j-cy;
            if (dx*dx + dy*dy <= r*r) {
                int px = x + i;
                int py = y + j;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    fb[py * fb_width + px] = color;
            }
        }
}

static void draw_cover(u32 *fb, int x, int y, const u32 *cover)
{
    for (int j = 0; j < LIB_COVER_H; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;
        if (x < 0 || x + LIB_COVER_W > W) continue;
        memcpy(fb + (size_t)py * fb_width + x,
               cover + (size_t)j * LIB_COVER_W,
               LIB_COVER_W * sizeof(u32));
    }
}

static void draw_text(FT_Face face, u32 *fb, int x, int y, const char *str)
{
    int start = x;

    for (const unsigned char *p = (const unsigned char *)str; *p;) {
        u32 c;
        int n = decode_utf8(&c, p);
        if (n <= 0) break;
        p += n;

        if (c == '\n') {
            y += 38;
            x = start;
            continue;
        }

        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) continue;

        FT_GlyphSlot g = face->glyph;
        FT_Bitmap *b = &g->bitmap;

        for (unsigned int j = 0; j < b->rows; j++) {
            for (unsigned int i = 0; i < b->width; i++) {
                int px = x + g->bitmap_left + i;
                int py = y - g->bitmap_top + j;

                if (px < clip_left || px >= clip_right || py < 0 || py >= H) continue;

                u8 a = b->buffer[j * b->pitch + i];
                if (!a) continue;

                u32 bg = fb[py * fb_width + px];
                u8 red = bg & 0xFF;
                u8 green = (bg >> 8) & 0xFF;
                u8 blue = (bg >> 16) & 0xFF;

                red += (255 - red) * a / 255;
                green += (255 - green) * a / 255;
                blue += (255 - blue) * a / 255;

                fb[py * fb_width + px] = RGBA8_MAXALPHA(red, green, blue);
            }
        }

        x += g->advance.x >> 6;
    }
}


static int measure_text(FT_Face face, const char *str)
{
    int width = 0;

    for (const unsigned char *p = (const unsigned char *)str; *p;) {
        u32 c;
        int n = decode_utf8(&c, p);
        if (n <= 0) break;
        p += n;

        if (!FT_Load_Char(face, c, FT_LOAD_DEFAULT))
            width += face->glyph->advance.x >> 6;
    }

    return width;
}


#define MAX_ACHIEVEMENTS 100

// Какие игры умеем читать из их сейва на консоли.
// flag_offset: в сейве Hotline Miami массив флагов начинается с технического id 256,
// поэтому достижение i лежит во флаге i+1.
typedef struct {
    const char *appid;
    u64 title_id;
    const char *save_path;
    int flag_offset;
} SaveSource;

static const SaveSource SAVE_SOURCES[] = {
    { "219150", 0x0100D0E00E51E000ULL, "/HotlineMiami", 1 },
};

static int save_flag_offset = 0;

static int load_save_flags(const char *appid, u8 *flags, int max_flags)
{
    if (!appid) return -1;

    save_flag_offset = 0;

    for (unsigned i = 0; i < sizeof(SAVE_SOURCES) / sizeof(SAVE_SOURCES[0]); i++) {
        if (strcmp(SAVE_SOURCES[i].appid, appid) == 0) {
            save_flag_offset = SAVE_SOURCES[i].flag_offset;
            return gamesave_read_unlocked(SAVE_SOURCES[i].title_id,
                                          SAVE_SOURCES[i].save_path,
                                          flags, max_flags);
        }
    }

    return -1;
}

static bool achievement_unlocked(const char *appid, int index,
                                 const SteamAchievement *achievement,
                                 const u8 *flags, int flag_count)
{
    if (flag_count > 0) {
        int slot = index + save_flag_offset;
        return slot >= 0 && slot < flag_count && flags[slot] != 0;
    }

    return save_is_unlocked(appid, achievement->id);
}

static int load_catalog(const char *appid,
                        SteamAchievement *achievements,
                        int max_achievements) {
    char path[128];
    snprintf(path, sizeof(path), "romfs:/catalog/%s.json", appid);

    FILE *file = fopen(path, "rb");
    if (!file) return -1;

    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return -1;
    }

    long size = ftell(file);
    if (size <= 0 || size > 65536) {
        fclose(file);
        return -1;
    }

    rewind(file);

    char *buffer = malloc((size_t)size + 1);
    if (!buffer) {
        fclose(file);
        return -1;
    }

    size_t read_size = fread(buffer, 1, (size_t)size, file);
    fclose(file);

    if (read_size != (size_t)size) {
        free(buffer);
        return -1;
    }

    buffer[size] = '\0';
    int count = steam_parse_achievements(buffer, achievements,
                                         max_achievements);
    free(buffer);
    return count;
}


static Result scan_user_save_data(u64 target_id, s64 *records_read,
                                  bool *found, u64 *save_id)
{
    FsSaveDataInfoReader reader;
    Result rc = fsOpenSaveDataInfoReader(
        &reader, FsSaveDataSpaceId_All
    );
    if (R_FAILED(rc))
        return rc;

    FILE *debug = fopen(
        "sdmc:/switch/NX-Stach/save_debug.txt", "w"
    );

    FsSaveDataInfo entries[64] = {0};

    *records_read = 0;
    *found = false;
    *save_id = 0;

    if (debug)
        fprintf(debug, "INDEX SPACE APP_ID SAVE_ID TYPE SIZE RANK UID0 UID1\n");

    for (int page = 0; page < 128; page++) {
        s64 count = 0;

        rc = fsSaveDataInfoReaderRead(
            &reader, entries, 64, &count
        );

        if (R_FAILED(rc) || count <= 0)
            break;

        if (count > 64)
            count = 64;

        for (s64 i = 0; i < count; i++) {
            FsSaveDataInfo *e = &entries[i];

            if (debug) {
                fprintf(debug,
                    "%lld %u %016llX %016llX %u %llu %u %016llX %016llX\n",
                    (long long)*records_read + i,
                    (unsigned)e->save_data_space_id,
                    (unsigned long long)e->application_id,
                    (unsigned long long)e->save_data_id,
                    (unsigned)e->save_data_type,
                    (unsigned long long)e->size,
                    (unsigned)e->save_data_rank,
                    (unsigned long long)e->uid.uid[0],
                    (unsigned long long)e->uid.uid[1]);
            }

            if (e->application_id == target_id) {
                *found = true;
                *save_id = e->save_data_id;

                if (debug) {
                    fprintf(debug,
                        "TARGET_INDEX %u SYSTEM_SAVE_ID %016llX\n",
                        (unsigned)e->save_data_index,
                        (unsigned long long)e->system_save_data_id);

                    FsSaveDataAttribute attr = {0};
                    attr.application_id = e->application_id;
                    attr.uid = e->uid;
                    attr.system_save_data_id = e->system_save_data_id;
                    attr.save_data_type = e->save_data_type;
                    attr.save_data_rank = e->save_data_rank;
                    attr.save_data_index = e->save_data_index;

                    FsFileSystem save_fs;
                    Result open_rc = fsOpenReadOnlySaveDataFileSystem(
                        &save_fs,
                        (FsSaveDataSpaceId)e->save_data_space_id,
                        &attr
                    );

                    fprintf(debug, "OPEN_READONLY_RESULT: 0x%08X\n",
                            (unsigned)open_rc);

                    if (R_SUCCEEDED(open_rc)) {
                        FsDir dir;
                        Result dir_rc = fsFsOpenDirectory(
                            &save_fs, "/",
                            FsDirOpenMode_ReadDirs | FsDirOpenMode_ReadFiles,
                            &dir
                        );

                        fprintf(debug, "OPEN_ROOT_RESULT: 0x%08X\n",
                                (unsigned)dir_rc);

                        if (R_SUCCEEDED(dir_rc)) {
                            FsDirectoryEntry dir_entries[32];
                            s64 total = 0;

                            Result read_rc = fsDirRead(
                                &dir, &total, 32, dir_entries
                            );

                            fprintf(debug, "DIR_READ_RESULT: 0x%08X COUNT: %lld\n",
                                    (unsigned)read_rc, (long long)total);

                            if (R_SUCCEEDED(read_rc)) {
                                for (s64 j = 0; j < total && j < 32; j++) {
                                    fprintf(debug, "%c %s %lld\n",
                                        dir_entries[j].type == FsDirEntryType_Dir ? 'D' : 'F',
                                        dir_entries[j].name,
                                        (long long)dir_entries[j].file_size);
                                }
                            }

                            const char *paths[] = {
                                "/HotlineMiami",
                                "/SaveData"
                            };

                            for (int k = 0; k < 2; k++) {
                                FsDir subdir;
                                Result sub_rc = fsFsOpenDirectory(
                                    &save_fs, paths[k],
                                    FsDirOpenMode_ReadDirs | FsDirOpenMode_ReadFiles,
                                    &subdir
                                );

                                fprintf(debug, "SUBDIR %s OPEN: 0x%08X\n",
                                        paths[k], (unsigned)sub_rc);

                                if (R_SUCCEEDED(sub_rc)) {
                                    FsDirectoryEntry entries[32];
                                    s64 entries_count = 0;

                                    Result entries_rc = fsDirRead(
                                        &subdir, &entries_count, 32, entries
                                    );

                                    fprintf(debug,
                                        "SUBDIR_READ: 0x%08X COUNT: %lld\n",
                                        (unsigned)entries_rc,
                                        (long long)entries_count);

                                    if (R_SUCCEEDED(entries_rc)) {
                                        for (s64 n = 0; n < entries_count && n < 32; n++) {
                                            fprintf(debug, "%c %s %lld\n",
                                                entries[n].type == FsDirEntryType_Dir ? 'D' : 'F',
                                                entries[n].name,
                                                (long long)entries[n].file_size);
                                        }
                                    }

                                    fsDirClose(&subdir);
                                }
                            }

                            FsFile save_file;
                            Result file_rc = fsFsOpenFile(
                                &save_fs,
                                "/HotlineMiami/savedata.vfs",
                                FsOpenMode_Read,
                                &save_file
                            );

                            fprintf(debug, "VFS_OPEN: 0x%08X\n", (unsigned)file_rc);
                            if (R_SUCCEEDED(file_rc)) {
                                s64 file_size = 0;
                                Result size_rc = fsFileGetSize(&save_file, &file_size);
                                fprintf(debug, "VFS_SIZE: 0x%08X %llu\n",
                                    (unsigned)size_rc, (unsigned long long)file_size);
                                FILE *export_file = fopen(
                                    "sdmc:/switch/NX-Stach/savedata.vfs", "wb"
                                );

                                if (R_SUCCEEDED(size_rc) && export_file) {
                                    u8 buffer[0x4000];
                                    u64 offset = 0;
                                    bool export_ok = true;

                                    while (offset < file_size) {
                                        u64 request = file_size - offset;
                                        if (request > sizeof(buffer))
                                            request = sizeof(buffer);

                                        u64 chunk_read = 0;
                                        Result chunk_rc = fsFileRead(
                                            &save_file, offset, buffer,
                                            request, 0, &chunk_read
                                        );

                                        if (R_FAILED(chunk_rc) || chunk_read == 0) {
                                            export_ok = false;
                                            break;
                                        }

                                        if (fwrite(buffer, 1, chunk_read, export_file)
                                            != chunk_read) {
                                            export_ok = false;
                                            break;
                                        }

                                        offset += chunk_read;
                                    }

                                    fclose(export_file);
                                    fprintf(debug, "VFS_EXPORT: %s BYTES: %llu\n",
                                        export_ok && offset == file_size ? "OK" : "FAILED",
                                        (unsigned long long)offset);
                                } else {
                                    if (export_file)
                                        fclose(export_file);
                                    fprintf(debug, "VFS_EXPORT: FAILED\n");
                                }

                                fsFileClose(&save_file);
                            }

                            fsDirClose(&dir);
                        }


                        fsFsClose(&save_fs);
                    }
                }
            }
        }

        *records_read += count;

        if (count < 64)
            break;
    }

    if (debug)
        fclose(debug);

    fsSaveDataInfoReaderClose(&reader);
    return rc;
}

int main(int argc, char **argv)
{
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);

    if (R_FAILED(plInitialize(PlServiceType_User))) return 1;

    PlFontData font;
    if (R_FAILED(plGetSharedFontByType(&font, PlSharedFontType_Standard))) {
        plExit();
        return 1;
    }

    FT_Library library;
    FT_Face face;
    if (FT_Init_FreeType(&library)) { plExit(); return 1; }
    if (FT_New_Memory_Face(library, font.address, font.size, 0, &face)) {
        FT_Done_FreeType(library);
        plExit();
        return 1;
    }
    FT_Set_Pixel_Sizes(face, 0, 30);

    Framebuffer fb;
    framebufferCreate(&fb, nwindowGetDefault(), W, H, PIXEL_FORMAT_RGBA_8888, 2);
    framebufferMakeLinear(&fb);

    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);

    bool romfs_ready = R_SUCCEEDED(romfsInit());
    bool save_ready = save_init();
    bool net_ready = net_init();

    char sync_status[128] = "Not synchronized";

    SteamAchievement achievements[MAX_ACHIEVEMENTS] = {0};
    int achievement_count = -1;

    if (romfs_ready && game_count > 0 && games[0].steam_appid[0])
        achievement_count = load_catalog(games[0].steam_appid,
                                         achievements, MAX_ACHIEVEMENTS);

    u8 save_flags[MAX_ACHIEVEMENTS] = {0};
    int save_flag_count = 0;

    int selected = 0;
    int game_screen = 0;
    int achievement_offset = 0;

    if (game_count > 0)
        save_flag_count = load_save_flags(games[0].steam_appid, save_flags,
                                          MAX_ACHIEVEMENTS);

    int diagnostic_screen = 0;
    Result diagnostic_result = 0;
    s64 diagnostic_count = 0;
    bool diagnostic_found = false;
    u64 diagnostic_save_id = 0;

    while (appletMainLoop()) {
        padUpdate(&pad);
        u32 kDown = padGetButtonsDown(&pad);

        if (kDown & HidNpadButton_Plus) break;

        if (diagnostic_screen) {
            if (kDown & HidNpadButton_B)
                diagnostic_screen = 0;
        } else if (!game_screen) {
            if (kDown & HidNpadButton_Y) {
                diagnostic_result = scan_user_save_data(
                    0x0100D0E00E51E000ULL,
                    &diagnostic_count,
                    &diagnostic_found,
                    &diagnostic_save_id
                );
                diagnostic_screen = 1;
            }

            if (game_count > 0) {
                if (kDown & HidNpadButton_Right)
                    selected = (selected + 1) % game_count;
                if (kDown & HidNpadButton_Left)
                    selected = (selected + game_count - 1) % game_count;
                if ((kDown & HidNpadButton_Up) && selected >= 4)
                    selected -= 4;
                if ((kDown & HidNpadButton_Down) && selected + 4 < game_count)
                    selected += 4;
            }

            if ((kDown & HidNpadButton_A) && game_count > 0) {
                achievement_count = -1;

                if (!games[selected].steam_appid[0]) {
                    snprintf(sync_status, sizeof(sync_status),
                             "No Steam AppID (add to games.json)");
                } else {
                    snprintf(sync_status, sizeof(sync_status),
                             "Connecting to Steam...");

                    if (net_ready) {
                        char *response = malloc(262144);
                        if (response) {
                            char path[192];
                            snprintf(path, sizeof(path),
                                "/IPlayerService/GetGameAchievements/v1/?appid=%s&language=english",
                                games[selected].steam_appid);

                            if (net_https_get("api.steampowered.com",
                                              path, response, 262144)) {
                                achievement_count = steam_parse_achievements(
                                    response, achievements, MAX_ACHIEVEMENTS);
                            }

                            free(response);
                        }
                    }
                }

                if (achievement_count >= 0) {
                    snprintf(sync_status, sizeof(sync_status),
                             "Steam: %d achievements", achievement_count);
                } else if (games[selected].steam_appid[0]) {
                    achievement_count = romfs_ready
                        ? load_catalog(games[selected].steam_appid, achievements,
                                       MAX_ACHIEVEMENTS)
                        : -1;

                    snprintf(sync_status, sizeof(sync_status),
                             achievement_count >= 0
                             ? "Using saved catalog"
                             : "Steam sync failed");
                }

                save_flag_count = load_save_flags(games[selected].steam_appid,
                                                  save_flags, MAX_ACHIEVEMENTS);

                achievement_offset = 0;
                game_screen = 1;
            }
        } else {
            if (kDown & HidNpadButton_B) game_screen = 0;
            if ((kDown & HidNpadButton_Up) && achievement_offset > 0)
                achievement_offset--;
            if ((kDown & HidNpadButton_Down) &&
                achievement_offset + 4 <= achievement_count - 1)
                achievement_offset++;
        }

        u32 stride;
        u32 *pixels = (u32 *)framebufferBegin(&fb, &stride);
        fb_width = stride / sizeof(u32);

        rect(pixels, 0, 0, W, H, RGBA8_MAXALPHA(37, 39, 43));

        if (diagnostic_screen) {
            draw_text(face, pixels, 55, 72, "Save Data Diagnostics");

            char line[128];

            snprintf(line, sizeof(line), "Result: 0x%08X",
                     (unsigned)diagnostic_result);
            draw_text(face, pixels, 85, 160, line);

            snprintf(line, sizeof(line), "Records read: %lld",
                     (long long)diagnostic_count);
            draw_text(face, pixels, 85, 220, line);

            draw_text(face, pixels, 85, 280,
                diagnostic_found
                ? "Hotline Miami save: FOUND"
                : "Hotline Miami save: NOT FOUND");

            if (diagnostic_found) {
                snprintf(line, sizeof(line), "Save ID: %016llX",
                         (unsigned long long)diagnostic_save_id);
                draw_text(face, pixels, 85, 340, line);
            }

            draw_text(face, pixels, 55, 600,
                "B: Back");
        } else if (!game_screen) {
            draw_text(face, pixels, 55, 72, "NX-Stach");

            const int per_page = 8;
            const int page = selected / per_page;
            const int first = page * per_page;
            const int pages = (game_count + per_page - 1) / per_page;

            char page_text[32];
            snprintf(page_text, sizeof(page_text), "%d / %d",
                     page + 1, pages > 0 ? pages : 1);
            int page_width = measure_text(face, page_text);
            draw_text(face, pixels, W - 55 - page_width, 72, page_text);

            if (game_count == 0) {
                draw_text(face, pixels, 55, 300, "No games found");
                draw_text(face, pixels, 55, 360,
                          "Check SD:/switch/NX-Stach/games.json");
            }

            static int marquee_offset = 0;

            for (int slot = 0; slot < per_page; slot++) {
                int i = first + slot;
                if (i >= game_count) break;

                int col = slot % 4;
                int row = slot / 4;
                int x = 55 + col * 295;
                int y = 210 + row * 215;

                const u32 *cover = library_cover(games[i].title_id);

                if (cover) {
                    draw_cover(pixels, x, y, cover);
                } else {
                    round_rect(pixels, x, y, LIB_COVER_W, LIB_COVER_H, 16,
                               RGBA8_MAXALPHA(52, 55, 60));
                    draw_text(face, pixels, x + 20, y + 100,
                              "no cover");
                }

                int bar_y = y + LIB_COVER_H - 44;
                rect(pixels, x, bar_y, LIB_COVER_W, 44,
                     RGBA8_MAXALPHA(22, 23, 26));

                clip_left = x + 10;
                clip_right = x + LIB_COVER_W - 10;

                if (i == selected) {
                    int text_width = measure_text(face, games[i].name);
                    int cycle = text_width + 40;
                    if (cycle < 1) cycle = 1;

                    marquee_offset = (marquee_offset + 2) % cycle;

                    draw_text(face, pixels, x + 10 - marquee_offset,
                              bar_y + 33, games[i].name);
                    draw_text(face, pixels, x + 10 - marquee_offset + cycle,
                              bar_y + 33, games[i].name);
                } else {
                    draw_text(face, pixels, x + 10, bar_y + 33,
                              games[i].name);
                }

                clip_left = 0;
                clip_right = W;

                if (i == selected) {
                    u32 accent = RGBA8_MAXALPHA(120, 200, 255);
                    rect(pixels, x, y, LIB_COVER_W, 3, accent);
                    rect(pixels, x, y + LIB_COVER_H - 3, LIB_COVER_W, 3, accent);
                    rect(pixels, x, y, 3, LIB_COVER_H, accent);
                    rect(pixels, x + LIB_COVER_W - 3, y, 3, LIB_COVER_H, accent);
                }
            }

            draw_text(face, pixels, 55, 665,
                      "A: Open    D-Pad: Select    +: Exit");
        } else {
            draw_text(face, pixels, 55, 72, games[selected].name);

            int unlocked_count = 0;
            for (int i = 0; i < achievement_count; i++) {
                if (achievement_unlocked(games[selected].steam_appid, i,
                                         &achievements[i],
                                         save_flags, save_flag_count))
                    unlocked_count++;
            }

            char stats[96];
            if (achievement_count >= 0) {
                snprintf(stats, sizeof(stats), "Achievements: %d / %d",
                         unlocked_count, achievement_count);
            } else {
                snprintf(stats, sizeof(stats), "Catalog: ERROR");
            }

            round_rect(pixels, 55, 110, 1170, 120, 18,
                       RGBA8_MAXALPHA(52, 55, 60));
            draw_text(face, pixels, 85, 160, stats);
            draw_text(face, pixels, 85, 205, sync_status);
            draw_text(face, pixels, 55, 285, "Achievements");

            for (int i = 0; i < 4; i++) {
                int index = achievement_offset + i;
                if (index >= achievement_count) break;

                bool unlocked = achievement_unlocked(
                    games[selected].steam_appid, index, &achievements[index],
                    save_flags, save_flag_count);

                int y = 310 + i * 65;
                u32 color = unlocked
                    ? RGBA8_MAXALPHA(62, 78, 65)
                    : RGBA8_MAXALPHA(52, 55, 60);

                round_rect(pixels, 55, y, 1170, 55, 14, color);

                char row_text[256];
                snprintf(row_text, sizeof(row_text), "%s  [%s]",
                         achievements[index].name,
                         unlocked ? "UNLOCKED" : "LOCKED");

                draw_text(face, pixels, 85, y + 38, row_text);
            }

            char source_line[128];
            if (save_flag_count > 0)
                snprintf(source_line, sizeof(source_line),
                         "Progress: from game save (%d flags)", save_flag_count);
            else
                snprintf(source_line, sizeof(source_line),
                         "Progress: progress.json (save read failed: %s)",
                         gamesave_last_error());

            draw_text(face, pixels, 55, 640, source_line);
            draw_text(face, pixels, 55, 680,
                save_ready ? "SD card: READY" : "SD card: ERROR");
        }

        framebufferEnd(&fb);
    }

    if (net_ready) net_exit();
    save_exit();
    library_exit();
    if (romfs_ready) romfsExit();
    framebufferClose(&fb);
    FT_Done_Face(face);
    FT_Done_FreeType(library);
    plExit();
    return 0;
}
