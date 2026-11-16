#include <switch.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#include "steam.h"
#include "save.h"
#include "net.h"
#include "gamesave.h"
#include "library.h"
#include "history.h"

#include <ft2build.h>
#include FT_FREETYPE_H

#include "stb_image.h"

#define W 1280
#define H 720
#define MAX_ACHIEVEMENTS 100

#define COVER_SIZE 190
#define GRID_COLS 5
#define GRID_X0 55
#define GRID_STEP_X 245
#define GRID_Y0 175
#define GRID_STEP_Y 235
#define HEADER_H 150

#define ACH_ICON_SIZE 44
#define ROW_H 78
#define LIST_Y0 250
#define LIST_ROWS 5

#define COLOR_BG      RGBA8_MAXALPHA(28, 30, 34)
#define COLOR_PANEL   RGBA8_MAXALPHA(48, 51, 57)
#define COLOR_PANEL2  RGBA8_MAXALPHA(40, 43, 48)
#define COLOR_TRACK   RGBA8_MAXALPHA(62, 66, 73)
#define COLOR_UNLOCK  RGBA8_MAXALPHA(52, 68, 55)
#define COLOR_ACCENT  RGBA8_MAXALPHA(120, 200, 255)

static u32 fb_width;
static int clip_left = 0;
static int clip_right = W;

static u8 text_r = 255, text_g = 255, text_b = 255;

static void set_text_color(u8 r, u8 g, u8 b) { text_r = r; text_g = g; text_b = b; }
static void reset_text_color(void) { set_text_color(255, 255, 255); }

/* ------------------------------- рисование ------------------------------- */

static void rect(u32 *fb, int x, int y, int w, int h, u32 color)
{
    for (int j = y; j < y + h; j++) {
        if (j < 0 || j >= H) continue;
        for (int i = x; i < x + w; i++) {
            if (i < 0 || i >= W) continue;
            fb[(size_t)j * fb_width + i] = color;
        }
    }
}

static void round_rect(u32 *fb, int x, int y, int w, int h, int r, u32 color)
{
    if (r * 2 > w) r = w / 2;
    if (r * 2 > h) r = h / 2;

    for (int j = 0; j < h; j++) {
        for (int i = 0; i < w; i++) {
            int cx = i < r ? r : (i >= w - r ? w - r - 1 : i);
            int cy = j < r ? r : (j >= h - r ? h - r - 1 : j);
            int dx = i - cx, dy = j - cy;

            if (dx * dx + dy * dy <= r * r) {
                int px = x + i, py = y + j;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    fb[(size_t)py * fb_width + px] = color;
            }
        }
    }
}

static void round_corners(u32 *fb, int x, int y, int w, int h, int r, u32 bg)
{
    for (int j = 0; j < r; j++) {
        for (int i = 0; i < r; i++) {
            int dx = r - i, dy = r - j;

            if (dx * dx + dy * dy > r * r) {
                int px = x + i, py = y + j;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    fb[(size_t)py * fb_width + px] = bg;

                px = x + w - 1 - i;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    fb[(size_t)py * fb_width + px] = bg;

                py = y + h - 1 - j;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    fb[(size_t)py * fb_width + px] = bg;

                px = x + i;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    fb[(size_t)py * fb_width + px] = bg;
            }
        }
    }
}

static int draw_codepoint(FT_Face face, u32 *fb, int x, int y, u32 c)
{
    if (FT_Load_Char(face, c, FT_LOAD_RENDER))
        return 0;

    FT_GlyphSlot g = face->glyph;
    FT_Bitmap *b = &g->bitmap;

    for (unsigned int j = 0; j < b->rows; j++) {
        for (unsigned int i = 0; i < b->width; i++) {
            int px = x + g->bitmap_left + i;
            int py = y - g->bitmap_top + j;

            if (px < clip_left || px >= clip_right || py < 0 || py >= H)
                continue;

            u8 a = b->buffer[j * b->pitch + i];
            if (!a) continue;

            u32 bg = fb[(size_t)py * fb_width + px];
            u8 red = bg & 0xFF;
            u8 green = (bg >> 8) & 0xFF;
            u8 blue = (bg >> 16) & 0xFF;

            red += (text_r - red) * a / 255;
            green += (text_g - green) * a / 255;
            blue += (text_b - blue) * a / 255;

            fb[(size_t)py * fb_width + px] = RGBA8_MAXALPHA(red, green, blue);
        }
    }

    return g->advance.x >> 6;
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
            y += 26;
            x = start;
            continue;
        }

        x += draw_codepoint(face, fb, x, y, c);
    }
}

