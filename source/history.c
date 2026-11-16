#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>

#include "history.h"

#define HISTORY_PATH "sdmc:/switch/NX-Stach/history.json"

static json_t *root = NULL;

void history_load(void) {
    json_error_t error;

    root = json_load_file(HISTORY_PATH, 0, &error);

    if (!root || !json_is_object(root)) {
        if (root) json_decref(root);
        root = json_object();
        json_t *games = json_object();
        json_object_set_new(root, "games", games);
    }
}

void history_save(void) {
    if (!root)
        return;

    json_dump_file(root, HISTORY_PATH, JSON_INDENT(2));
}

static json_t *ensure_game(const char *appid) {
    if (!root || !appid) return NULL;

    json_t *games = json_object_get(root, "games");

    if (!json_is_object(games)) {
        games = json_object();
        json_object_set_new(root, "games", games);
    }

    json_t *game = json_object_get(games, appid);

    if (!json_is_object(game)) {
        game = json_object();
        json_object_set_new(games, appid, game);
    }

    return game;
}

u64 history_get(const char *appid, const char *achievement_id) {
    json_t *game = json_object_get(json_object_get(root, "games"), appid ? appid : "");

    if (!json_is_object(game) || !achievement_id)
        return 0;

    json_t *value = json_object_get(game, achievement_id);

    return json_is_integer(value) ? (u64)json_integer_value(value) : 0;
}

void history_mark(const char *appid, const char *achievement_id, u64 when) {
    if (!appid || !achievement_id || !when)
        return;

    json_t *game = ensure_game(appid);

    if (!game)
        return;

    json_object_set_new(game, achievement_id, json_integer((json_int_t)when));
}
