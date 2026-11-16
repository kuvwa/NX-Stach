#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>
#include <sys/stat.h>

#include "recipe.h"
#include "gamesave.h"

#define RECIPE_DIR "sdmc:/switch/NX-Stach/recipes"

static void path_for(u64 title_id, const char *appid, const char *prefix,
                     char *out, size_t size)
{
    snprintf(out, size, "%s/recipes/%016llX_%s.json", prefix,
             (unsigned long long)title_id, (appid && appid[0]) ? appid : "0");
}

static bool load_file(const char *path, Recipe *out, u64 title_id)
{
    json_error_t error;
    json_t *root = json_load_file(path, 0, &error);

    if (!root) return false;

    memset(out, 0, sizeof(*out));
    out->title_id = title_id;

    const char *appid = json_string_value(json_object_get(root, "steam_appid"));
    const char *file = json_string_value(json_object_get(root, "file_path"));
    const char *marker = json_string_value(json_object_get(root, "marker"));

    snprintf(out->steam_appid, sizeof(out->steam_appid), "%s", appid ? appid : "");
    snprintf(out->file_path, sizeof(out->file_path), "%s", file ? file : "");
    snprintf(out->marker, sizeof(out->marker), "%s", marker ? marker : "");

    out->offset = (int)json_integer_value(json_object_get(root, "offset"));
    out->skip = (int)json_integer_value(json_object_get(root, "skip"));
    out->format = (int)json_integer_value(json_object_get(root, "format"));
    out->count = (int)json_integer_value(json_object_get(root, "count"));

    json_decref(root);

    out->valid = out->file_path[0] != '\0';
    return out->valid;
}

bool recipe_load(u64 title_id, const char *appid, Recipe *out)
{
    char path[220];

    out->valid = false;
    out->from_sd = false;

    path_for(title_id, appid, "sdmc:/switch/NX-Stach", path, sizeof(path));

    if (load_file(path, out, title_id)) {
        out->from_sd = true;
        return true;
    }

    // встроенные рецепты: romfs:/recipes/<id>_<appid>.json
    snprintf(path, sizeof(path), "romfs:/recipes/%016llX_%s.json",
             (unsigned long long)title_id, (appid && appid[0]) ? appid : "0");

    return load_file(path, out, title_id);
}

bool recipe_save(const Recipe *r)
{
    if (!r || !r->valid)
        return false;

    mkdir("sdmc:/switch/NX-Stach", 0777);
    mkdir(RECIPE_DIR, 0777);

    json_t *root = json_object();

    json_object_set_new(root, "steam_appid", json_string(r->steam_appid));
    json_object_set_new(root, "file_path", json_string(r->file_path));
    json_object_set_new(root, "marker", json_string(r->marker));
    json_object_set_new(root, "offset", json_integer(r->offset));
    json_object_set_new(root, "skip", json_integer(r->skip));
    json_object_set_new(root, "format", json_integer(r->format));
    json_object_set_new(root, "count", json_integer(r->count));

    char path[220];
    path_for(r->title_id, r->steam_appid, "sdmc:/switch/NX-Stach", path,
             sizeof(path));

    int ok = json_dump_file(root, path, JSON_INDENT(2));

    json_decref(root);
    return ok == 0;
}

void recipe_delete(u64 title_id, const char *appid)
{
    char path[220];
    path_for(title_id, appid, "sdmc:/switch/NX-Stach", path, sizeof(path));
    remove(path);
}

int recipe_read_flags(const Recipe *r, u8 *flags, int max_flags)
{
    if (!r || !r->valid)
        return -1;

    return gamesave_read_block(r->title_id, r->file_path, r->marker,
                               r->offset, r->skip, r->format,
                               flags, max_flags);
}
