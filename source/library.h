#pragma once

#include <switch.h>
#include <stdbool.h>
#include <stddef.h>

#define MAX_GAMES 64
#define LIB_COVER_W 270
#define LIB_COVER_H 190

typedef struct {
    u64 title_id;
    char name[128];
    char steam_appid[32];
} Game;

// Загружает список игр: сначала из консоли (ns), если не вышло — из games.json.
// Возвращает количество игр.
int library_load(Game *games, int max_games);

// Обложка игры в формате кадра (RGBA8_MAXALPHA), LIB_COVER_W x LIB_COVER_H.
// NULL, если обложку получить не удалось.
const u32 *library_cover(u64 title_id);

bool library_online(void);
void library_exit(void);
