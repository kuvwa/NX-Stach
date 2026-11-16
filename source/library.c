#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <jansson.h>

#include "library.h"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#define CACHE_SLOTS 24
#define TITLE_ID_MASK 0xFFFFFFFFFFFFF000ULL
#define GAMES_JSON "sdmc:/switch/NX-Stach/games.json"

static NsApplicationControlData *control_buffer = NULL;
static bool ns_ready = false;

typedef struct {
    u64 title_id;
    u32 *pixels;
    u32 color;
    u32 dominant;
} CoverSlot;

static CoverSlot covers[CACHE_SLOTS];
static u32 last_color = RGBA8_MAXALPHA(120, 200, 255);
static int cover_next = 0;

bool library_online(void) { return ns_ready; }

u32 library_dominant_color(u64 title_id)
{
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++)
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].dominant;

    return 0;
}

u32 library_cover_color(u64 title_id)
{
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++)
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].color;

    return last_color;
}

static bool ensure_ns(void) {
    if (ns_ready) return true;
    if (R_FAILED(nsInitialize())) return false;
    if (!control_buffer) {
        control_buffer = malloc(sizeof(NsApplicationControlData));
        if (!control_buffer) {
            nsExit();
            return false;
        }
    }
    ns_ready = true;
    return true;
}

void library_exit(void) {
    for (int i = 0; i < CACHE_SLOTS; i++) {
        free(covers[i].pixels);
        covers[i].pixels = NULL;
        covers[i].title_id = 0;
    }
    free(control_buffer);
    control_buffer = NULL;
    if (ns_ready) {
        nsExit();
        ns_ready = false;
    }
}

static bool read_control(u64 title_id, u64 *actual_size) {
    if (!ensure_ns()) return false;

    u64 actual = 0;

    if (R_FAILED(nsGetApplicationControlData(
            NsApplicationControlSource_Storage, title_id,
            control_buffer, sizeof(NsApplicationControlData), &actual)))
        return false;

    if (actual <= sizeof(NacpStruct))
        return false;

    if (actual_size) *actual_size = actual;
    return true;
}

static bool read_name(u64 title_id, char *out, size_t size) {
    if (!read_control(title_id, NULL))
        return false;

    NacpLanguageEntry *lang = NULL;

    if (R_FAILED(nacpGetLanguageEntry(&control_buffer->nacp, &lang)) || !lang)
        return false;

    if (!lang->name[0])
        return false;

    size_t n = strlen(lang->name);
    if (n >= size) n = size - 1;
    memcpy(out, lang->name, n);
    out[n] = '\0';
    return true;
}

static void normalize_title_id_str(const char *in, u64 *out) {
    char tmp[64] = {0};
    size_t j = 0;

    if (in) {
        const char *p = in;
        while (*p == ' ') p++;
        if (p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) p += 2;

        for (; *p && j < sizeof(tmp) - 1; p++) {
            if (*p == ' ' || *p == '-' || *p == '_' || *p == '\t') continue;
            tmp[j++] = *p;
        }
    }

    *out = strtoull(tmp[0] ? tmp : "0", NULL, 16) & TITLE_ID_MASK;
}

static void merge_steam_ids(Game *games, int count) {
    if (count <= 0) return;

    json_error_t error;
    json_t *root = json_load_file(GAMES_JSON, 0, &error);
    if (!root) return;

    json_t *array = json_object_get(root, "games");

    if (json_is_array(array)) {
        size_t index;
        json_t *item;

        json_array_foreach(array, index, item) {
            const char *id = json_string_value(json_object_get(item, "switch_id"));
            const char *appid = json_string_value(json_object_get(item, "steam_app_id"));

            u64 title_id = 0;
            normalize_title_id_str(id, &title_id);

            if (!title_id) continue;

            for (int i = 0; i < count; i++) {
                if (games[i].title_id == title_id) {
                    snprintf(games[i].steam_appid, sizeof(games[i].steam_appid),
                             "%s", appid ? appid : "");
                    break;
                }
            }
        }
    }

    json_decref(root);
}

static int load_from_json(Game *games, int max_games) {
    json_error_t error;
    json_t *root = json_load_file(GAMES_JSON, 0, &error);
    if (!root) return 0;

    json_t *array = json_object_get(root, "games");
    int count = 0;

    if (json_is_array(array)) {
        size_t index;
        json_t *item;

        json_array_foreach(array, index, item) {
            if (count >= max_games) break;

            const char *id = json_string_value(json_object_get(item, "switch_id"));
            const char *name = json_string_value(json_object_get(item, "name"));
            const char *appid = json_string_value(json_object_get(item, "steam_app_id"));

            u64 title_id = 0;
            normalize_title_id_str(id, &title_id);

            if (!title_id) continue;

            games[count].title_id = title_id;
            snprintf(games[count].name, sizeof(games[count].name), "%s",
                     name ? name : "Unknown game");
            snprintf(games[count].steam_appid, sizeof(games[count].steam_appid),
                     "%s", appid ? appid : "");
            count++;
        }
    }

    json_decref(root);
    return count;
}


