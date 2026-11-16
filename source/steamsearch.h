#pragma once

#include <switch.h>
#include <stdbool.h>
#include <stddef.h>

#define STEAM_MAX_RESULTS 24

typedef struct {
    int appid;
    char name[160];
} SteamSearchResult;

// Поиск игр в магазине Steam. Возвращает количество найденных.
int steam_search(const char *term, SteamSearchResult *out, int max_results);

// Скачивает JSON с достижениями. Возвращает длину или -1.
int steam_fetch_achievements(int appid, char *buffer, size_t size);
int steam_fetch_achievements_lang(int appid, const char *language,
                                  char *buffer, size_t size);

// Скачивает иконку достижения (jpeg). Возвращает длину или -1.
int steam_fetch_icon(int appid, const char *icon_file,
                     unsigned char *buffer, size_t size);

// Кладёт steam_app_id в games.json (создаёт запись, если её нет).
void games_json_set_appid(u64 title_id, const char *name, const char *appid);
