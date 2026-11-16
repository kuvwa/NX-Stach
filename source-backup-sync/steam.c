
#include "steam.h"
#include <stdio.h>
#include <string.h>

static void copy_string(char* dst, size_t size, const char* src) {
    if (!src) src = "";
    snprintf(dst, size, "%s", src);
}

int steam_parse_games(const char* text, SteamGame* games, int max_games) {
    if (!text || !games || max_games <= 0) return -1;

    json_error_t error;
    json_t* root = json_loads(text, 0, &error);
    if (!root) return -1;

    json_t* response = json_object_get(root, "response");
    json_t* array = response ? json_object_get(response, "games") : NULL;

    if (!json_is_array(array)) {
        json_decref(root);
        return -1;
    }

    int count = 0;
    size_t i;
    json_t* item;

    json_array_foreach(array, i, item) {
        if (count >= max_games) break;

        json_t* appid = json_object_get(item, "appid");
        json_t* name = json_object_get(item, "name");
        json_t* playtime = json_object_get(item, "playtime_forever");

        snprintf(games[count].appid, sizeof(games[count].appid),
                 "%lld", (long long)json_integer_value(appid));

        copy_string(games[count].name, sizeof(games[count].name),
                    json_string_value(name));

        games[count].playtime = (int)json_integer_value(playtime);
        count++;
    }

    json_decref(root);
    return count;
}

int steam_parse_achievements(const char* text,
                            SteamAchievement* achievements,
                            int max_achievements) {
    if (!text || !achievements || max_achievements <= 0) return -1;

    json_error_t error;
    json_t* root = json_loads(text, 0, &error);
    if (!root) return -1;

    json_t* array = json_object_get(root, "achievements");

    if (!json_is_array(array)) {
        json_decref(root);
        return -1;
    }

    int count = 0;
    size_t i;
    json_t* item;

    json_array_foreach(array, i, item) {
        if (count >= max_achievements) break;

        copy_string(achievements[count].id,
                    sizeof(achievements[count].id),
                    json_string_value(json_object_get(item, "id")));

        copy_string(achievements[count].name,
                    sizeof(achievements[count].name),
                    json_string_value(json_object_get(item, "name")));

        copy_string(achievements[count].description,
                    sizeof(achievements[count].description),
                    json_string_value(json_object_get(item, "description")));

        copy_string(achievements[count].icon,
                    sizeof(achievements[count].icon),
                    json_string_value(json_object_get(item, "icon")));

        count++;
    }

    json_decref(root);
    return count;
}
