#include <switch.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "steam.h"
#include "save.h"
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
            if (dx*dx + dy*dy <= r*r)
                fb[(y+j)*fb_width+x+i] = color;
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

    const char *test_json =
        "{\"response\":{\"games\":["
        "{\"appid\":219150,\"name\":\"Hotline Miami\",\"playtime_forever\":0},"
        "{\"appid\":274170,\"name\":\"Hotline Miami 2: Wrong Number\",\"playtime_forever\":0}"
        "]}}";

    SteamGame games[2] = {0};
    int game_count = steam_parse_games(test_json, games, 2);
    if (game_count <= 0) return 1;

    bool romfs_ready = R_SUCCEEDED(romfsInit());
    bool save_ready = save_init();

    SteamAchievement achievements[MAX_ACHIEVEMENTS] = {0};
    int achievement_count = romfs_ready
        ? load_catalog("219150", achievements, MAX_ACHIEVEMENTS)
        : -1;

    int selected = 0;
    int game_screen = 0;
    int achievement_offset = 0;

    while (appletMainLoop()) {
        padUpdate(&pad);
        u32 kDown = padGetButtonsDown(&pad);

        if (kDown & HidNpadButton_Plus) break;

        if ((kDown & HidNpadButton_X) && save_ready &&
            achievement_count > achievement_offset) {
            save_unlock(games[selected].appid,
                        achievements[achievement_offset].id);
        }

        if (!game_screen) {
            if (kDown & HidNpadButton_Right) selected = (selected + 1) % game_count;
            if (kDown & HidNpadButton_Left) selected = (selected + game_count - 1) % game_count;
            if (kDown & HidNpadButton_A) {
                achievement_count = romfs_ready
                    ? load_catalog(games[selected].appid, achievements,
                                   MAX_ACHIEVEMENTS)
                    : -1;
                achievement_offset = 0;
                game_screen = 1;
            }
        } else {
            if (kDown & HidNpadButton_B) game_screen = 0;
            if ((kDown & HidNpadButton_Up) && achievement_offset > 0)
                achievement_offset--;
            if ((kDown & HidNpadButton_Down) &&
                achievement_offset + 4 < achievement_count)
                achievement_offset++;
        }

        u32 stride;
        u32 *pixels = (u32 *)framebufferBegin(&fb, &stride);
        fb_width = stride / sizeof(u32);

        rect(pixels, 0, 0, W, H, RGBA8_MAXALPHA(37, 39, 43));

        if (!game_screen) {
            draw_text(face, pixels, 55, 72, "NX-Stach");

            round_rect(pixels, 55, 110, 1170, 90, 18,
                       RGBA8_MAXALPHA(52, 55, 60));
            draw_text(face, pixels, 85, 165, "Steam Achievements");

            int tile_x[4] = {55, 350, 645, 940};
            int tile_w[4] = {270, 270, 270, 285};

            static int marquee_offset = 0;

            for (int i = 0; i < game_count; i++) {
                u32 color = (i == selected)
                    ? RGBA8_MAXALPHA(82, 86, 94)
                    : RGBA8_MAXALPHA(52, 55, 60);

                round_rect(pixels, tile_x[i], 230, tile_w[i], 190, 18, color);

                if (i == 1) {
                    int left = tile_x[i] + 20;
                    int right = tile_x[i] + tile_w[i] - 20;

                    clip_left = left;
                    clip_right = right;

                    int text_width = measure_text(face, games[i].name);
                    int cycle = text_width + 60;

                    marquee_offset = (marquee_offset + 1) % cycle;

                    draw_text(face, pixels,
                              left - marquee_offset, 300, games[i].name);
                    draw_text(face, pixels,
                              left - marquee_offset + cycle, 300, games[i].name);

                    clip_left = 0;
                    clip_right = W;
                } else {
                    draw_text(face, pixels, tile_x[i] + 25, 300, games[i].name);
                }
            }

            draw_text(face, pixels, 55, 500, "A: Open game");
            draw_text(face, pixels, 55, 650, "Press + to exit");
        } else {
            draw_text(face, pixels, 55, 72, games[selected].name);

            int unlocked_count = 0;
            for (int i = 0; i < achievement_count; i++) {
                if (save_is_unlocked(games[selected].appid,
                                     achievements[i].id))
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
            draw_text(face, pixels, 55, 285, "Achievements");

            for (int i = 0; i < 4; i++) {
                int index = achievement_offset + i;
                if (index >= achievement_count) break;

                bool unlocked = save_is_unlocked(
                    games[selected].appid, achievements[index].id);

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

            draw_text(face, pixels, 55, 600,
                "X: Unlock first visible achievement (test)");
            draw_text(face, pixels, 55, 645,
                save_ready ? "SD card: READY" : "SD card: ERROR");
            draw_text(face, pixels, 55, 680, save_status());
        }

        framebufferEnd(&fb);
    }

    save_exit();
    if (romfs_ready) romfsExit();
    framebufferClose(&fb);
    FT_Done_Face(face);
    FT_Done_FreeType(library);
    plExit();
    return 0;
}
