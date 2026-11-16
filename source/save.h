#pragma once
#include <stdbool.h>

bool save_init(void);
bool save_is_unlocked(const char *appid, const char *achievement_id);
bool save_unlock(const char *appid, const char *achievement_id);
bool save_lock(const char *appid, const char *achievement_id);
const char *save_status(void);
void save_exit(void);
