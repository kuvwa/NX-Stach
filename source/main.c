#include <switch.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <sys/stat.h>

#include "steam.h"
#include "save.h"
#include "net.h"
#include "gamesave.h"
#include "library.h"
#include "history.h"
#include "recipe.h"

#include <ft2build.h>
#include FT_FREETYPE_H

#include "stb_image.h"

#define W 1280
#define H 720
#define MAX_ACHIEVEMENTS 100

// сетка карточек
#define CARD_W 175
#define CARD_H 175
#define GRID_COLS 6
#define GRID_GAP_X 30
#define GRID_GAP_Y 30
#define GRID_STEP_X (CARD_W + GRID_GAP_X)
#define GRID_STEP_Y (CARD_H + GRID_GAP_Y)
#define GRID_Y0 178
#define HEADER_H 150

#define ACH_ICON_SIZE 44
#define ROW_H 72
#define SECTION_H 40
#define LIST_TOP 342
#define LIST_BOTTOM 700

#define COLOR_BG      RGBA8_MAXALPHA(24, 26, 30)
#define COLOR_PANEL   RGBA8_MAXALPHA(44, 47, 52)
#define COLOR_TRACK   RGBA8_MAXALPHA(60, 64, 70)
#define COLOR_ACCENT  RGBA8_MAXALPHA(120, 200, 255)
#define COLOR_LINE    RGBA8_MAXALPHA(48, 51, 57)
#define COLOR_SELECT  RGBA8_MAXALPHA(240, 243, 248)

static u32 fb_width;
static int clip_left = 0;
static int clip_right = W;
static int clip_top = 0;
static int clip_bottom = H;

static u8 text_r = 255, text_g = 255, text_b = 255;

static int measure_text(FT_Face face, const char *str);
static u32 blend_px(u32 bg, u32 fg, int a);

static void set_text_color(u8 r, u8 g, u8 b) { text_r = r; text_g = g; text_b = b; }
static void reset_text_color(void) { set_text_color(255, 255, 255); }

/* ------------------------------- рисование ------------------------------- */

static void fill_bg(u32 *fb, u32 color)
{
    for (int j = 0; j < H; j++)
        for (int i = 0; i < W; i++)
            fb[(size_t)j * fb_width + i] = color;
}

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

            if (px < clip_left || px >= clip_right) continue;
            if (py < clip_top || py >= clip_bottom) continue;

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

static void draw_text_right(FT_Face face, u32 *fb, int right, int y, const char *str)
{
    draw_text(face, fb, right - measure_text(face, str), y, str);
}