// Перелив светло-голубой -> белый.
static void draw_text_shine(FT_Face face, u32 *fb, int x, int y,
                            const char *str, int phase)
{
    int index = 0;

    for (const unsigned char *p = (const unsigned char *)str; *p;) {
        u32 c;
        int n = decode_utf8(&c, p);
        if (n <= 0) break;
        p += n;

        int wave = (phase + index * 30) % 600;
        if (wave > 300) wave = 600 - wave;

        float k = (float)wave / 300.0f;

        set_text_color((u8)(150 + 105 * k),
                       (u8)(215 + 40 * k),
                       255);

        x += draw_codepoint(face, fb, x, y, c);
        index++;
    }

    reset_text_color();
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

static void draw_cover(u32 *fb, int x, int y, const u32 *cover,
                       u32 corner_color, int radius)
{
    for (int j = 0; j < COVER_SIZE; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;
        if (x < 0 || x + COVER_SIZE > W) continue;

        memcpy(fb + (size_t)py * fb_width + x,
               cover + (size_t)j * COVER_SIZE,
               COVER_SIZE * sizeof(u32));
    }

    round_corners(fb, x, y, COVER_SIZE, COVER_SIZE, radius, corner_color);
}

static void draw_scrollbar(u32 *fb, int x, int y, int h, int content, int view, int scroll)
{
    if (content <= view) return;

    round_rect(fb, x, y, 6, h, 3, COLOR_TRACK);

    int thumb_h = h * view / content;
    if (thumb_h < 40) thumb_h = 40;

    int max_scroll = content - view;
    int pos = max_scroll > 0 ? (h - thumb_h) * scroll / max_scroll : 0;

    round_rect(fb, x, y + pos, 6, thumb_h, 3, RGBA8_MAXALPHA(150, 155, 165));
}

/* --------------------------- иконки достижений --------------------------- */

static u32 *ach_icons[MAX_ACHIEVEMENTS];

static void ach_icons_clear(void)
{
    for (int i = 0; i < MAX_ACHIEVEMENTS; i++) {
        free(ach_icons[i]);
        ach_icons[i] = NULL;
    }
}

static u32 *load_achievement_icon(const char *appid, const char *id)
{
    char path[256];
    snprintf(path, sizeof(path), "romfs:/catalog/icons/%.32s/%.96s.jpg",
             appid, id);

    FILE *file = fopen(path, "rb");
    if (!file) return NULL;

    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return NULL; }

    long size = ftell(file);
    if (size <= 0 || size > 262144) { fclose(file); return NULL; }

    rewind(file);

    u8 *buffer = malloc((size_t)size);
    if (!buffer) { fclose(file); return NULL; }

    if (fread(buffer, 1, (size_t)size, file) != (size_t)size) {
        fclose(file);
        free(buffer);
        return NULL;
    }

    fclose(file);

    int width = 0, height = 0, channels = 0;
    stbi_uc *image = stbi_load_from_memory(buffer, (int)size,
                                           &width, &height, &channels, 4);
    free(buffer);

    if (!image || width <= 0 || height <= 0) {
        if (image) stbi_image_free(image);
        return NULL;
    }

    u32 *pixels = malloc((size_t)ACH_ICON_SIZE * ACH_ICON_SIZE * sizeof(u32));

    if (!pixels) { stbi_image_free(image); return NULL; }

    float scale = (float)width / (float)ACH_ICON_SIZE;
    if ((float)height / (float)ACH_ICON_SIZE > scale)
        scale = (float)height / (float)ACH_ICON_SIZE;

    float off_x = ((float)width - (float)ACH_ICON_SIZE * scale) / 2.0f;
    float off_y = ((float)height - (float)ACH_ICON_SIZE * scale) / 2.0f;

    for (int y = 0; y < ACH_ICON_SIZE; y++) {
        int sy = (int)(off_y + (float)y * scale);
        if (sy < 0) sy = 0;
        if (sy >= height) sy = height - 1;

        for (int x = 0; x < ACH_ICON_SIZE; x++) {
            int sx = (int)(off_x + (float)x * scale);
            if (sx < 0) sx = 0;
            if (sx >= width) sx = width - 1;

            const stbi_uc *src = image + ((size_t)sy * width + sx) * 4;
            pixels[(size_t)y * ACH_ICON_SIZE + x] =
                RGBA8_MAXALPHA(src[0], src[1], src[2]);
        }
    }

    stbi_image_free(image);
    return pixels;
}

