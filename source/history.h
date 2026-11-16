#pragma once

#include <switch.h>
#include <stdbool.h>

void history_load(void);
void history_save(void);

// Время получения достижения (unix time) или 0, если неизвестно.
u64 history_get(const char *appid, const char *achievement_id);
void history_mark(const char *appid, const char *achievement_id, u64 when);