// Один образ на Switch может содержать несколько игр (например, Hotline Miami
// Collection). Здесь такие игры разворачиваются в отдельные плитки.
typedef struct {
    u64 title_id;
    const char *label;
    const char *steam_appid;
} Variant;

static const Variant VARIANTS[] = {
    { 0x0100D0E00E51E000ULL, "Hotline Miami", "219150" },
    { 0x0100D0E00E51E000ULL, "Hotline Miami 2: Wrong Number", "274170" },
    { 0x010093D00C726000ULL, "Downwell", "360740" },
    { 0x010031200B94C000ULL, "My Friend Pedro", "557340" },
};

static int expand_variants(Game *games, int count, int max_games) {
    Game out[MAX_GAMES];
    int n = 0;

    for (int i = 0; i < count && n < max_games; i++) {
        bool matched = false;

        for (unsigned v = 0; v < sizeof(VARIANTS) / sizeof(VARIANTS[0]); v++) {
            if (games[i].title_id != VARIANTS[v].title_id) continue;
            if (n >= max_games) break;

            out[n].title_id = games[i].title_id;
            snprintf(out[n].name, sizeof(out[n].name), "%s", VARIANTS[v].label);
            snprintf(out[n].steam_appid, sizeof(out[n].steam_appid), "%s",
                     VARIANTS[v].steam_appid);
            n++;
            matched = true;
        }

        if (!matched && n < max_games)
            out[n++] = games[i];
    }

    memcpy(games, out, sizeof(Game) * (size_t)n);
    return n;
}

static int compare_games(const void *a, const void *b) {
    return strcasecmp(((const Game *)a)->name, ((const Game *)b)->name);
}

// Отсекаем хоумбрю-лончеры, их в списке игр быть не должно.
static bool looks_like_homebrew(const char *name) {
    static const char *skip[] = {
        // эмуляторы
        "PPSSPP", "RetroArch", "melonDS", "mGBA", "DeSmuME", "Dolphin",
        "Citra", "yuzu", "Skyline", "Strato", "Flycast", "DuckStation",
        "Snes9x", "FCEUX", "Genesis Plus", "Mednafen", "Vita3K",
        // лончеры и установщики
        "hbmenu", "Homebrew", "DBI", "Goldleaf", "Awoo", "Tinfoil",
        "Appstore", "hb-appstore", "NUT", "ftpd", "sys-ftpd",
        // утилиты
        "NX-Shell", "NXThemes", "nx-themes", "EdiZon", "Checkpoint",
        "JKSV", "Lockpick", "TegraExplorer", "Hekate", "Fizeau",
        "sys-clk", "Status Monitor", "SimpleModManager",
        // стриминг
        "Moonlight", "Chiaki", "PSPlay", "Steam Link",
    };

    if (!name) return true;

    for (unsigned i = 0; i < sizeof(skip) / sizeof(skip[0]); i++) {
        size_t len = strlen(skip[i]);
        const char *p = name;

        while (*p) {
            if (strncasecmp(p, skip[i], len) == 0)
                return true;
            p++;
        }
    }

    return false;
}

int library_load(Game *games, int max_games) {
    if (!games || max_games <= 0)
        return 0;

    int count = 0;

    if (ensure_ns()) {
        NsApplicationRecord records[64];
        s32 offset = 0;

        while (count < max_games) {
            s32 got = 0;

            if (R_FAILED(nsListApplicationRecord(records, 64, offset, &got)) || got <= 0)
                break;

            if (got > 64) got = 64;

            for (s32 i = 0; i < got && count < max_games; i++) {
                u64 title_id = records[i].application_id & TITLE_ID_MASK;
                char name[128];

                if (!title_id) continue;
                if (!read_name(title_id, name, sizeof(name))) continue;
                if (looks_like_homebrew(name)) continue;

                games[count].title_id = title_id;
                snprintf(games[count].name, sizeof(games[count].name), "%s", name);
                games[count].steam_appid[0] = 0;
                count++;
            }

            offset += got;

            if (got < 64) break;
        }
    }

    if (count == 0)
        count = load_from_json(games, max_games);
    else
        merge_steam_ids(games, count);

    count = expand_variants(games, count, max_games);

    qsort(games, count, sizeof(Game), compare_games);

    return count;
}