static void ach_icons_load(const char *appid, int count,
                           const SteamAchievement *achievements)
{
    ach_icons_clear();

    if (!appid || !appid[0] || count <= 0)
        return;

    for (int i = 0; i < count && i < MAX_ACHIEVEMENTS; i++)
        ach_icons[i] = load_achievement_icon(appid, achievements[i].id);
}

static void draw_achievement_icon(u32 *fb, int x, int y,
                                  const u32 *icon, bool dim)
{
    for (int j = 0; j < ACH_ICON_SIZE; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;

        for (int i = 0; i < ACH_ICON_SIZE; i++) {
            int px = x + i;
            if (px < 0 || px >= W) continue;

            u32 color = icon[(size_t)j * ACH_ICON_SIZE + i];
            u8 red = color & 0xFF;
            u8 green = (color >> 8) & 0xFF;
            u8 blue = (color >> 16) & 0xFF;

            if (dim) {
                red = (u8)(red * 40 / 100);
                green = (u8)(green * 40 / 100);
                blue = (u8)(blue * 40 / 100);
            }

            fb[(size_t)py * fb_width + px] = RGBA8_MAXALPHA(red, green, blue);
        }
    }
}

/* ----------------------------- каталог Steam ----------------------------- */

static int load_catalog(const char *appid,
                        SteamAchievement *achievements,
                        int max_achievements)
{
    char path[128];
    snprintf(path, sizeof(path), "romfs:/catalog/%.32s.json", appid);

    FILE *file = fopen(path, "rb");
    if (!file) return -1;

    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return -1; }

    long size = ftell(file);
    if (size <= 0 || size > 65536) { fclose(file); return -1; }

    rewind(file);

    char *buffer = malloc((size_t)size + 1);
    if (!buffer) { fclose(file); return -1; }

    size_t read_size = fread(buffer, 1, (size_t)size, file);
    fclose(file);

    if (read_size != (size_t)size) { free(buffer); return -1; }

    buffer[size] = '\0';
    int count = steam_parse_achievements(buffer, achievements,
                                         max_achievements);
    free(buffer);
    return count;
}

/* ------------------------------ сейв игры ------------------------------ */

typedef struct {
    const char *appid;
    u64 title_id;
    const char *save_path;
    int flag_offset;
} SaveSource;

