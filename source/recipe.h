#pragma once

#include <switch.h>
#include <stdbool.h>

// «Рецепт» — как читать прогресс достижений из сейва игры.
typedef struct {
    u64 title_id;
    char steam_appid[16];
    char file_path[128];
    char marker[64];
    int offset;
    int skip;
    int format;   // 0 = ASCII '0'/'1', 1 = байты 0/1
    int count;    // сколько достижений ожидается (0 = не важно)
    bool valid;
    bool from_sd;
} Recipe;

// Ищет рецепт: сначала SD, потом встроенный romfs.
bool recipe_load(u64 title_id, const char *appid, Recipe *out);
bool recipe_save(const Recipe *r);
void recipe_delete(u64 title_id, const char *appid);

// Читает флаги по рецепту. names — внутренние имена достижений
// (нужны для формата 2 «по именам»). Возвращает число флагов или -1.
int recipe_read_flags(const Recipe *r, const char **names, int name_count,
                      u8 *flags, int max_flags);