const u32 *library_cover(u64 title_id) {
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++) {
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].pixels;
    }

    u64 actual = 0;

    if (!read_control(title_id, &actual))
        return NULL;

    if (actual <= sizeof(NacpStruct) ||
        actual > sizeof(NsApplicationControlData))
        return NULL;

    size_t icon_len = (size_t)(actual - sizeof(NacpStruct));

    if (icon_len > sizeof(control_buffer->icon))
        icon_len = sizeof(control_buffer->icon);

    if (icon_len < 128 || icon_len > (256 * 1024))
        return NULL;

    int width = 0, height = 0, channels = 0;

    stbi_uc *image = stbi_load_from_memory(
        control_buffer->icon, (int)icon_len,
        &width, &height, &channels, 4);

    if (!image || width <= 0 || height <= 0) {
        if (image) stbi_image_free(image);
        return NULL;
    }

    u32 *pixels = malloc((size_t)LIB_COVER_W * LIB_COVER_H * sizeof(u32));

    if (!pixels) {
        stbi_image_free(image);
        return NULL;
    }

    // центрируем и обрезаем под 270x190
    const float scale_x = (float)width / (float)LIB_COVER_W;
    const float scale_y = (float)height / (float)LIB_COVER_H;
    const float scale = scale_x > scale_y ? scale_x : scale_y;

    const float crop_w = (float)LIB_COVER_W * scale;
    const float crop_h = (float)LIB_COVER_H * scale;
    const float off_x = ((float)width - crop_w) / 2.0f;
    const float off_y = ((float)height - crop_h) / 2.0f;

    for (int y = 0; y < LIB_COVER_H; y++) {
        int sy = (int)(off_y + (float)y * scale);
        if (sy < 0) sy = 0;
        if (sy >= height) sy = height - 1;

        for (int x = 0; x < LIB_COVER_W; x++) {
            int sx = (int)(off_x + (float)x * scale);
            if (sx < 0) sx = 0;
            if (sx >= width) sx = width - 1;

            const stbi_uc *src = image + ((size_t)sy * width + sx) * 4;
            pixels[(size_t)y * LIB_COVER_W + x] =
                RGBA8_MAXALPHA(src[0], src[1], src[2]);
        }
    }

    stbi_image_free(image);

    int slot = cover_next;
    cover_next = (cover_next + 1) % CACHE_SLOTS;

    // средний цвет обложки — для подсветки
    u64 sr = 0, sg = 0, sb = 0, n = 0;

    for (int y = 0; y < LIB_COVER_H; y += 4) {
        for (int x = 0; x < LIB_COVER_W; x += 4) {
            u32 c = pixels[(size_t)y * LIB_COVER_W + x];
            sr += c & 0xFF;
            sg += (c >> 8) & 0xFF;
            sb += (c >> 16) & 0xFF;
            n++;
        }
    }

    int cr = 120, cg = 200, cb = 255;

    if (n > 0) {
        cr = (int)(sr / n);
        cg = (int)(sg / n);
        cb = (int)(sb / n);

        int mx = cr > cg ? (cr > cb ? cr : cb) : (cg > cb ? cg : cb);
        int k = mx > 0 ? 235 * 100 / mx : 100;
        if (k > 260) k = 260;

        cr = cr * k / 100;
        cg = cg * k / 100;
        cb = cb * k / 100;

        if (cr > 235) cr = 235;
        if (cg > 235) cg = 235;
        if (cb > 235) cb = 235;
    }

    // самый частый цвет (грубая гистограмма 4 бита на канал)
    static u16 hist[4096];
    for (int i = 0; i < 4096; i++) hist[i] = 0;

    for (int y = 0; y < LIB_COVER_H; y += 3) {
        for (int x = 0; x < LIB_COVER_W; x += 3) {
            u32 c = pixels[(size_t)y * LIB_COVER_W + x];
            int idx = (((c >> 4) & 0xF) << 8) |
                      (((c >> 12) & 0xF) << 4) |
                      ((c >> 20) & 0xF);
            if (hist[idx] < 60000) hist[idx]++;
        }
    }

    int best = 0;
    for (int i = 1; i < 4096; i++)
        if (hist[i] > hist[best]) best = i;

    int dr = ((best >> 8) & 0xF) * 17 + 8;
    int dg = ((best >> 4) & 0xF) * 17 + 8;
    int db = (best & 0xF) * 17 + 8;

    free(covers[slot].pixels);
    covers[slot].pixels = pixels;
    covers[slot].title_id = title_id;
    covers[slot].color = RGBA8_MAXALPHA(cr, cg, cb);
    covers[slot].dominant = RGBA8_MAXALPHA(dr, dg, db);

    last_color = covers[slot].color;

    return pixels;
}