static const SaveSource SAVE_SOURCES[] = {
    { "219150", 0x0100D0E00E51E000ULL, "/HotlineMiami", 1 },
    { "274170", 0x0100D0E00E51E000ULL, "/HotlineMiami2", 1 },
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

/* -------------------------------- прочее -------------------------------- */

static u32 game_playtime_minutes(u64 title_id)
{
    PdmPlayStatistics stats;

    if (R_FAILED(pdmqryInitialize()))
        return 0;

    Result rc = pdmqryQueryPlayStatisticsByApplicationId(title_id, false, &stats);

    pdmqryExit();

    if (R_FAILED(rc))
        return 0;

    return (u32)(stats.playtime / 60000000000ULL);
}

static void format_date(u64 epoch, char *out, size_t size)
{
    out[0] = '\0';

    if (!epoch) return;

    TimeCalendarTime cal;
    TimeCalendarAdditionalInfo info;

    if (R_FAILED(timeToCalendarTimeWithMyRule((time_t)epoch, &cal, &info)))
        return;

    snprintf(out, size, "%02d.%02d.%04d", cal.day, cal.month, cal.year);
}

static bool text_contains(const char *haystack, const char *needle)
{
    if (!needle || !needle[0]) return true;

    size_t len = strlen(needle);
    const char *p = haystack;

    while (*p) {
        if (strncasecmp(p, needle, len) == 0)
            return true;
        p++;
    }

    return false;
}

static bool ask_search(char *out, size_t size)
{
    SwkbdConfig kbd;

    if (R_FAILED(swkbdCreate(&kbd, 0)))
        return false;

    swkbdConfigMakePresetDefault(&kbd);
    swkbdConfigSetGuideText(&kbd, "Search game");

    char buffer[64] = {0};
    Result rc = swkbdShow(&kbd, buffer, sizeof(buffer));

    swkbdClose(&kbd);

    if (R_FAILED(rc))
        return false;

    snprintf(out, size, "%s", buffer);
    return true;
}

/* ------------------------------- отрисовка ------------------------------- */

typedef struct {
    bool touching;
    int start_x, start_y;
    int last_x, last_y;
    bool dragged;
} TouchState;

static void draw_back_button(FT_Face face, u32 *fb, int x, int y)
{
    round_rect(fb, x, y, 52, 52, 16, COLOR_PANEL);
    // стрелка "<"
    rect(fb, x + 30, y + 16, 4, 20, RGBA8_MAXALPHA(220, 225, 235));
    for (int i = 0; i < 10; i++) {
        rect(fb, x + 30 - i, y + 16 + i, 4, 1, RGBA8_MAXALPHA(220, 225, 235));
        rect(fb, x + 30 - i, y + 35 - i, 4, 1, RGBA8_MAXALPHA(220, 225, 235));
    }
}

static void draw_guide(FT_Face face, FT_Face face_small, u32 *fb)
{
    const int w = 540, h = 360;
    const int x = (W - w) / 2, y = (H - h) / 2;

    round_rect(fb, x, y, w, h, 24, RGBA8_MAXALPHA(42, 45, 51));
    round_rect(fb, x, y, w, 64, 24, RGBA8_MAXALPHA(56, 60, 68));
    rect(fb, x, y + 44, w, 20, RGBA8_MAXALPHA(56, 60, 68));

    draw_text(face, fb, x + 30, y + 44, "Guide");
    draw_text_shine(face, fb, x + w - 30 - measure_text(face, "!"), y + 44, "!", 0);

    const char *lines[] = {
        "D-Pad / Stick   - select",
        "Touch           - scroll / tap",
        "A               - open game",
        "B               - back",
        "Y               - search",
        "-               - guide",
        "+               - exit",
    };

    int text_y = y + 112;

    for (unsigned i = 0; i < sizeof(lines) / sizeof(lines[0]); i++) {
        set_text_color(205, 210, 220);
        draw_text(face_small, fb, x + 36, text_y, lines[i]);
        reset_text_color();
        text_y += 32;
    }

    set_text_color(130, 135, 145);
    draw_text(face_small, fb, x + 36, y + h - 22, "Tap outside to close");
    reset_text_color();
}

/* --------------------------------- main --------------------------------- */

int main(int argc, char **argv)
{
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);

    PadState pad;
    padInitializeDefault(&pad);

    hidInitializeTouchScreen();

    if (R_FAILED(plInitialize(PlServiceType_User))) return 1;

    PlFontData font;
    if (R_FAILED(plGetSharedFontByType(&font, PlSharedFontType_Standard))) {
        plExit();
        return 1;
    }

    FT_Library ft;
    FT_Face face, face_small;

    if (FT_Init_FreeType(&ft)) { plExit(); return 1; }
    if (FT_New_Memory_Face(ft, font.address, font.size, 0, &face)) {
        FT_Done_FreeType(ft);
        plExit();
        return 1;
    }
    FT_Set_Pixel_Sizes(face, 0, 30);

    if (FT_New_Memory_Face(ft, font.address, font.size, 0, &face_small)) {
        FT_Done_Face(face);
        FT_Done_FreeType(ft);
        plExit();
        return 1;
    }
    FT_Set_Pixel_Sizes(face_small, 0, 20);

    Framebuffer fb;
    framebufferCreate(&fb, nwindowGetDefault(), W, H, PIXEL_FORMAT_RGBA_8888, 2);
    framebufferMakeLinear(&fb);

    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);

    bool romfs_ready = R_SUCCEEDED(romfsInit());

    save_init();
    bool net_ready = net_init();
    history_load();

    // диагностика структуры сейва коллекции
    gamesave_dump_tree(0x0100D0E00E51E000ULL);

    int view[MAX_GAMES];
    int view_count = 0;

    SteamAchievement achievements[MAX_ACHIEVEMENTS] = {0};
    int achievement_count = 0;
    int unlocked_count = 0;
    int order[MAX_ACHIEVEMENTS];

    u8 flags[MAX_ACHIEVEMENTS] = {0};
    int flag_count = 0;

    u32 playtime_minutes = 0;

    char search[64] = "";

    int selected = 0;
    int screen = 0;
    int guide_open = 0;

    float grid_scroll = 0.0f, grid_target = 0.0f;
    float list_scroll = 0.0f, list_target = 0.0f;

    u32 shine_counter = 0;
    int marquee_counter = 0;

    TouchState touch = {0};
    bool stick_latch = false;

    for (int i = 0; i < game_count; i++)
        view[view_count++] = i;

    while (appletMainLoop()) {
        padUpdate(&pad);
        u32 kDown = padGetButtonsDown(&pad);

        if (kDown & HidNpadButton_Plus) break;

        /* ---------- тач ---------- */
        HidTouchScreenState touch_state = {0};
        int touch_x = 0, touch_y = 0;
        bool tap = false;

        if (hidGetTouchScreenStates(&touch_state, 1) > 0 &&
            touch_state.count > 0) {
            touch_x = (int)touch_state.touches[0].x;
            touch_y = (int)touch_state.touches[0].y;

            if (!touch.touching) {
                touch.touching = true;
                touch.dragged = false;
                touch.start_x = touch_x;
                touch.start_y = touch_y;
            } else {
                int dx = touch_x - touch.last_x;
                int dy = touch_y - touch.last_y;

                if (abs(touch_x - touch.start_x) > 12 ||
                    abs(touch_y - touch.start_y) > 12)
                    touch.dragged = true;

                if (touch.dragged) {
                    if (guide_open) {
                        /* окно не скроллим */
                    } else if (screen == 0) {
                        grid_scroll -= (float)dy;
                        grid_target = grid_scroll;
                    } else {
                        list_scroll -= (float)dy;
                        list_target = list_scroll;
                    }
                }

                (void)dx;
            }

            touch.last_x = touch_x;
            touch.last_y = touch_y;
        } else if (touch.touching) {
            touch.touching = false;
            tap = !touch.dragged;
            touch.dragged = false;
        }

        /* ---------- кнопки ---------- */
        if (kDown & HidNpadButton_Minus)
            guide_open = !guide_open;
        else if (guide_open && (kDown & HidNpadButton_B))
            guide_open = 0;

        /* ---------- обработка нажатий ---------- */
        bool handled = false;

        if (tap) {
            // кнопка Guide
            if (touch_x >= 52 && touch_x <= 118 &&
                touch_y >= H - 92 && touch_y <= H - 26) {
                guide_open = !guide_open;
                handled = true;
            } else if (guide_open) {
                guide_open = 0;
                handled = true;
            }
        }

        if (!handled && !guide_open) {
            if (tap) {
                if (screen == 0) {
                    // поиск
                    if (touch_y >= 86 && touch_y <= 138) {
                        char query[64];
                        snprintf(query, sizeof(query), "%s", search);

                        if (ask_search(query, sizeof(query))) {
                            snprintf(search, sizeof(search), "%s", query);

                            view_count = 0;
                            selected = 0;
                            grid_scroll = grid_target = 0.0f;

                            for (int i = 0; i < game_count; i++)
                                if (text_contains(games[i].name, search))
                                    view[view_count++] = i;
                        }
                    } else if (touch_y >= GRID_Y0) {
                        int row = (int)((touch_y + grid_scroll - GRID_Y0) / GRID_STEP_Y);
                        int col = (touch_x - GRID_X0) / GRID_STEP_X;

                        if (col >= 0 && col < GRID_COLS && row >= 0) {
                            int x0 = GRID_X0 + col * GRID_STEP_X;
                            int position = row * GRID_COLS + col;

                            if (touch_x >= x0 && touch_x <= x0 + COVER_SIZE &&
                                position < view_count) {
                                selected = position;
                                kDown |= HidNpadButton_A;
                            }
                        }
                    }
                } else {
                    if (touch_x >= 52 && touch_x <= 118 &&
                        touch_y >= 30 && touch_y <= 96) {
                        screen = 0;
                        ach_icons_clear();
                    }
                }
            }

            if (screen == 0) {
                if (view_count > 0) {
                    if (kDown & HidNpadButton_Right)
                        selected = (selected + 1) % view_count;
                    if (kDown & HidNpadButton_Left)
                        selected = (selected + view_count - 1) % view_count;
                    if ((kDown & HidNpadButton_Down) && selected + GRID_COLS < view_count)
                        selected += GRID_COLS;
                    if ((kDown & HidNpadButton_Up) && selected >= GRID_COLS)
                        selected -= GRID_COLS;
                }

                HidAnalogStickState stick = padGetStickPos(&pad, 0);

                if (stick.y > 16000 || stick.y < -16000) {
                    if (!stick_latch && view_count > 0) {
                        stick_latch = true;

                        if (stick.y < 0) {
                            if (selected + GRID_COLS < view_count)
                                selected += GRID_COLS;
                        } else {
                            if (selected >= GRID_COLS)
                                selected -= GRID_COLS;
                        }
                    }
                } else {
                    stick_latch = false;
                }

                if ((kDown & HidNpadButton_A) && view_count > 0) {
                    const Game *game = &games[view[selected]];

                    achievement_count = 0;
                    unlocked_count = 0;
                    flag_count = 0;
                    list_scroll = list_target = 0.0f;

                    if (!game->steam_appid[0]) {
                        achievement_count = 0;
                    } else {
                        if (net_ready) {
                            char *response = malloc(262144);

                            if (response) {
                                char path[192];
                                snprintf(path, sizeof(path),
                                    "/IPlayerService/GetGameAchievements/v1/?appid=%s&language=english",
                                    game->steam_appid);

                                if (net_https_get("api.steampowered.com",
                                                  path, response, 262144))
                                    achievement_count = steam_parse_achievements(
                                        response, achievements, MAX_ACHIEVEMENTS);

                                free(response);
                            }
                        }

                        if (achievement_count <= 0)
                            achievement_count = romfs_ready
                                ? load_catalog(game->steam_appid, achievements,
                                               MAX_ACHIEVEMENTS)
                                : 0;

                        flag_count = load_save_flags(game->steam_appid, flags,
                                                     MAX_ACHIEVEMENTS);

                        if (flag_count > 0) {
                            u64 now = (u64)time(NULL);
                            bool changed = false;

                            for (int i = 0; i < achievement_count; i++) {
                                if (achievement_unlocked(game->steam_appid, i,
                                                         &achievements[i],
                                                         flags, flag_count)) {
                                    unlocked_count++;

                                    if (history_get(game->steam_appid,
                                                    achievements[i].id) == 0) {
                                        history_mark(game->steam_appid,
                                                     achievements[i].id, now);
                                        changed = true;
                                    }
                                }
                            }

                            if (changed) history_save();
                        } else if (achievement_count > 0) {
                            for (int i = 0; i < achievement_count; i++)
                                if (save_is_unlocked(game->steam_appid,
                                                     achievements[i].id))
                                    unlocked_count++;
                        }
                    }

                    {
                        int n = 0;

                        for (int i = 0; i < achievement_count; i++)
                            if (achievement_unlocked(game->steam_appid, i,
                                                     &achievements[i],
                                                     flags, flag_count))
                                order[n++] = i;

                        for (int i = 0; i < achievement_count; i++)
                            if (!achievement_unlocked(game->steam_appid, i,
                                                      &achievements[i],
                                                      flags, flag_count))
                                order[n++] = i;
                    }

                    ach_icons_load(game->steam_appid, achievement_count, achievements);
                    playtime_minutes = game_playtime_minutes(game->title_id);

                    screen = 1;
                }
            } else {
                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }
                if (kDown & HidNpadButton_Down)
                    list_target += ROW_H;
                if (kDown & HidNpadButton_Up)
                    list_target -= ROW_H;
            }
        }

        /* ---------- ограничение прокрутки ---------- */
        {
            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            float content = (float)rows * GRID_STEP_Y;
            float visible = (float)(H - GRID_Y0 - 60);
            float max_scroll = content - visible;

            if (max_scroll < 0) max_scroll = 0;

            // держим выбранную плитку в кадре
            if (!touch.dragged) {
                int row = selected / GRID_COLS;
                float top = (float)row * GRID_STEP_Y;

                if (top < grid_target) grid_target = top;
                if (top + GRID_STEP_Y > grid_target + visible)
                    grid_target = top + GRID_STEP_Y - visible;
            }

            if (grid_target < 0) grid_target = 0;
            if (grid_target > max_scroll) grid_target = max_scroll;
            if (grid_scroll < 0) grid_scroll = 0;
            if (grid_scroll > max_scroll) grid_scroll = max_scroll;

            if (!touch.dragged)
                grid_scroll += (grid_target - grid_scroll) * 0.25f;

            float list_content = (float)achievement_count * ROW_H;
            float list_visible = (float)(LIST_ROWS * ROW_H);
            float list_max = list_content - list_visible;

            if (list_max < 0) list_max = 0;
            if (list_target < 0) list_target = 0;
            if (list_target > list_max) list_target = list_max;
            if (list_scroll < 0) list_scroll = 0;
            if (list_scroll > list_max) list_scroll = list_max;

            if (!touch.dragged)
                list_scroll += (list_target - list_scroll) * 0.3f;
        }

        /* ---------- отрисовка ---------- */
        u32 stride;
        u32 *pixels = (u32 *)framebufferBegin(&fb, &stride);
        fb_width = stride / sizeof(u32);

        rect(pixels, 0, 0, W, H, COLOR_BG);

        if (screen == 0) {
            // грид
            for (int i = 0; i < view_count; i++) {
                int col = i % GRID_COLS;
                int row = i / GRID_COLS;

                int x = GRID_X0 + col * GRID_STEP_X;
                int y = GRID_Y0 + (int)((float)row * GRID_STEP_Y - grid_scroll);

                if (y + COVER_SIZE + 30 < HEADER_H) continue;
                if (y > H) continue;

                int game_index = view[i];
                const u32 *cover = library_cover(games[game_index].title_id);

                if (i == selected) {
                    round_rect(pixels, x - 6, y - 6, COVER_SIZE + 12,
                               COVER_SIZE + 12, 24, COLOR_ACCENT);
                }

                if (cover)
                    draw_cover(pixels, x, y, cover,
                               i == selected ? COLOR_ACCENT : COLOR_BG, 18);
                else
                    round_rect(pixels, x, y, COVER_SIZE, COVER_SIZE, 18,
                               COLOR_PANEL);

                clip_left = x;
                clip_right = x + COVER_SIZE;

                int name_y = y + COVER_SIZE + 26;

                if (i == selected) {
                    int name_width = measure_text(face_small, games[game_index].name);
                    int cycle = name_width + 60;
                    if (cycle < 1) cycle = 1;

                    int shift = marquee_counter % cycle;

                    draw_text(face_small, pixels, x - shift, name_y,
                              games[game_index].name);
                    draw_text(face_small, pixels, x - shift + cycle, name_y,
                              games[game_index].name);
                } else {
                    set_text_color(200, 205, 215);
                    draw_text(face_small, pixels, x, name_y, games[game_index].name);
                    reset_text_color();
                }

                clip_left = 0;
                clip_right = W;
            }

            // шапка
            rect(pixels, 0, 0, W, HEADER_H, COLOR_BG);
            draw_text_shine(face, pixels, 55, 58, "NX-Stach", shine_counter);

            round_rect(pixels, 55, 86, 1170, 52, 14, COLOR_PANEL);

            if (search[0]) {
                set_text_color(230, 232, 238);
                draw_text(face_small, pixels, 78, 120, search);
            } else {
                set_text_color(120, 125, 135);
                draw_text(face_small, pixels, 78, 120, "Search...");
            }
            reset_text_color();

            set_text_color(110, 115, 125);
            draw_text(face_small, pixels, W - 130, 120, "Y");
            reset_text_color();

            const int visible_rows = 2;
            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            draw_scrollbar(pixels, W - 24, GRID_Y0, H - GRID_Y0 - 80,
                           rows * GRID_STEP_Y, visible_rows * GRID_STEP_Y,
                           (int)grid_scroll);
        } else if (view_count > 0) {
            const Game *game = &games[view[selected]];

            // список
            int first = (int)(list_scroll / ROW_H);

            for (int i = first; i < achievement_count && i < first + LIST_ROWS + 2; i++) {
                int index = order[i];
                bool unlocked = achievement_unlocked(game->steam_appid, index,
                                                     &achievements[index],
                                                     flags, flag_count);

                int y = LIST_Y0 + i * ROW_H - (int)list_scroll;

                if (y + ROW_H < 200) continue;

                round_rect(pixels, 55, y, 1130, ROW_H - 10, 14,
                           unlocked ? COLOR_UNLOCK : COLOR_PANEL2);

                if (ach_icons[index])
                    draw_achievement_icon(pixels, 70, y + 12, ach_icons[index], !unlocked);
                else
                    round_rect(pixels, 70, y + 12, ACH_ICON_SIZE, ACH_ICON_SIZE, 8,
                               RGBA8_MAXALPHA(32, 34, 38));

                if (unlocked) set_text_color(200, 245, 205);
                else set_text_color(195, 200, 210);

                clip_left = 128;
                clip_right = 980;
                draw_text(face_small, pixels, 128, y + 28, achievements[index].name);
                clip_left = 0;
                clip_right = W;

                set_text_color(140, 145, 155);
                clip_left = 128;
                clip_right = 980;
                draw_text(face_small, pixels, 128, y + 52, achievements[index].description);
                clip_left = 0;
                clip_right = W;
                reset_text_color();

                if (unlocked) {
                    char date[32];
                    format_date(history_get(game->steam_appid, achievements[index].id),
                                date, sizeof(date));

                    if (date[0]) {
                        set_text_color(150, 200, 160);
                        int date_width = measure_text(face_small, date);
                        draw_text(face_small, pixels, 1165 - date_width, y + 40, date);
                        reset_text_color();
                    }
                }
            }

            draw_scrollbar(pixels, W - 24, LIST_Y0, LIST_ROWS * ROW_H,
                           achievement_count * ROW_H, LIST_ROWS * ROW_H,
                           (int)list_scroll);

            // шапка
            rect(pixels, 0, 0, W, 210, COLOR_BG);

            draw_back_button(face, pixels, 55, 34);
            draw_text(face, pixels, 128, 68, game->name);

            char stats[128];
            snprintf(stats, sizeof(stats), "Achievements: %d / %d",
                     unlocked_count, achievement_count);

            set_text_color(190, 195, 205);
            draw_text(face_small, pixels, 128, 100, stats);

            if (playtime_minutes > 0) {
                char playtime[64];
                snprintf(playtime, sizeof(playtime), "Time in game: %u h %u m",
                         playtime_minutes / 60, playtime_minutes % 60);
                draw_text(face_small, pixels, 128, 126, playtime);
            }
            reset_text_color();

            int bar_w = 960;
            int filled = achievement_count > 0
                ? bar_w * unlocked_count / achievement_count : 0;

            round_rect(pixels, 55, 152, bar_w, 18, 9, COLOR_TRACK);
            if (filled > 0)
                round_rect(pixels, 55, 152, filled, 18, 9, COLOR_ACCENT);

            // обложка
            const u32 *cover = library_cover(game->title_id);
            if (cover)
                draw_cover(pixels, W - 55 - COVER_SIZE, 30, cover, COLOR_BG, 18);
            else
                round_rect(pixels, W - 55 - COVER_SIZE, 30, COVER_SIZE,
                           COVER_SIZE, 18, COLOR_PANEL);

            set_text_color(150, 155, 165);
            draw_text(face_small, pixels, 55, 200, "ACHIEVEMENTS");
            reset_text_color();
        }

        // кнопка Guide поверх всего
        {
            const int size = 52;
            const int bx = 55;
            const int by = H - 85;

            round_rect(pixels, bx, by, size, size, size / 2, COLOR_PANEL);

            int glyph_w = measure_text(face, "!");
            set_text_color(235, 240, 250);
            draw_text(face, pixels, bx + (size * 2 / 3) - glyph_w / 2,
                      by + size / 2 + 10, "!");
            reset_text_color();
        }

        if (guide_open)
            draw_guide(face, face_small, pixels);

        framebufferEnd(&fb);

        shine_counter = (u32)(shine_counter + 22);
        marquee_counter = (marquee_counter + 2) % 100000;
    }

    if (net_ready) net_exit();
    ach_icons_clear();
    history_save();
    save_exit();
    library_exit();
    if (romfs_ready) romfsExit();
    framebufferClose(&fb);
    FT_Done_Face(face_small);
    FT_Done_Face(face);
    FT_Done_FreeType(ft);
    plExit();
    return 0;
}