static void draw_text_shine(FT_Face face, u32 *fb, int x, int y,
                            const char *str, int phase)
{
    int index = 0;

    for (const unsigned char *p = (const unsigned char *)str; *p;) {
        u32 c;
        int n = decode_utf8(&c, p);
        if (n <= 0) break;
        p += n;

        int wave = (phase + index * 26) % 480;
        if (wave > 240) wave = 480 - wave;

        float k = (float)wave / 240.0f;

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

static void draw_cover(u32 *fb, int x, int y, int size, const u32 *cover,
                       u32 corner_color, int radius)
{
    for (int j = 0; j < size; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;
        if (x < 0 || x + size > W) continue;

        int sy = j * LIB_COVER_H / size;

        for (int i = 0; i < size; i++)
            fb[(size_t)py * fb_width + x + i] =
                cover[(size_t)sy * LIB_COVER_W + i * LIB_COVER_W / size];
    }

    round_corners(fb, x, y, size, size, radius, corner_color);
}

// Тумблер: пилюля со светлой окантовкой, синяя когда включён,
// и «резиновая» кнопка, которая вытягивается в процессе переключения.
static void draw_toggle(u32 *fb, int x, int y, float t)
{
    const int w = 64, h = 34;

    u32 on  = RGBA8_MAXALPHA(30, 144, 255);
    u32 off = RGBA8_MAXALPHA(70, 74, 82);

    // окантовка
    round_rect(fb, x, y, w, h, h / 2, RGBA8_MAXALPHA(196, 201, 210));

    // дорожка
    round_rect(fb, x + 2, y + 2, w - 4, h - 4, (h - 4) / 2,
               blend_px(off, on, (int)(255.0f * t)));

    // кнопка: вытягивается на середине пути
    int knob_h = 24;
    int stretch = (int)(13.0f * 4.0f * t * (1.0f - t));
    int knob_w = knob_h + stretch;

    int pad = 5;
    int travel = (w - pad * 2) - knob_w;
    if (travel < 0) travel = 0;

    int kx = x + pad + (int)((float)travel * t);
    int ky = y + (h - knob_h) / 2;

    // лёгкая тень
    round_rect(fb, kx + 1, ky + 1, knob_w, knob_h, knob_h / 2,
               blend_px(RGBA8_MAXALPHA(40, 42, 48), RGBA8_MAXALPHA(0, 0, 0), 60));

    round_rect(fb, kx, ky, knob_w, knob_h, knob_h / 2,
               RGBA8_MAXALPHA(250, 251, 254));
}

static void draw_scrollbar(u32 *fb, int x, int y, int h, int content, int view, int scroll)
{
    if (content <= view) return;

    round_rect(fb, x, y, 5, h, 3, COLOR_TRACK);

    int thumb_h = h * view / content;
    if (thumb_h < 40) thumb_h = 40;

    int max_scroll = content - view;
    int pos = max_scroll > 0 ? (h - thumb_h) * scroll / max_scroll : 0;

    round_rect(fb, x, y + pos, 5, thumb_h, 3, RGBA8_MAXALPHA(150, 155, 165));
}

static u32 blend_px(u32 bg, u32 fg, int a)
{
    if (a <= 0) return bg;
    if (a >= 255) return fg;

    int br = bg & 0xFF, bg_g = (bg >> 8) & 0xFF, bb = (bg >> 16) & 0xFF;
    int fr = fg & 0xFF, fg_g = (fg >> 8) & 0xFF, fb_ = (fg >> 16) & 0xFF;

    int r = br + (fr - br) * a / 255;
    int g = bg_g + (fg_g - bg_g) * a / 255;
    int b = bb + (fb_ - bb) * a / 255;

    return RGBA8_MAXALPHA(r, g, b);
}

// Матовое стекло поверх прямоугольного участка кадра.
static void glass_region(u32 *fb, int x, int y, int w, int h,
                         int block, int alpha, int radius)
{
    if (w <= 0 || h <= 0) return;

    int sw = (w + block - 1) / block;
    int sh = (h + block - 1) / block;

    u32 *small = malloc((size_t)sw * sh * sizeof(u32));

    if (!small) return;

    for (int sy = 0; sy < sh; sy++) {
        for (int sx = 0; sx < sw; sx++) {
            int r = 0, g = 0, b = 0, n = 0;

            for (int j = 0; j < block; j++) {
                int py = y + sy * block + j;
                if (py < 0 || py >= H) continue;

                for (int i = 0; i < block; i++) {
                    int px = x + sx * block + i;
                    if (px < 0 || px >= W) continue;

                    u32 c = fb[(size_t)py * fb_width + px];
                    r += c & 0xFF;
                    g += (c >> 8) & 0xFF;
                    b += (c >> 16) & 0xFF;
                    n++;
                }
            }

            if (!n) n = 1;
            small[(size_t)sy * sw + sx] = RGBA8_MAXALPHA(r / n, g / n, b / n);
        }
    }

    for (int j = 0; j < h; j++) {
        int py = y + j;
        if (py < 0 || py >= H) continue;

        int iy = j / block, ty = j % block;
        int iy1 = (iy + 1 < sh) ? iy + 1 : iy;

        for (int i = 0; i < w; i++) {
            int px = x + i;
            if (px < 0 || px >= W) continue;

            if (radius > 0 && j >= h - radius) {
                int dy = j - (h - radius);
                if (dy * dy > radius * radius) continue;
            }

            int ix = i / block, tx = i % block;
            int ix1 = (ix + 1 < sw) ? ix + 1 : ix;

            u32 c00 = small[(size_t)iy * sw + ix];
            u32 c10 = small[(size_t)iy * sw + ix1];
            u32 c01 = small[(size_t)iy1 * sw + ix];
            u32 c11 = small[(size_t)iy1 * sw + ix1];

            int r = 0, g = 0, b = 0;

            for (int k = 0; k < 2; k++) {
                int wy = k ? ty : (block - ty);
                u32 t = k ? c01 : c00;
                u32 bo = k ? c11 : c10;

                for (int m = 0; m < 2; m++) {
                    int wx = m ? tx : (block - tx);
                    u32 c = m ? bo : t;
                    int wgt = wx * wy;

                    r += (c & 0xFF) * wgt;
                    g += ((c >> 8) & 0xFF) * wgt;
                    b += ((c >> 16) & 0xFF) * wgt;
                }
            }

            int div = block * block;
            u32 blurred = RGBA8_MAXALPHA(r / div, g / div, b / div);

            fb[(size_t)py * fb_width + px] =
                blend_px(blurred, RGBA8_MAXALPHA(12, 13, 17), alpha);
        }
    }

    free(small);
}

// Очень мягкое свечение вокруг карточки (несколько слоёв + затухание).
static void draw_glow(u32 *fb, int x, int y, int size, int radius,
                      int spread, u32 color, int strength)
{
    int cx = x + size / 2;
    int cy = y + size / 2;
    int half = size / 2;
    int outer = half + spread;
    int inner = half - radius;

    for (int py = cy - outer; py <= cy + outer; py++) {
        if (py < 0 || py >= H) continue;

        for (int px = cx - outer; px <= cx + outer; px++) {
            if (px < 0 || px >= W) continue;

            int dx = abs(px - cx) - inner;
            int dy = abs(py - cy) - inner;

            if (dx < 0) dx = 0;
            if (dy < 0) dy = 0;

            float d = sqrtf((float)(dx * dx + dy * dy)) - (float)radius;

            if (d < 0.0f || d > (float)spread) continue;

            float t = 1.0f - d / (float)spread;
            t = t * t * (3.0f - 2.0f * t);

            int a = (int)((float)strength * t);
            if (a <= 0) continue;

            u32 *dst = &fb[(size_t)py * fb_width + px];
            *dst = blend_px(*dst, color, a);
        }
    }
}

#define HEADER_BG_H 260

static u32 *header_bg = NULL;
static int header_bg_ready = 0;

// Фон шапки: самый частый цвет обложки, затемнённый и растянутый в градиент.
static void build_header_bg(u64 title_id)
{
    header_bg_ready = 0;

    if (!header_bg) {
        header_bg = malloc((size_t)W * HEADER_BG_H * sizeof(u32));
        if (!header_bg) return;
    }

    library_cover(title_id);

    u32 dom = library_dominant_color(title_id);

    if (!dom)
        dom = library_cover_color(title_id);

    if (!dom) {
        for (int y = 0; y < HEADER_BG_H; y++)
            for (int x = 0; x < W; x++)
                header_bg[(size_t)y * W + x] = COLOR_BG;

        header_bg_ready = 1;
        return;
    }

    // вытягиваем цвет наверх по яркости, чтобы тёмные обложки тоже светились
    int cr = dom & 0xFF;
    int cg = (dom >> 8) & 0xFF;
    int cb = (dom >> 16) & 0xFF;

    int mx = cr > cg ? (cr > cb ? cr : cb) : (cg > cb ? cg : cb);

    if (mx > 0 && mx < 210) {
        int k = 210 * 100 / mx;
        cr = cr * k / 100;
        cg = cg * k / 100;
        cb = cb * k / 100;

        if (cr > 235) cr = 235;
        if (cg > 235) cg = 235;
        if (cb > 235) cb = 235;
    }

    u32 bright = RGBA8_MAXALPHA(cr, cg, cb);
    u32 base = blend_px(bright, RGBA8_MAXALPHA(10, 11, 14), 60);

    for (int y = 0; y < HEADER_BG_H; y++) {
        float t = 1.0f - (float)y / (float)HEADER_BG_H;
        t = powf(t, 1.7f);

        int alpha = (int)(238.0f * t);

        u32 color = blend_px(COLOR_BG, base, alpha);

        for (int x = 0; x < W; x++)
            header_bg[(size_t)y * W + x] = color;
    }

    header_bg_ready = 1;
}

static void draw_header_bg(u32 *fb)
{
    if (!header_bg_ready || !header_bg) return;

    for (int y = 0; y < HEADER_BG_H; y++) {
        if (y >= H) break;
        memcpy(fb + (size_t)y * fb_width, header_bg + (size_t)y * W,
               (size_t)W * sizeof(u32));
    }
}

/* --------------------------- ачивки: иконки --------------------------- */

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
                red = (u8)(red * 38 / 100);
                green = (u8)(green * 38 / 100);
                blue = (u8)(blue * 38 / 100);
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

static const char *g_ach_names[MAX_ACHIEVEMENTS];
static int g_ach_name_count = 0;

static void fill_ach_names(const SteamAchievement *achievements, int count)
{
    g_ach_name_count = 0;

    for (int i = 0; i < count && i < MAX_ACHIEVEMENTS; i++) {
        g_ach_names[i] = achievements[i].id;
        g_ach_name_count = i + 1;
    }
}

static int load_save_flags(u64 title_id, const char *appid,
                           u8 *flags, int max_flags)
{
    Recipe recipe;

    if (!recipe_load(title_id, appid, &recipe))
        return -1;

    return recipe_read_flags(&recipe, g_ach_names, g_ach_name_count,
                             flags, max_flags);
}

static bool achievement_unlocked(const char *appid, int index,
                                 const SteamAchievement *achievement,
                                 const u8 *flags, int flag_count)
{
    if (flag_count > 0)
        return index >= 0 && index < flag_count && flags[index] != 0;

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
    swkbdConfigSetGuideText(&kbd, "Поиск игры");

    char buffer[64] = {0};
    Result rc = swkbdShow(&kbd, buffer, sizeof(buffer));

    swkbdClose(&kbd);

    if (R_FAILED(rc))
        return false;

    snprintf(out, size, "%s", buffer);
    return true;
}

/* ------------------------------ список строк ------------------------------ */

typedef struct {
    int kind;
    int ach;
    const char *label;
    int y;
    int height;
} ListRow;

static ListRow list_rows[MAX_ACHIEVEMENTS * 2 + 8];
static int list_row_count = 0;
static int list_total_height = 0;
static int list_unlocked = 0;
static int list_locked = 0;

static void build_list(const char *appid, const SteamAchievement *achievements,
                       int count, const u8 *flags, int flag_count,
                       bool only_locked)
{
    list_row_count = 0;
    list_unlocked = 0;
    list_locked = 0;

    for (int i = 0; i < count; i++) {
        if (achievement_unlocked(appid, i, &achievements[i], flags, flag_count))
            list_unlocked++;
        else
            list_locked++;
    }

    int y = 0;

    if (list_unlocked > 0 && !only_locked) {
        ListRow *row = &list_rows[list_row_count++];
        row->kind = 0;
        row->label = "ПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ";
        row->ach = list_unlocked;
        row->y = y;
        row->height = SECTION_H;
        y += SECTION_H;

        for (int i = 0; i < count; i++) {
            if (!achievement_unlocked(appid, i, &achievements[i], flags, flag_count))
                continue;

            row = &list_rows[list_row_count++];
            row->kind = 1;
            row->ach = i;
            row->y = y;
            row->height = ROW_H;
            y += ROW_H;
        }
    }

    if (list_locked > 0) {
        ListRow *row = &list_rows[list_row_count++];
        row->kind = 0;
        row->label = "НЕПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ";
        row->ach = list_locked;
        row->y = y;
        row->height = SECTION_H;
        y += SECTION_H;

        for (int i = 0; i < count; i++) {
            if (achievement_unlocked(appid, i, &achievements[i], flags, flag_count))
                continue;

            row = &list_rows[list_row_count++];
            row->kind = 1;
            row->ach = i;
            row->y = y;
            row->height = ROW_H;
            y += ROW_H;
        }
    }

    list_total_height = y;
}

static void draw_progress(Framebuffer *fb, FT_Face face, FT_Face face_small,
                          const char *title, const char *line, int percent)
{
    u32 stride;
    u32 *px = (u32 *)framebufferBegin(fb, &stride);
    fb_width = stride / sizeof(u32);

    fill_bg(px, COLOR_BG);

    clip_left = 0;
    clip_right = W;
    clip_top = 0;
    clip_bottom = H;

    draw_text(face, px, 55, 300, title);

    set_text_color(170, 175, 185);
    draw_text(face_small, px, 55, 340, line);
    reset_text_color();

    round_rect(px, 55, 370, 1170, 16, 8, COLOR_TRACK);

    if (percent > 0)
        round_rect(px, 55, 370, 1170 * percent / 100, 16, 8, COLOR_ACCENT);

    framebufferEnd(fb);
}

/* ------------------------------- стики ------------------------------- */

typedef struct {
    int dir_x;
    int dir_y;
    int frames;
} StickRepeat;

static void stick_update(StickRepeat *st, HidAnalogStickState raw,
                         int *out_x, int *out_y)
{
    int dx = 0, dy = 0;

    if (raw.x > 16000) dx = 1;
    else if (raw.x < -16000) dx = -1;

    if (raw.y > 16000) dy = 1;
    else if (raw.y < -16000) dy = -1;

    *out_x = 0;
    *out_y = 0;

    if (dx == 0 && dy == 0) {
        st->frames = 0;
        st->dir_x = 0;
        st->dir_y = 0;
        return;
    }

    if (dx != st->dir_x || dy != st->dir_y) {
        st->dir_x = dx;
        st->dir_y = dy;
        st->frames = 0;
        *out_x = dx;
        *out_y = dy;
        return;
    }

    st->frames++;

    if (st->frames > 16 && (st->frames % 4) == 0) {
        *out_x = dx;
        *out_y = dy;
    }
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

    int view[MAX_GAMES];
    int view_count = 0;

    SteamAchievement achievements[MAX_ACHIEVEMENTS] = {0};
    int achievement_count = 0;
    int unlocked_count = 0;

    u8 flags[MAX_ACHIEVEMENTS] = {0};
    int flag_count = 0;

    u32 playtime_minutes = 0;

    char search[64] = "";

    int selected = 0;
    int screen = 0;
    int only_locked = 0;
    int follow_selection = 0;
    float hover_anim = 0.0f;

    float grid_scroll = 0.0f, grid_target = 0.0f;
    float list_scroll = 0.0f, list_target = 0.0f;
    float drag_velocity = 0.0f;

    u32 shine_counter = 0;
    u32 tick = 0;
    float pulse = 1.0f;
    float toggle_anim = 0.0f;

    char toast[160] = "";
    int toast_frames = 0;

    bool touch_down = false;
    int touch_start_x = 0, touch_start_y = 0;
    int touch_last_x = 0, touch_last_y = 0;
    bool touch_dragged = false;
    bool touch_tapped = false;
    int tap_x = 0, tap_y = 0;

    StickRepeat stick_left = {0};
    StickRepeat stick_right = {0};
    int hold_frames = 0;

    for (int i = 0; i < game_count; i++)
        view[view_count++] = i;

    while (appletMainLoop()) {
        padUpdate(&pad);
        u32 kDown = padGetButtonsDown(&pad);
        u32 held = padGetButtons(&pad);

        if (kDown & HidNpadButton_Plus) break;

        /* ------------------------------- тач ------------------------------- */
        HidTouchScreenState touch_state = {0};
        touch_tapped = false;

        if (hidGetTouchScreenStates(&touch_state, 1) > 0 &&
            touch_state.count > 0) {
            int tx = (int)touch_state.touches[0].x;
            int ty = (int)touch_state.touches[0].y;

            if (!touch_down) {
                touch_down = true;
                touch_dragged = false;
                touch_start_x = tx;
                touch_start_y = ty;
            } else {
                int dy = ty - touch_last_y;

                if (abs(tx - touch_start_x) > 10 ||
                    abs(ty - touch_start_y) > 10)
                    touch_dragged = true;

                if (touch_dragged) {
                    drag_velocity = drag_velocity * 0.6f + (float)dy * 0.4f;

                    if (screen == 0) {
                        grid_scroll -= (float)dy;
                        grid_target = grid_scroll;
                    } else {
                        list_scroll -= (float)dy;
                        list_target = list_scroll;
                    }
                }
            }

            touch_last_x = tx;
            touch_last_y = ty;
        } else if (touch_down) {
            touch_down = false;

            if (touch_dragged) {
                float fling = -drag_velocity * 8.0f;

                if (screen == 0) grid_target += fling;
                else list_target += fling;
            } else {
                touch_tapped = true;
                tap_x = touch_last_x;
                tap_y = touch_last_y;
            }

            drag_velocity = 0.0f;
            touch_dragged = false;
        }

        bool consumed = false;

        /* ------------------------------- тапы ------------------------------- */
        if (touch_tapped) {
            if (screen == 0) {
                if (tap_y >= 82 && tap_y <= 134) {
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

                    consumed = true;
                } else if (tap_y >= GRID_Y0) {
                    int row = (int)(((float)tap_y + grid_scroll - GRID_Y0) /
                                    (float)GRID_STEP_Y);
                    int col = (tap_x - (W - (GRID_COLS * GRID_STEP_X - GRID_GAP_X)) / 2) /
                              GRID_STEP_X;

                    if (col >= 0 && col < GRID_COLS && row >= 0) {
                        int position = row * GRID_COLS + col;

                        if (position < view_count) {
                            selected = position;
                            kDown |= HidNpadButton_A;
                        }
                    }
                }
            } else {
                if (tap_x >= 45 && tap_x <= 115 && tap_y >= 20 && tap_y <= 90) {
                    screen = 0;
                    ach_icons_clear();
                    consumed = true;
                } else if (tap_y >= 30 && tap_y <= 78 && tap_x >= 980) {
                    kDown |= HidNpadButton_Y;
                } else if (tap_y >= 276 && tap_y <= 332) {
                    only_locked = !only_locked;
                    list_scroll = list_target = 0.0f;
                    consumed = true;
                }
            }
        }

        /* ----------------------------- навигация ----------------------------- */
        if (!consumed) {
            if (screen == 0 && (kDown & HidNpadButton_B) && search[0]) {
                search[0] = '\0';
                selected = 0;
                grid_scroll = grid_target = 0.0f;

                view_count = 0;
                for (int i = 0; i < game_count; i++)
                    view[view_count++] = i;

                consumed = true;
            }

            if (!consumed && screen == 0 && (kDown & HidNpadButton_Y)) {
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

                consumed = true;
            }

            if (!consumed && screen == 0) {
                if (view_count > 0) {
                    if (kDown & HidNpadButton_Right) {
                        selected = (selected + 1) % view_count;
                        follow_selection = 1;
                    }
                    if (kDown & HidNpadButton_Left) {
                        selected = (selected + view_count - 1) % view_count;
                        follow_selection = 1;
                    }
                    if (kDown & HidNpadButton_Down) {
                        int next = selected + GRID_COLS;
                        if (next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }
                    if (kDown & HidNpadButton_Up) {
                        int next = selected - GRID_COLS;
                        if (next >= 0) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }
                }

                int sx = 0, sy = 0;

                stick_update(&stick_left, padGetStickPos(&pad, 0), &sx, &sy);

                if (view_count > 0) {
                    if (sx) {
                        selected = (selected + sx + view_count) % view_count;
                        follow_selection = 1;
                    }
                    if (sy) {
                        int next = selected - sy * GRID_COLS;

                        if (next >= 0 && next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }
                }

                stick_update(&stick_right, padGetStickPos(&pad, 1), &sx, &sy);

                if (sy)
                    grid_target -= (float)sy * (float)GRID_STEP_Y;

                if ((kDown & HidNpadButton_A) && view_count > 0) {
                    const Game *game = &games[view[selected]];

                    achievement_count = 0;
                    unlocked_count = 0;
                    flag_count = 0;
                    only_locked = 0;
                    list_scroll = list_target = 0.0f;

                    if (game->steam_appid[0]) {
                        achievement_count = romfs_ready
                            ? load_catalog(game->steam_appid, achievements,
                                           MAX_ACHIEVEMENTS)
                            : 0;

                        if (achievement_count <= 0 && net_ready) {
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

                        flag_count = load_save_flags(game->title_id, game->steam_appid,
                                                     flags, MAX_ACHIEVEMENTS);

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

                    fill_ach_names(achievements, achievement_count);
                    ach_icons_load(game->steam_appid, achievement_count, achievements);
                    playtime_minutes = game_playtime_minutes(game->title_id);
                    build_header_bg(game->title_id);

                    screen = 1;
                }
            } else if (screen == 1) {
                if (kDown & HidNpadButton_Y) {
                    Game *g = &games[view[selected]];

                    draw_progress(&fb, face, face_small, g->name,
                                  "Выгружаем сейв на карту...", 40);

                    int copied = gamesave_dump_to_sd(g->title_id);

                    if (copied > 0) {
                        snprintf(toast, sizeof(toast),
                                 "Сейв выгружен: %d файлов (dumps/%016llX)",
                                 copied, (unsigned long long)g->title_id);
                    } else {
                        snprintf(toast, sizeof(toast), "Сейв не найден или пуст");
                    }

                    toast_frames = 260;
                }

                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }

                if (kDown & HidNpadButton_Down) list_target += ROW_H;
                if (kDown & HidNpadButton_Up) list_target -= ROW_H;

                int sx = 0, sy = 0;

                stick_update(&stick_left, padGetStickPos(&pad, 0), &sx, &sy);
                if (sy) list_target -= (float)sy * (float)ROW_H;

                stick_update(&stick_right, padGetStickPos(&pad, 1), &sx, &sy);
                if (sy) list_target -= (float)sy * (float)ROW_H;
            }

            if (held & (HidNpadButton_Down | HidNpadButton_Up)) {
                hold_frames++;

                if (hold_frames > 30 && (hold_frames % 4) == 0) {
                    int step = (held & HidNpadButton_Down) ? 1 : -1;

                    if (screen == 0 && view_count > 0) {
                        int next = selected + step * GRID_COLS;

                        if (next >= 0 && next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    } else if (screen == 1) {
                        list_target += step * ROW_H;
                    }
                }
            } else {
                hold_frames = 0;
            }
        }

        /* --------------------------- ограничение скролла --------------------------- */
        {
            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            float content = (float)rows * GRID_STEP_Y;
            float visible = (float)(H - GRID_Y0);
            float max_scroll = content - visible;

            if (max_scroll < 0) max_scroll = 0;

            if (follow_selection) {
                hover_anim = 0.55f;
                int row = selected / GRID_COLS;
                float top = (float)row * GRID_STEP_Y;
                float bottom = top + GRID_STEP_Y;

                if (top < grid_target) grid_target = top;
                if (bottom > grid_target + visible)
                    grid_target = bottom - visible;

                follow_selection = 0;
            }

            if (grid_target < 0) grid_target = 0;
            if (grid_target > max_scroll) grid_target = max_scroll;
            if (grid_scroll < 0) grid_scroll = 0;
            if (grid_scroll > max_scroll) grid_scroll = max_scroll;

            if (!touch_dragged)
                grid_scroll += (grid_target - grid_scroll) * 0.13f;
        }

        {
            float view_h = (float)(LIST_BOTTOM - LIST_TOP);
            float max_scroll = (float)list_total_height - view_h;

            if (max_scroll < 0) max_scroll = 0;

            if (list_target < 0) list_target = 0;
            if (list_target > max_scroll) list_target = max_scroll;
            if (list_scroll < 0) list_scroll = 0;
            if (list_scroll > max_scroll) list_scroll = max_scroll;

            if (!touch_dragged)
                list_scroll += (list_target - list_scroll) * 0.14f;
        }

        /* ------------------------------ отрисовка ------------------------------ */
        u32 stride;
        u32 *pixels = (u32 *)framebufferBegin(&fb, &stride);
        fb_width = stride / sizeof(u32);

        fill_bg(pixels, COLOR_BG);
        clip_top = 0;
        clip_bottom = H;

        if (screen == 0) {
            int grid_x0 = (W - (GRID_COLS * GRID_STEP_X - GRID_GAP_X)) / 2;

            for (int i = 0; i < view_count; i++) {
                int col = i % GRID_COLS;
                int row = i / GRID_COLS;

                int x = grid_x0 + col * GRID_STEP_X;
                int y = GRID_Y0 + (int)((float)row * GRID_STEP_Y - grid_scroll);

                if (y + CARD_H < HEADER_H) continue;
                if (y > H) continue;

                int game_index = view[i];
                const u32 *cover = library_cover(games[game_index].title_id);

                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);
                    int grow = (int)(hover_anim * 4.0f);

                    u32 glow_dark = blend_px(glow, RGBA8_MAXALPHA(0, 0, 0), 90);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 30 + grow, glow_dark,
                              (int)(30 + 30 * pulse));

                    u32 frame = blend_px(COLOR_BG, COLOR_SELECT,
                                         (int)(120 + 130 * pulse));

                    round_rect(pixels, x - 3, y - 3, CARD_W + 6, CARD_H + 6,
                               10, frame);
                }

                if (cover)
                    draw_cover(pixels, x, y, CARD_W, cover,
                               i == selected ? COLOR_SELECT : COLOR_BG, 8);
                else
                    round_rect(pixels, x, y, CARD_W, CARD_H, 8, COLOR_PANEL);

                if (i == selected) {
                    // стеклянная плашка с названием
                    int strip_h = 44;
                    int strip_y = y + CARD_H - strip_h;

                    glass_region(pixels, x, strip_y, CARD_W, strip_h,
                                 5, 130, 0);

                    round_corners(pixels, x, y, CARD_W, CARD_H, 8,
                                  i == selected ? COLOR_SELECT : COLOR_BG);

                    clip_left = x + 8;
                    clip_right = x + CARD_W - 8;
                    clip_top = strip_y;
                    clip_bottom = y + CARD_H;

                    const char *name = games[game_index].name;
                    int name_w = measure_text(face_small, name);
                    int cycle = name_w + 40;
                    if (cycle < 1) cycle = 1;

                    int shift = (name_w > CARD_W - 20)
                        ? (int)(tick % (u32)cycle) : 0;

                    set_text_color(248, 250, 253);
                    draw_text(face_small, pixels, x + 10 - shift,
                              strip_y + 30, name);
                    if (name_w > CARD_W - 20)
                        draw_text(face_small, pixels, x + 10 - shift + cycle,
                                  strip_y + 30, name);
                    reset_text_color();

                    clip_left = 0;
                    clip_right = W;
                    clip_top = 0;
                    clip_bottom = H;
                }
            }

            rect(pixels, 0, 0, W, HEADER_H, COLOR_BG);

            draw_text_shine(face, pixels, 55, 62, "NX-Stach", (int)shine_counter);

            round_rect(pixels, 55, 82, 1170, 52, 14, COLOR_PANEL);

            if (search[0]) {
                set_text_color(230, 232, 238);
                draw_text(face_small, pixels, 78, 116, search);
            } else {
                set_text_color(120, 125, 135);
                draw_text(face_small, pixels, 78, 116, "Поиск...");
            }
            reset_text_color();

            set_text_color(110, 115, 125);
            draw_text(face_small, pixels, W - 90, 116, "Y");
            reset_text_color();

            if (view_count == 0) {
                set_text_color(150, 155, 165);
                draw_text(face, pixels, 55, 320, "Ничего не найдено");
                reset_text_color();
            }

            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            draw_scrollbar(pixels, W - 22, GRID_Y0, H - GRID_Y0 - 20,
                           rows * GRID_STEP_Y, H - GRID_Y0,
                           (int)grid_scroll);
        } else if (view_count > 0) {
            const Game *game = &games[view[selected]];

            build_list(game->steam_appid, achievements, achievement_count,
                       flags, flag_count, only_locked != 0);

            if (achievement_count <= 0) {
                set_text_color(150, 155, 165);
                draw_text(face_small, pixels, 55, 410, "Нет каталога достижений");
                draw_text(face_small, pixels, 55, 440,
                          game->steam_appid[0]
                          ? "Проверь romfs:/catalog/ и Steam AppID"
                          : "У игры не указан Steam AppID");
                reset_text_color();
            }

            clip_top = LIST_TOP;
            clip_bottom = LIST_BOTTOM;

            int offset = (int)list_scroll;

            for (int i = 0; i < list_row_count; i++) {
                ListRow *row = &list_rows[i];

                int y = LIST_TOP + row->y - offset;

                if (y + row->height < LIST_TOP) continue;
                if (y > LIST_BOTTOM) break;

                if (row->kind == 0) {
                    char header[96];
                    snprintf(header, sizeof(header), "%s (%d)",
                             row->label, row->ach);
                    set_text_color(150, 155, 165);
                    draw_text(face_small, pixels, 55, y + 26, header);
                    reset_text_color();
                    continue;
                }

                int index = row->ach;
                bool unlocked = achievement_unlocked(game->steam_appid, index,
                                                     &achievements[index],
                                                     flags, flag_count);

                if (ach_icons[index])
                    draw_achievement_icon(pixels, 55, y + 6, ach_icons[index], !unlocked);
                else
                    round_rect(pixels, 55, y + 6, ACH_ICON_SIZE, ACH_ICON_SIZE, 8,
                               RGBA8_MAXALPHA(32, 34, 38));

                if (unlocked) set_text_color(210, 245, 215);
                else set_text_color(180, 185, 195);

                clip_left = 120;
                clip_right = 1010;
                draw_text(face_small, pixels, 120, y + 26, achievements[index].name);
                clip_left = 0;
                clip_right = W;

                set_text_color(130, 135, 145);
                clip_left = 120;
                clip_right = 1010;
                draw_text(face_small, pixels, 120, y + 50, achievements[index].description);
                clip_left = 0;
                clip_right = W;
                reset_text_color();

                if (unlocked) {
                    char date[40];
                    char line[64];

                    format_date(history_get(game->steam_appid, achievements[index].id),
                                date, sizeof(date));

                    if (date[0]) {
                        snprintf(line, sizeof(line), "Получено %s", date);
                        set_text_color(130, 170, 140);
                        draw_text_right(face_small, pixels, 1195, y + 40, line);
                        reset_text_color();
                    }
                }

                rect(pixels, 55, y + row->height - 1, 1140, 1, COLOR_LINE);
            }

            clip_top = 0;
            clip_bottom = H;

            draw_scrollbar(pixels, W - 22, LIST_TOP, LIST_BOTTOM - LIST_TOP,
                           list_total_height, LIST_BOTTOM - LIST_TOP,
                           (int)list_scroll);

            rect(pixels, 0, 0, W, LIST_TOP - 6, COLOR_BG);
            draw_header_bg(pixels);

            const u32 *cover = library_cover(game->title_id);
            if (cover)
                draw_cover(pixels, 55, 38, 120, cover, COLOR_BG, 16);
            else
                round_rect(pixels, 55, 38, 120, 120, 16, COLOR_PANEL);

            clip_left = 200;
            clip_right = W - 40;
            draw_text(face, pixels, 200, 78, game->name);
            clip_left = 0;
            clip_right = W;

            char stats[192];

            if (playtime_minutes > 0)
                snprintf(stats, sizeof(stats),
                         "Достижения: %d / %d   |   Время в игре: %u ч %u м",
                         unlocked_count, achievement_count,
                         playtime_minutes / 60, playtime_minutes % 60);
            else
                snprintf(stats, sizeof(stats), "Достижения: %d / %d",
                         unlocked_count, achievement_count);

            set_text_color(160, 165, 175);
            draw_text(face_small, pixels, 200, 110, stats);
            reset_text_color();

            {
                const char *label = "Выгрузить сейв";
                int lw = measure_text(face_small, label);
                int bw = lw + 78;
                int bx = W - 55 - bw;
                int by = 34;

                round_rect(pixels, bx, by, bw, 40, 12, COLOR_PANEL);

                round_rect(pixels, bx + 12, by + 8, 24, 24, 12,
                           RGBA8_MAXALPHA(72, 77, 86));

                set_text_color(236, 241, 250);
                draw_text(face_small, pixels, bx + 18, by + 26, "Y");
                draw_text(face_small, pixels, bx + 46, by + 26, label);
                reset_text_color();
            }

            round_rect(pixels, 55, 176, 1170, 76, 16, COLOR_PANEL);

            int percent = achievement_count > 0
                ? unlocked_count * 100 / achievement_count : 0;

            char progress[96];
            snprintf(progress, sizeof(progress),
                     "Получено достижений: %d/%d (%d%%)",
                     unlocked_count, achievement_count, percent);

            set_text_color(220, 224, 232);
            draw_text(face_small, pixels, 85, 206, progress);
            reset_text_color();

            int bar_w = 1110;
            int filled = bar_w * percent / 100;

            round_rect(pixels, 85, 220, bar_w, 12, 6, COLOR_TRACK);
            if (filled > 0)
                round_rect(pixels, 85, 220, filled, 12, 6, COLOR_ACCENT);

            set_text_color(190, 195, 205);
            draw_text(face_small, pixels, 55, 306, "Только невыполненные");
            reset_text_color();

            draw_toggle(pixels, 1138, 277, toggle_anim);
        }

        if (toast_frames > 0) {
            int tw = measure_text(face_small, toast);
            int w = tw + 48;

            if (w > W - 80) w = W - 80;

            int x = (W - w) / 2;
            int y = H - 96;

            round_rect(pixels, x, y, w, 46, 14, RGBA8_MAXALPHA(52, 56, 63));

            clip_left = x + 20;
            clip_right = x + w - 20;
            set_text_color(235, 240, 250);
            draw_text(face_small, pixels, x + 24, y + 30, toast);
            reset_text_color();
            clip_left = 0;
            clip_right = W;

            toast_frames--;
        }

        framebufferEnd(&fb);

        tick++;
        pulse = 0.5f + 0.5f * sinf((float)tick * 0.055f);

        toggle_anim += ((only_locked ? 1.0f : 0.0f) - toggle_anim) * 0.16f;

        hover_anim += (1.0f - hover_anim) * 0.22f;
        shine_counter = (u32)(shine_counter + 30);
    }

    if (net_ready) net_exit();
    ach_icons_clear();
    history_save();
    save_exit();
    library_exit();
    if (romfs_ready) romfsExit();
    free(header_bg);
    framebufferClose(&fb);
    FT_Done_Face(face_small);
    FT_Done_Face(face);
    FT_Done_FreeType(ft);
    plExit();
    return 0;
}
