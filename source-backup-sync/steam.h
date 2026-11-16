#pragma once

#include <jansson.h>
#include <stdbool.h>

typedef struct {
    char appid[32];
    char name[128];
    int playtime;
} SteamGame;

typedef struct {
    char id[128];
    char name[128];
    char description[512];
    char icon[256];
} SteamAchievement;

int steam_parse_games(const char* json, SteamGame* games, int max_games);
int steam_parse_achievements(const char* json, SteamAchievement* achievements, int max_achievements);
