#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <strings.h>
#include <jansson.h>

#include "steamsearch.h"
#include "net.h"

#define SEARCH_BUFFER (128 * 1024)
#define JSON_BUFFER   (512 * 1024)
#define ICON_BUFFER   (256 * 1024)

static void url_encode(const char *in, char *out, size_t size)
{
    static const char *hex = "0123456789ABCDEF";
    size_t o = 0;

    for (const unsigned char *p = (const unsigned char *)in; *p && o + 4 < size; p++) {
        if (isalnum(*p) || *p == '-' || *p == '_' || *p == '.' || *p == '~') {
            out[o++] = (char)*p;
        } else if (*p == ' ') {
            out[o++] = '%';
            out[o++] = '2';
            out[o++] = '0';
        } else {
            out[o++] = '%';
            out[o++] = hex[*p >> 4];
            out[o++] = hex[*p & 0xF];
        }
    }

    out[o] = '\0';
}

static bool looks_like_junk(const char *name)
{
    static const char *skip[] = {
        "Soundtrack", "Digital Comic", "Artbook", "Season Pass",
        "Bundle", "DLC", "Expansion",
    };

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

int steam_search(const char *term, SteamSearchResult *out, int max_results)
{
    if (!term || !term[0] || !out || max_results <= 0)
        return 0;

    char *response = malloc(SEARCH_BUFFER);
    if (!response) return 0;

    char encoded[512];
    url_encode(term, encoded, sizeof(encoded));

    char path[768];
    snprintf(path, sizeof(path),
             "/api/storesearch/?term=%s&l=english&cc=US", encoded);

    if (!net_https_get("store.steampowered.com", path, response, SEARCH_BUFFER)) {
        free(response);
        return 0;
    }

    json_error_t error;
    json_t *root = json_loads(response, 0, &error);
    free(response);

    if (!root) return 0;

    json_t *items = json_object_get(root, "items");
    int count = 0;

    if (json_is_array(items)) {
        size_t index;
        json_t *item;

        json_array_foreach(items, index, item) {
            if (count >= max_results) break;

            const char *type = json_string_value(json_object_get(item, "type"));
            const char *name = json_string_value(json_object_get(item, "name"));
            json_t *id = json_object_get(item, "id");

            if (!name || !json_is_integer(id)) continue;
            if (type && strcmp(type, "app") != 0) continue;
            if (looks_like_junk(name)) continue;

            out[count].appid = (int)json_integer_value(id);
            snprintf(out[count].name, sizeof(out[count].name), "%s", name);
            count++;
        }
    }

    json_decref(root);
    return count;
}

int steam_fetch_achievements(int appid, char *buffer, size_t size)
{
    return steam_fetch_achievements_lang(appid, "english", buffer, size);
}

int steam_fetch_achievements_lang(int appid, const char *language,
                                  char *buffer, size_t size)
{
    char path[192];
    snprintf(path, sizeof(path),
             "/IPlayerService/GetGameAchievements/v1/?appid=%d&language=%s",
             appid, language ? language : "english");

    if (!net_https_get("api.steampowered.com", path, buffer, size))
        return -1;

    size_t len = strlen(buffer);

    return len > 32 ? (int)len : -1;
}

int steam_fetch_icon(int appid, const char *icon_file,
                     unsigned char *buffer, size_t size)
{
    if (!icon_file || !icon_file[0])
        return -1;

    char path[512];
    snprintf(path, sizeof(path),
             "/community_assets/images/apps/%d/%s", appid, icon_file);

    if (!net_https_get("shared.akamai.steamstatic.com", path,
                       (char *)buffer, size))
        return -1;

    size_t len = net_last_body_length();

    return len > 128 ? (int)len : -1;
}

void games_json_set_appid(u64 title_id, const char *name, const char *appid)
{
    const char *path = "sdmc:/switch/NX-Stach/games.json";

    json_error_t error;
    json_t *root = json_load_file(path, 0, &error);

    if (!root) {
        root = json_object();
        json_object_set_new(root, "games", json_array());
    }

    json_t *games = json_object_get(root, "games");

    if (!json_is_array(games)) {
        games = json_array();
        json_object_set_new(root, "games", games);
    }

    char id_text[32];
    snprintf(id_text, sizeof(id_text), "%016llX", (unsigned long long)title_id);

    bool updated = false;
    size_t index;
    json_t *item;

    json_array_foreach(games, index, item) {
        const char *sid = json_string_value(json_object_get(item, "switch_id"));

        if (!sid) continue;

        if (strcasecmp(sid, id_text) == 0) {
            json_object_set_new(item, "steam_app_id", json_string(appid));
            if (name && name[0])
                json_object_set_new(item, "name", json_string(name));
            updated = true;
            break;
        }
    }

    if (!updated) {
        json_t *item = json_object();
        json_object_set_new(item, "switch_id", json_string(id_text));
        json_object_set_new(item, "name", json_string(name ? name : ""));
        json_object_set_new(item, "steam_app_id", json_string(appid));
        json_array_append_new(games, item);
    }

    json_dump_file(root, path, JSON_INDENT(2));
    json_decref(root);
}
